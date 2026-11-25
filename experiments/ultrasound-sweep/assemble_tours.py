"""Assemble the inspected ultrasound sweeps and their acquired references for a local gallery."""
import argparse
import json
from itertools import product
import math
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

import numpy as np
import build_abdomen
import build_aortic_screening
import build_axilla
import build_breast
import build_carotid
import build_early_pregnancy
import build_gestational
import build_pregnancy
import build_thyroid
from breast_anatomy import FEMALE_SKIN_SHA, MAMMARY_SHA
from breast_compression import SETTLE_DEPTH_MM
from case_library import write_case_library
from delivery import detail_files, read_poses, sha256, sweep_files, validate_image, validate_mesh, verify_inventory
from geometry import FRAME_COUNT, KEYFRAMES, RASTER_SIZE, SECTOR_DEPTH_MM, SECTOR_HALF_ANGLE_DEG, LENS_RADIUS_MM, VOXEL_MM
from prepare_scenes import read_vendor, shared_geometry
from survey_delivery import STUDY, survey_files

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


def reference_sources(regional_sources):
    refs = dict(GALLBLADDER_REFERENCES)
    files = {}
    landmarks = set()
    sources = ['hepatopancreatic.json', 'renal-splenic.json', 'great-vessels.json', 'normal-landmarks.json']
    sources.extend(regional_sources)
    for source in sources:
        group = json.loads((RESEARCH / source).read_text())
        if source == 'normal-landmarks.json':
            landmarks.update(group)
        for key, ref in group.items():
            if ref.get('role') in ('related', 'comparison-and-related'):
                landmarks.add(key)
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


def verify_contact_fields(root, track):
    """Every frame must seat the same lens and preserve tissue depth order."""
    frames = read_poses(root / 'sweep.js')
    geometry = None
    for index, frame in enumerate(frames):
        if track['id'] == 'axilla' and frame.get('imagingDepthMm') != build_axilla.imaging_depth(index, track['sectorDepthMm']):
            raise ValueError(f'Invalid axillary imaging depth at frame {index}')
        try:
            rig = frame['contactRig']
            width, height = rig['faceWidthMm'], rig['faceElevationMm']
            settle, feather = rig['settleDepthMm'], rig['featherMm']
            x, y = rig['lateralMm'], rig['elevationMm']
            shape = (x, y, width, height, settle, feather)
            field = np.asarray(rig['surfaceMm'], dtype=float)
            valid = (width == track['fieldWidthMm'] and min(height, settle, feather) > 0
                     and all(math.isfinite(v) for v in (height, settle, feather))
                     and all(len(axis) >= 3 and len(axis) % 2 and
                             np.allclose(axis, np.linspace(-span/2, span/2, len(axis)), atol=1e-5)
                             for axis, span in ((x, width), (y, height)))
                     and field.shape == (len(y), len(x)) and np.isfinite(field).all()
                     and field.max() <= .5
                     and (track.get('compressionMm', 0) - field.min()) * 1.5 < settle
                     and (geometry is None or geometry == shape))
        except (TypeError, ValueError, KeyError):
            valid = False
        if not valid:
            raise ValueError(f'Invalid seated contact field at frame {index} in {root.name}')
        geometry = shape


def verify_ap_spans(root, receipt):
    """Calipers and readout must describe the same physical chord in the saved raster."""
    pitch = np.asarray(receipt.get('rasterPitchMm'), dtype=float)
    if pitch.shape not in ((), (2,)) or not np.isfinite(pitch).all() or (pitch <= 0).any():
        raise ValueError(f'Invalid aortic raster calibration: {root.name}')
    for i, frame in enumerate(read_poses(root / 'sweep.js')):
        span = frame.get('apSpan')
        if not isinstance(span, dict):
            raise ValueError(f'Missing modeled AP span at frame {i}')
        ends = np.asarray(span.get('endpointsPx'), dtype=float)
        mm = span.get('millimetres')
        if (ends.shape != (2, 2) or not np.isfinite(ends).all()
                or (ends < 0).any() or (ends >= RASTER_SIZE).any()
                or not isinstance(mm, (float, int)) or not math.isfinite(mm) or mm <= 0
                or abs(np.linalg.norm((ends[1] - ends[0]) * pitch) - mm) > .05):
            raise ValueError(f'Invalid modeled AP span at frame {i}')


def verify_track(root, track, stops, builder):
    slug = track['id']
    case = track.get('case', 's1233')
    linear = track.get('probeType') == 'linear'
    receipt = json.loads((root / 'verification.json').read_text())
    recipe = Path(builder.__file__).name
    if builder is build_aortic_screening:
        if (not (root / 'delivery.json').is_file()
                or receipt.get('modelRecipeSha256') != builder.model_recipe_sha256()
                or receipt.get('ctSha256') != builder.CT_SHA or receipt.get('maskSha256') != builder.PINS):
            raise ValueError(f'Rebuild {slug} for the current aortic survey anatomy and sampler.')
        verify_ap_spans(root, receipt)
    if builder in (build_breast, build_axilla) and receipt.get('renderRecipeSha256') != builder.render_recipe_sha256(slug):
        raise ValueError(f'Rebuild {slug} with the current tissue rendering recipe.')
    if builder is build_carotid and (
            receipt.get('modelRecipeSha256') != builder.model_recipe_sha256()
            or receipt.get('ctSha256') != builder.CT_SHA or receipt.get('maskSha256') != builder.PINS
            or receipt.get('obstructionMaskSha256') != builder.OBSTRUCTION_PINS):
        raise ValueError(f'Rebuild {slug} for the current carotid anatomy and sampler.')
    if builder in (build_breast, build_axilla, build_carotid):
        verify_contact_fields(root, track)
    if 'steering' in track:
        steering = track['steering']
        axes = steering['axes']
        cells = steering['cells']
        values = [axis['values'] for axis in axes]
        if (len(values) != 3 or any(len(v) < 2 or not all(map(math.isfinite, v))
                                      or list(v) != sorted(set(v)) for v in values)
                or {tuple(cell['indices']) for cell in cells} != set(product(*(range(len(v)) for v in values)))
                or len(cells) != math.prod(map(len, values))
                or len({cell['frame'] for cell in cells}) != len(cells)
                or any(cell['frame'] not in range(FRAME_COUNT) for cell in cells)
                or json.dumps(steering, sort_keys=True) != json.dumps(receipt.get('steering'), sort_keys=True)
                or receipt.get('compressionMm') != track.get('compressionMm')
                or receipt.get('compressionSettleDepthMm') != SETTLE_DEPTH_MM):
            raise ValueError(f'Rebuild {slug} for the configured steering and compression.')
    if builder is build_breast and (receipt.get('mammaryAtlasSha256') != MAMMARY_SHA
                                    or receipt.get('femaleSkinSha256') != FEMALE_SKIN_SHA):
        raise ValueError(f'Rebuild {slug} for the current breast atlas inputs.')
    if builder is build_axilla and receipt.get('femaleSkinSha256') != FEMALE_SKIN_SHA:
        raise ValueError(f'Rebuild {slug} for the current axillary exterior.')
    if builder in (build_pregnancy, build_early_pregnancy, build_gestational):
        if not (root / 'delivery.json').is_file():
            raise ValueError(f'Missing pregnancy sweep delivery inventory: {slug}')
        if builder is build_pregnancy:
            model_matches = receipt.get('pregnancyRecipeSha256') == builder.pregnancy_recipe_sha256()
        else:
            model_matches = receipt.get('modelRecipeSha256') == builder.model_recipe_sha256()
        if not model_matches:
            raise ValueError(f'Rebuild {slug} for the current pregnancy anatomy and sampler.')
    expected_pose = builder.pose_recipe_sha256(slug)
    if (track.get('requirePoseReceipt', False) or 'poseRecipeSha256' in receipt) and (
            receipt.get('poseRecipeSha256') != expected_pose):
        raise ValueError(f'Rebuild {slug} with {recipe} for the current pose recipe.')
    expected_palette = build_abdomen.section_palette_sha256(track)
    if (track.get('requirePaletteReceipt', False) or 'sectionPaletteSha256' in receipt) and (
            receipt.get('sectionPaletteSha256') != expected_palette):
        raise ValueError(f'Rebuild {slug} with {recipe} for the current section palette.')
    if linear:
        if not (root / 'delivery.json').is_file():
            raise ValueError(f'Missing linear sweep delivery inventory: {slug}')
        if (receipt.get('fieldWidthMm') != track['fieldWidthMm'] or receipt.get('probeType') != 'linear'
                or receipt.get('fieldShape') != 'rectangle'):
            raise ValueError(f'Rebuild {slug} for the configured linear field.')
    elif receipt['lensRadiusMm'] != LENS_RADIUS_MM or receipt['sectorHalfAngleDeg'] != SECTOR_HALF_ANGLE_DEG:
        raise ValueError(f'Rebuild {slug} for the configured curved field.')
    if (receipt['exterior'] != track['exterior'] or receipt['sectorDepthMm'] != track['sectorDepthMm']
            or receipt['case'] != case or receipt['voxelMm'] != track.get('voxelMm', VOXEL_MM)
            or set(receipt['frames']) != {str(stop['frame']) for stop in stops}):
        raise ValueError(f'Rebuild {slug} for the configured exterior, depth, case and keyframes.')


def configure_timeline(tour):
    slug = tour['id']
    if 'stops' in tour:
        stops = tour.pop('stops')
    else:
        ref_ids = tour.pop('keyframeReferenceIds', [f'{slug}-{frame}' for frame in KEYFRAMES])
        stops = [dict(frame=frame, label=label, referenceId=ref_id)
                 for frame, label, ref_id in zip(KEYFRAMES, tour.pop('keyframeLabels'), ref_ids, strict=True)]
        if entry := tour.pop('entryReference', None):
            if entry['frame'] != 0:
                raise ValueError(f'Entry comparison must start at frame zero: {slug}')
            stops.insert(0, entry)
            tour['initialFrame'] = KEYFRAMES[0]
    frames = [stop['frame'] for stop in stops]
    if (not frames or any(type(frame) is not int or frame not in range(FRAME_COUNT) for frame in frames)
            or frames != sorted(set(frames)) or tour.get('initialFrame', frames[0]) not in frames):
        raise ValueError(f'Invalid comparison frames: {slug}')
    tour['keyframes'] = stops
    if 'phases' not in tour:
        split = next(frame for frame in frames if frame > 0)
        tour['phases'] = [dict(frame=frame, label=label) for frame, label in
                          zip((0, split), tour.pop('phaseLabels'), strict=True)]
    phase_frames = [phase['frame'] for phase in tour['phases']]
    if (not phase_frames or phase_frames[0] != 0 or phase_frames != sorted(set(phase_frames))
            or any(type(frame) is not int or frame not in range(FRAME_COUNT - 1) for frame in phase_frames)):
        raise ValueError(f'Invalid sweep phases: {slug}')


def configured_tours(output, refs, files, landmark_refs, tracks):
    tours, identities, used_references = [], {}, set()
    pregnancy_stages = json.loads((HERE / 'pregnancy-stages.json').read_text())
    for track, builder in tracks:
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
        case = tour.get('case', 's1233')
        if builder in (build_thyroid, build_carotid):
            tour['anatomySource'] = {
                'label': f'TotalSegmentator {case} anatomy', 'url': 'https://zenodo.org/records/10047263',
                'license': 'CC BY 4.0', 'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
            }
        tour.setdefault('sourceNote', (
            f'Illustrative BodyParts3D exterior fitted to the {case} probe-contact window.'
            if tour.get('exterior') == 'fitted-atlas' else
            f'External body surface and internal structures sampled from the same {case} CT.'
        ))
        configure_timeline(tour)
        stops = tour['keyframes']
        if tour.get('bodyRegion') == 'Pregnancy':
            tour['pregnancyStage'] = pregnancy_stages[tour['pregnancyStage']]
        for stop in stops:
            ref_id = stop['referenceId']
            if ref_id not in refs or (ref_id in landmark_refs and refs[ref_id].get('role') != 'comparison-and-related'):
                raise ValueError(f'Missing acquired comparison: {ref_id}')
            used_references.add(ref_id)
        landmarks = tour.setdefault('landmarks', [])
        if not isinstance(landmarks, list) or len(set(landmarks)) != len(landmarks) or set(landmarks) - landmark_refs:
            raise ValueError(f'Invalid supporting landmark reference: {slug}')
        used_references.update(landmarks)

        if detail_frames := tour.pop('detailFrames', []):
            receipt = json.loads((output / root / 'verification.json').read_text())
            linear = tour.get('fieldShape') == 'rectangle'
            regions = receipt.get('detailBoundsMm' if linear else 'detailRois', {})
            if set(map(str, detail_frames)) != set(regions) or set(detail_frames) - {stop['frame'] for stop in stops}:
                raise ValueError(f'Unexpected magnified keyframes: {slug}')
            for stop in stops:
                if stop['frame'] in detail_frames:
                    region = regions[str(stop['frame'])]
                    if linear:
                        bounds = np.asarray(region, dtype=float)
                        half = tour['fieldWidthMm'] / 2
                        if bounds.shape != (4,) or not np.isfinite(bounds).all():
                            raise ValueError(f'Invalid linear detail bounds: {slug}')
                        x0, y0, x1, y1 = bounds
                        if not (-half <= x0 < x1 <= half and 0 <= y0 < y1 <= tour['sectorDepthMm']):
                            raise ValueError(f'Invalid linear detail bounds: {slug}')
                        stop['detail'] = {'boundsMm': region}
                    else:
                        stop['detail'] = {'roi': region}
        for stop in stops:
            if 'roi' in stop.get('detail', {}):
                grid = build_abdomen.ImagingGrid(tour['sectorDepthMm'], stop['detail']['roi'])
                half_pixel = (grid.x[0, 1] - grid.x[0, 0]) / 2
                stop['detail']['boundsMm'] = [round(float(bound), 4) for bound in
                    (grid.x[0, 0] - half_pixel, grid.y[0, 0] - half_pixel,
                     grid.x[0, -1] + half_pixel, grid.y[-1, 0] + half_pixel)]
        inventory = sweep_files(mesh_names) + detail_files(stops)
        if tour.get('compressionMm'):
            tour['compressionSettleDepthMm'] = SETTLE_DEPTH_MM
            inventory.extend(f'media/press-{kind}-{frame:02}.webp'
                             for kind in ('scan', 'section') for frame in range(FRAME_COUNT))
        if slug == 'gallbladder':
            inventory += [ref['path'] for ref in GALLBLADDER_REFERENCES.values()]
        else:
            verify_track(output / root, track, stops, builder)
            tour.pop('requirePoseReceipt', None)
            tour.pop('requirePaletteReceipt', None)
            if tour.get('pregnancyStage'):
                for key in ('windows', 'landmarkMinimums', 'requireModelReceipt'):
                    tour.pop(key, None)
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


def write_catalogue(destination, refs, tours, survey=None):
    if survey is not None:
        study = destination / STUDY
        study.mkdir(exist_ok=True)
        protocol, skin = survey
        (study / protocol['displaySkinPath']).write_bytes(skin)
        (study / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    for name, variable, content in [('references.js', 'abdomenReferences', refs), ('abdomen-tours.js', 'abdomenTours', tours)]:
        (destination / name).write_text(f'const {variable} = ' + json.dumps(content, ensure_ascii=False, indent=2) + ';\n')
    for name in ('index.html', 'study.css', 'study.js', 'study-picker.js', 'scene.js', 'probe-steering.js'):
        shutil.copyfile(HERE / name, destination / name)
    copy_cardiac_study(HERE / 'cardiac', destination)
    write_case_library(destination, tours, refs)


def copy_cardiac_study(source, destination):
    reference = json.loads((source / 'acquisition.json').read_text())
    if sha256((source / reference['file']).read_bytes()) != reference['sha256']:
        raise ValueError('Unexpected acquired cardiac cine identity')
    records = json.loads((source / 'reference/sources.json').read_text())
    geometry = json.loads((source / 'torso/geometry.json').read_text())
    runtime = ['index.html', 'echo.css', 'echo.js', 'reading.js', 'references.js', 'acquisition.json',
               'CC-BY-SA-3.0.txt', reference['file'], 'reference/sources.json', 'reference/CC-BY-NC-ND-4.0.txt',
               'torso/registration.js', 'torso/torso-view.js', 'measure/measure.css']
    runtime.extend(f'heart-{module}.js' for module in (
        'echo', 'geometry', 'poses', 'scene', 'slice', 'vessels', 'view'))
    runtime.extend(f'measure/{module}.js' for module in (
        'calculations', 'color-section', 'protocol', 'sections', 'signal-view', 'strain', 'workbench'))
    for key in ('skin', 'bones', 'cartilage'):
        name = f'torso/{key}.raw'
        if sha256((source / name).read_bytes()) != geometry[key]['sha256']:
            raise ValueError(f'Unexpected cardiac torso geometry: {key}')
        runtime.append(name)
    for view, cine in records['cine'].items():
        if not re.fullmatch(r'[a-z0-9-]+\.(?:webp|webm)', cine['file']):
            raise ValueError(f'Invalid cardiac reference path: {view}')
        name = 'reference/' + cine['file']
        if sha256((source / name).read_bytes()) != cine['sha256']:
            raise ValueError(f'Unexpected acquired cardiac cine identity: {view}')
        runtime.append(name)
    archive = source / 'reference/bse-table1.zip'
    if sha256(archive.read_bytes()) != records['bse']['sha256']:
        raise ValueError('Unexpected published echo panel archive')
    numbers = sorted(panel['number'] for items in records['panels'].values() for panel in items)
    if numbers != list(range(1, 89)):
        raise ValueError('Incomplete published echo panel inventory')
    target = destination / 'cardiac'
    for name in runtime:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, dest)
    images = target / 'reference/bse'
    images.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for number in numbers:
            name = f'ERP-20-0026inf{number}.jpg'
            (images / name).write_bytes(z.read(name))


def assemble(output, delivery=None):
    if delivery is not None and delivery.exists():
        raise ValueError(f'Choose a fresh delivery directory: {delivery}')
    tracks = [(track, build_abdomen) for track in [GALLBLADDER, *build_abdomen.read_tracks()]]
    regional_sources = []
    for region, builder, group in [('thyroid', build_thyroid, build_thyroid.read_thyroid_tracks()),
                                   ('carotid', build_carotid, build_carotid.read_tracks()),
                                   ('breast', build_breast, build_breast.read_breast_tracks()),
                                   ('axilla', build_axilla, build_axilla.read_axilla_tracks()),
                                   ('early-pregnancy', build_early_pregnancy, build_early_pregnancy.read_tracks()),
                                   ('pregnancy', build_pregnancy, build_pregnancy.read_pregnancy_tracks()),
                                   ('gestational', build_gestational, build_gestational.read_tracks()),
                                   ('aortic-screening', build_aortic_screening, build_aortic_screening.read_tracks())]:
        if any((output / 'sweeps' / track['id']).exists() for track in group):
            missing = [track['id'] for track in group if not (output / 'sweeps' / track['id']).is_dir()]
            if missing:
                raise ValueError(f'Incomplete {region} study. Build missing sweeps: {", ".join(missing)}')
            tracks.extend((track, builder) for track in group)
            regional_sources.append(region + '.json')
    refs, files, landmarks = reference_sources(regional_sources)
    for path, expected in shared_geometry().items():
        if (output / path).read_bytes() != expected:
            raise ValueError(f'Stale shared probe geometry: {path}')
        files[path] = output / path
    for path in read_vendor(output / 'vendor'):
        files[path] = output / path
    tours = configured_tours(output, refs, files, landmarks, tracks)
    survey = survey_files(output, refs, files)
    if survey is not None:
        for tour in tours:
            if tour['id'] in ('carotid-right', 'carotid-left'):
                tour['combinedExam'] = {'title': 'Bilateral carotid exam', 'path': STUDY + '/'}
    if delivery is None:
        for path, source in files.items():
            if path.startswith(('references/', STUDY + '/')):
                dest = output / path
                if dest != source:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, dest)
        write_catalogue(output, refs, tours, survey)
    else:
        delivery.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=delivery.parent) as stage_dir:
            stage = Path(stage_dir) / 'study'
            for path, source in files.items():
                dest = stage / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
            write_catalogue(stage, refs, tours, survey)
            stage.rename(delivery)
    print(f'Assembled {len(tours)} sweeps with {len(refs)} reference bindings.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Staging tree with generated sweeps and prepared gallbladder scene')
    parser.add_argument('--delivery', type=Path, help='Write a fresh serving tree without duplicate mesh files')
    args = parser.parse_args()
    assemble(args.output, args.delivery)
