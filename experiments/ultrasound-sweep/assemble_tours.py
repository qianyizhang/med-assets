"""Assemble the inspected ultrasound sweeps and their acquired references for a local gallery."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile

from build_abdomen import pose_recipe_sha256, read_tracks, section_palette_sha256
import build_thyroid
from delivery import sha256, sweep_files, validate_image, validate_mesh, verify_inventory
from geometry import KEYFRAMES, SECTOR_DEPTH_MM, SECTOR_HALF_ANGLE_DEG, LENS_RADIUS_MM, VOXEL_MM
from prepare_scenes import read_vendor, shared_geometry

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / 'research'
GALLBLADDER = {
    'id': 'gallbladder', 'title': 'Gallbladder', 'organ': 'gallbladder',
    'region': 'Right upper abdomen', 'exterior': 'fitted-atlas',
    'sectorDepthMm': SECTOR_DEPTH_MM, 'keyframeLabels': ['Long axis', 'Short axis'],
    'phaseLabels': ['Find window', 'Rotate probe'],
    'parts': [
        {'id': 'gallbladder', 'label': 'Gallbladder', 'color': '#3fbf9e', 'opacity': 1},
        {'id': 'liver', 'label': 'Liver', 'color': '#ad6155', 'opacity': .58},
        {'id': 'ribs', 'label': 'Ribs', 'color': '#dacaad', 'opacity': .78},
    ],
    'overlayParts': ['gallbladder', 'liver', 'portal_vein_and_splenic_vein'],
    'landmarks': ['extrahepatic-duct'],
}
GALLBLADDER_REFERENCES = {
    'gallbladder-12': {
        'path': 'media/acquired-long.webp', 'title': 'Gallbladder in long axis',
        'credit': 'Claudia Lucius et al., Life (2025), figure 2', 'url': 'https://doi.org/10.3390/life15060941',
        'license': 'CC BY 4.0', 'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
        'note': 'Claudia Lucius’s own collection. Complete still resized and converted to WebP.',
    },
    'gallbladder-48': {
        'path': 'media/acquired-short.webp', 'title': 'Normal Gallbladder, Short Axis',
        'credit': 'Kathryn Pade, MD, Rady Children’s Hospital San Diego · The POCUS Atlas',
        'url': 'https://www.thepocusatlas.com/pedsbiliary', 'license': 'CC BY-NC 4.0',
        'licenseUrl': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'note': 'Adolescent case. Full cine frame at 1.2 seconds converted to WebP.',
    },
}


def reference_sources(include_thyroid):
    refs = dict(GALLBLADDER_REFERENCES)
    files = {}
    landmarks = set()
    sources = ['hepatopancreatic.json', 'renal-splenic.json', 'great-vessels.json', 'normal-landmarks.json']
    if include_thyroid:
        sources.append('thyroid.json')
    for source in sources:
        group = json.loads((RESEARCH / source).read_text())
        if source == 'normal-landmarks.json':
            landmarks.update(group)
        for key, ref in group.items():
            if key in refs:
                raise ValueError(f'Duplicate reference {key}')
            name = Path(ref['path']).name
            if ref['path'] != 'references/' + name or not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.webp', name):
                raise ValueError(f'Invalid reference path {key}')
            if ref['path'] in files:
                raise ValueError(f'Duplicate reference output: {ref["path"]}')
            path = RESEARCH / 'acquired' / name
            if sha256(path.read_bytes()) != ref['sha256']:
                raise ValueError(f'Unexpected acquired image identity: {name}')
            validate_image(path)
            files[ref['path']] = path
            refs[key] = ref
    return refs, files, landmarks


def verify_track(root, track, stops):
    slug = track['id']
    case = track.get('case', 's1233')
    linear = track.get('probeType') == 'linear'
    receipt = json.loads((root / 'verification.json').read_text())
    recipe = 'build_thyroid.py' if linear else 'build_abdomen.py'
    expected_pose = build_thyroid.pose_recipe_sha256(slug) if linear else pose_recipe_sha256(slug)
    if (track.get('requirePoseReceipt', False) or 'poseRecipeSha256' in receipt) and (
            receipt.get('poseRecipeSha256') != expected_pose):
        raise ValueError(f'Rebuild {slug} with {recipe} --track {slug} for the current pose recipe.')
    expected_palette = section_palette_sha256(track)
    if (track.get('requirePaletteReceipt', False) or 'sectionPaletteSha256' in receipt) and (
            receipt.get('sectionPaletteSha256') != expected_palette):
        raise ValueError(f'Rebuild {slug} with {recipe} --track {slug} for the current section palette.')
    if linear:
        if not (root / 'delivery.json').is_file():
            raise ValueError(f'Missing thyroid delivery inventory: {slug}')
        if (receipt.get('fieldWidthMm') != track['fieldWidthMm'] or receipt.get('probeType') != 'linear'
                or receipt.get('fieldShape') != 'rectangle'):
            raise ValueError(f'Rebuild {slug} for the configured linear field.')
    elif receipt['lensRadiusMm'] != LENS_RADIUS_MM or receipt['sectorHalfAngleDeg'] != SECTOR_HALF_ANGLE_DEG:
        raise ValueError(f'Rebuild {slug} for the configured curved field.')
    if (receipt['exterior'] != track['exterior'] or receipt['sectorDepthMm'] != track['sectorDepthMm']
            or receipt['case'] != case or receipt['voxelMm'] != VOXEL_MM
            or set(receipt['frames']) != {str(stop['frame']) for stop in stops}):
        raise ValueError(f'Rebuild {slug} for the configured exterior, depth, case and keyframes.')


def configured_tours(output, refs, files, landmark_refs, tracks):
    tours, identities, used_references = [], {}, set()
    for track in tracks:
        tour = track.copy()
        slug = tour['id']
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug) or any(item['id'] == slug for item in tours):
            raise ValueError(f'Invalid or repeated sweep ID: {slug}')
        root = './' if slug == 'gallbladder' else f'sweeps/{slug}/'
        parts = {part['id']: part for part in tour['parts']}
        mesh_names = ['torso', *parts]
        if (len(parts) != len(tour['parts']) or tour['organ'] not in parts or 'torso' in parts
                or any(not re.fullmatch(r'[a-z0-9][a-z0-9_]*', part) for part in parts)):
            raise ValueError(f'Invalid or repeated scene part: {slug}')
        if slug == 'gallbladder':
            parts['portal_vein_and_splenic_vein'] = {
                'id': 'portal_vein_and_splenic_vein', 'label': 'Portal and splenic veins', 'color': '#799ac4',
            }
        tour['overlayParts'] = [parts[key] for key in tour['overlayParts']]
        tour['assetRoot'] = root
        tour['title'] += ' sweep'
        linear = tour.get('probeType') == 'linear'
        case = tour.get('case', 's1233')
        if linear:
            tour['anatomySource'] = {
                'label': f'TotalSegmentator {case} anatomy', 'url': 'https://zenodo.org/records/10047263',
                'license': 'CC BY 4.0', 'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
            }
        tour.setdefault('sourceNote', (
            f'Illustrative BodyParts3D exterior fitted to the {case} probe-contact window.'
            if tour.get('exterior') == 'fitted-atlas' else
            f'External body surface and internal structures sampled from the same {case} CT.'
        ))
        stops = [dict(frame=frame, label=label, referenceId=f'{slug}-{frame}')
                 for frame, label in zip(KEYFRAMES, tour.pop('keyframeLabels'), strict=True)]
        if entry := tour.pop('entryReference', None):
            if entry['frame'] != 0:
                raise ValueError(f'Entry comparison must start at frame zero: {slug}')
            stops.insert(0, entry)
            tour['initialFrame'] = KEYFRAMES[0]
        tour['keyframes'] = stops
        for stop in stops:
            ref_id = stop['referenceId']
            if ref_id not in refs or ref_id in landmark_refs:
                raise ValueError(f'Missing acquired comparison: {ref_id}')
            used_references.add(ref_id)
        tour['phases'] = [dict(frame=frame, label=label) for frame, label in
                          zip((0, KEYFRAMES[0]), tour.pop('phaseLabels'), strict=True)]
        landmarks = tour.setdefault('landmarks', [])
        if not isinstance(landmarks, list) or len(set(landmarks)) != len(landmarks) or set(landmarks) - landmark_refs:
            raise ValueError(f'Invalid supporting landmark reference: {slug}')
        used_references.update(landmarks)

        inventory = sweep_files(mesh_names)
        if slug == 'gallbladder':
            inventory += [ref['path'] for ref in GALLBLADDER_REFERENCES.values()]
        else:
            verify_track(output / root, track, stops)
            tour.pop('requirePoseReceipt', None)
            tour.pop('requirePaletteReceipt', None)
        verify_inventory(output / root, inventory)
        for relative in inventory:
            path = root.removeprefix('./') + relative
            source = output / path
            if relative.startswith('scenes/'):
                raw = source.read_bytes()
                validate_mesh(raw, source)
                identity = sha256(raw)
                canonical = identities.setdefault(identity, path)
                if canonical != path:
                    tour.setdefault('meshPaths', {})[source.stem] = canonical
                    continue
            files[path] = source
        tours.append(tour)
    if refs.keys() != used_references:
        raise ValueError(f'Unassigned acquired references: {sorted(refs.keys() - used_references)}')
    return tours


def write_catalogue(destination, refs, tours):
    for name, variable, content in [('references.js', 'abdomenReferences', refs), ('abdomen-tours.js', 'abdomenTours', tours)]:
        (destination / name).write_text(f'const {variable} = ' + json.dumps(content, ensure_ascii=False, indent=2) + ';\n')
    for name in ('index.html', 'study.css', 'study.js', 'scene.js'):
        shutil.copyfile(HERE / name, destination / name)


def assemble(output, delivery=None):
    if delivery is not None and delivery.exists():
        raise ValueError(f'Choose a fresh delivery directory: {delivery}')
    tracks = [GALLBLADDER, *read_tracks()]
    thyroid_tracks = build_thyroid.read_thyroid_tracks()
    include_thyroid = any((output / 'sweeps' / track['id']).exists() for track in thyroid_tracks)
    if include_thyroid:
        missing = [t['id'] for t in thyroid_tracks if not (output / 'sweeps' / t['id']).is_dir()]
        if missing:
            raise ValueError(f'Incomplete thyroid study. Build missing sweeps: {", ".join(missing)}')
        tracks.extend(thyroid_tracks)
    refs, files, landmarks = reference_sources(include_thyroid)
    for path, expected in shared_geometry().items():
        if (output / path).read_bytes() != expected:
            raise ValueError(f'Stale shared probe geometry: {path}')
        files[path] = output / path
    for path in read_vendor(output / 'vendor'):
        files[path] = output / path
    tours = configured_tours(output, refs, files, landmarks, tracks)
    if delivery is None:
        for path, source in files.items():
            if path.startswith('references/'):
                dest = output / path
                dest.parent.mkdir(exist_ok=True)
                shutil.copyfile(source, dest)
        write_catalogue(output, refs, tours)
    else:
        delivery.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=delivery.parent) as stage_dir:
            stage = Path(stage_dir) / 'study'
            for path, source in files.items():
                dest = stage / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
            write_catalogue(stage, refs, tours)
            stage.rename(delivery)
    print(f'Assembled {len(tours)} sweeps with {len(refs)} reference bindings.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Staging tree with generated sweeps and prepared gallbladder scene')
    parser.add_argument('--delivery', type=Path, help='Write a fresh serving tree without duplicate mesh files')
    args = parser.parse_args()
    assemble(args.output, args.delivery)
