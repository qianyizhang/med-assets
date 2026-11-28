"""Build a same-case transverse aortic sweep and segmented AP chords from s1233."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from scipy import ndimage as nd

import build_abdomen as abdomen
from build_study import AFFINE, CT_SHA, body_surface, fine_scatter, material_at, unit, volume
from scene_assets import scene_assets
from delivery import sha256, sweep_files, write_manifest
from geometry import FRAME_COUNT, LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM

HERE = Path(__file__).resolve().parent
TRACK = HERE / 'aortic-screening-track.json'
STATIONS = ((0, 218), (12, 213), (30, 183), (48, 151))
AP = np.array([0., 1., 0.])
VERTEBRAE = ('vertebrae_T12', *(f'vertebrae_L{n}' for n in range(1, 6)))
PINS = {
    name: abdomen.PINS[name] for name in ('aorta', 'inferior_vena_cava')
} | {
    'iliac_artery_left': 'd4329e10f6e2339a1ea1acd40592bffbda1979ff63e16554ef3c0788a0284204',
    'iliac_artery_right': '621ae2643717bd282cabcd4f990d6cc8b3a23408cdac64b55d147d874a508f7c',
    'vertebrae_T12': 'c855d908660252decd48d27fe041b63f4807758532f45a1054388adf420443b8',
    'vertebrae_L1': '0b334fe58f400a9c47ddbe1584945afa00a22f8daa2e26ebfe794e79bb7878ae',
    'vertebrae_L2': '1949021187b4e0c656569ae1e50898834499898ea530f959ebbfb12be9e1ad29',
    'vertebrae_L3': '9da23a97c2e5e5c8bddff40337970916ec67421e617976bd9c58c474d853cbf4',
    'vertebrae_L4': 'c2f6c1106f8305477d06bc09efa6b9e36f2621eddb9b316f6b5f201175cbb8dd',
    'vertebrae_L5': 'c752e865e613844ae5860105868848d792f511083ff5aedfcfc8cbbd7641b249',
}


def read_tracks():
    return [json.loads(TRACK.read_text())]


def pose_recipe_sha256(slug):
    track, = read_tracks()
    if slug != track['id']:
        raise ValueError(f'Unknown aortic survey: {slug}')
    return sha256(json.dumps(STATIONS).encode())


def model_recipe_sha256():
    names = ('build_aortic_screening.py', 'build_abdomen.py', 'build_study.py', 'geometry.py',
             'display_body.py', 'exterior-atlas.json', 'fit_abdomen.py')
    pins = {name: sha256((HERE / name).read_bytes()) for name in names}
    return sha256(json.dumps(pins, sort_keys=True).encode())


def load_masks(case):
    masks = {name: volume(case / f'segmentations/{name}.nii.gz', pin, 'u1')
             for name, pin in PINS.items() if name not in VERTEBRAE}
    spine = np.zeros_like(masks['aorta'])
    for name in VERTEBRAE:
        spine |= volume(case / f'segmentations/{name}.nii.gz', PINS[name], 'u1')
    return masks | {'vertebrae': spine}


def centerline(mask):
    centers = []
    levels = np.arange(147, 235)
    for z in levels:
        layer, _ = nd.label(mask[:, :, z])
        sizes = np.bincount(layer.ravel())
        sizes[0] = 0
        if not sizes.max():
            raise ValueError(f'Missing aortic trunk at case voxel slice {z}')
        centers.append(np.column_stack(np.nonzero(layer == sizes.argmax())).mean(axis=0))
    xy = nd.gaussian_filter1d(np.asarray(centers), 4.8, axis=0, mode='nearest')
    return np.column_stack((xy, levels))


def frame_path(shell, ct, line):
    indices, z = zip(*STATIONS, strict=True)
    for number in range(FRAME_COUNT):
        height = np.interp(number, indices, z)
        xyz = [np.interp(height + offset, line[:, 2], values) for offset in (-5, 0, 5)
               for values in line.T]
        lower, target, upper = np.asarray(xyz).reshape(3, 3)
        tangent = unit(upper - lower)
        # Aim in the cross-sectional plane. Prioritize soft-tissue rays close
        # to the anterior approach and to the previous frame's lateral tilt.
        ap = unit(AP - tangent * (AP @ tangent))
        lateral = unit(np.cross(ap, tangent))
        candidates = []
        desired = np.interp(height, [151, 165, 185, 222], [-.10, -.07, -.16, -.22])
        previous = desired if number == 0 else tilt
        for tilt in np.linspace(-.32, .22, 19):
            out = unit(ap + tilt * lateral)
            width, _, beam = abdomen.axes(out, lateral).T
            contact = abdomen.contact_point(target, beam, shell)
            distance = np.linalg.norm(contact - target)
            rays = contact[:, None] + beam[:, None] * np.arange(4, distance - 4, .8)
            hu = material_at(ct, rays)
            air = np.count_nonzero(hu < -450)
            bone = np.count_nonzero(hu > 350)
            cost = air * .55 + bone * .65 + 45 * (tilt - previous)**2 + 6 * (tilt - desired)**2
            candidates.append((cost, tilt, width, beam, contact, distance, air, bone))
        _, tilt, width, beam, contact, distance, air, bone = min(candidates, key=lambda row: row[0])
        if number == 0:
            initial_beam, initial_width = beam, width
        relative_angle = np.arccos(np.clip((beam @ initial_beam + width @ initial_width
                                           + np.cross(beam, width) @ np.cross(initial_beam, initial_width) - 1) / 2,
                                          -1, 1))
        frame = {'contact': contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist(),
                 'degrees': round(float(np.rad2deg(relative_angle)), 2)}
        yield frame, target, tangent, ap, distance, air, bone


def main_ap_span(mask, target, tangent, ap):
    """Longest contiguous AP mask chord near the trunk center in the short-axis plane."""
    lateral = unit(np.cross(ap, tangent))
    offsets = np.arange(-5.0, 5.01, .25) / VOXEL_MM
    distance = np.linspace(-31, 31, 621) / VOXEL_MM
    origins = target[:, None] + lateral[:, None] * offsets
    xyz = origins[:, :, None] + ap[:, None, None] * distance
    sample = material_at(mask, xyz)
    middle = len(distance) // 2
    chords = []
    for origin, row in zip(origins.T, sample, strict=True):
        if row[middle] < .5:
            continue
        lo = np.flatnonzero(row[:middle] < .5)
        hi = np.flatnonzero(row[middle:] < .5) + middle
        if not len(lo) or not len(hi):
            continue
        a, b = lo[-1], hi[0]
        def crossing(i):
            return distance[i] + (distance[i+1] - distance[i]) * (.5 - row[i]) / (row[i+1] - row[i])
        start, end = crossing(a), crossing(b - 1)
        chords.append(((end - start) * VOXEL_MM, origin + ap * start, origin + ap * end))
    if not chords:
        raise ValueError('No contiguous AP mask chord through the aortic trunk')
    return max(chords, key=lambda chord: chord[0])


def annotation(grid, frame, chord):
    mm, a, b = chord
    local = (np.array([a, b]) - frame['contact']) * VOXEL_MM
    x_axis = grid.x[0]
    y_axis = grid.y[:, 0]
    pitch = x_axis[1] - x_axis[0]
    x = (local @ frame['width'] - x_axis[0]) / pitch
    y = (local @ frame['beam'] - y_axis[0]) / pitch
    endpoints = np.column_stack((x, y)).round(3)
    return {'millimetres': round(float(mm), 3), 'endpointsPx': endpoints.tolist()}


def ras_mm(points):
    return (np.asarray(points) @ AFFINE[:3, :3].T + AFFINE[:3, 3]).round(3).tolist()


def acoustic_interfaces(gray, frame, grid, masks):
    """Add illustrative reflection and shadow at native section boundaries."""
    samples = grid.coordinates(frame, grid.polar_x, grid.polar_y)
    gray = gray.astype('f')
    for name, reflecting, scatter in (('aorta', 112, 14), ('inferior_vena_cava', 62, 10)):
        vessel = material_at(masks[name], samples)
        polar_edge = np.abs(np.gradient(nd.gaussian_filter(vessel, (1.15, .65)), axis=0))
        specular = material_at(nd.gaussian_filter(polar_edge, (.65, .7)), grid.to_image)
        interior = material_at(vessel, grid.to_image)
        gray += reflecting * specular + scatter * interior
    xyz = grid.coordinates(frame, grid.x, grid.y)
    aorta = material_at(masks['aorta'], xyz)
    gray += (7 * aorta) * fine_scatter(xyz)

    bone = material_at(masks['vertebrae'], samples)
    exposure = .5 * np.cumsum(bone, axis=0)
    first_interface = np.maximum(np.gradient(nd.gaussian_filter(bone, (.75, .72)), axis=0), 0)
    front = first_interface * np.exp(-exposure / 4)
    echo = material_at(nd.gaussian_filter(front, (1.1, .65)), grid.to_image)
    shadow = material_at(nd.gaussian_filter(np.exp(-exposure / 6.4), (.62, 1.05)), grid.to_image)
    gray = gray * shadow + 490 * echo
    return np.where(grid.field, np.clip(gray, 1, 245), 0).astype('u1')


def build(case, output, track):
    ct = volume(case / 'ct.nii.gz', CT_SHA, '<i2')
    shell, vertices, faces = body_surface(ct)
    masks = load_masks(case)
    line = centerline(masks['aorta'])
    grid = abdomen.ImagingGrid(track['sectorDepthMm'])
    frames_and_targets = list(frame_path(shell, ct, line))
    frames = [row[0] for row in frames_and_targets]
    source = abdomen.exterior_inputs(case, [track])
    mesh, contact_receipt = abdomen.fit_exterior(track, frames, shell, (vertices, faces[:, ::-1]), source)
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    (scenes / 'torso.mesh').write_bytes(mesh)
    governed = scene_assets(track)
    for name, mask in masks.items():
        raw = governed.get(name)
        (scenes / f'{name}.mesh').write_bytes(abdomen.mesh_from_mask(mask, (117, 237)) if raw is None else raw)
    parts = abdomen.section_palette(track)
    evidence = {}
    stop_frames = {stop['frame'] for stop in track['stops']}
    rays = []
    for index, (frame, target, tangent, ap, distance, air, bone) in enumerate(frames_and_targets):
        gray, labels = grid.sample(frame, ct, masks)
        gray = acoustic_interfaces(gray, frame, grid, masks)
        profile = abdomen.measure_landmark(labels['aorta'], gray)
        chord = main_ap_span(masks['aorta'], target, tangent, ap)
        frame['apSpan'] = annotation(grid, frame, chord)
        rays.append((air, bone))
        if profile['largestSectionPixels'] < 350 or chord[0] < 10 or distance * VOXEL_MM > track['sectorDepthMm'] - 15 or air > 4 or bone > 3:
            raise ValueError(f'Aorta poorly depicted at frame {index}: {profile}')
        if index in stop_frames:
            detail = {name: abdomen.measure_landmark(region, gray) for name, region in labels.items()}
            evidence[str(index)] = {**detail, 'anchorRasMm': ras_mm(target), 'contactRasMm': ras_mm(frame['contact']),
                                    'apSpanEndpointsRasMm': ras_mm(chord[1:]), 'apSpan': frame['apSpan'],
                                    'targetDepthMm': round(float(distance * VOXEL_MM), 2),
                                    'centerlineDirection': tangent.round(6).tolist(),
                                    'centerRayAirSamples': int(air), 'centerRayBoneSamples': int(bone)}
        Image.fromarray(gray).save(media / f'scan-{index:02}.webp', quality=90)
        Image.fromarray(abdomen.overlay(gray, labels, parts)).save(media / f'section-{index:02}.webp', quality=88)
    iliac_start = {name: int(np.nonzero(masks[name].any(axis=(0, 1)))[0][-1])
                   for name in ('iliac_artery_left', 'iliac_artery_right')}
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        'case': 's1233', 'coordinateFrame': 'native CT voxel grid with RAS affine',
        'ctSha256': CT_SHA, 'maskSha256': PINS, **contact_receipt,
        'voxelMm': VOXEL_MM, 'sectorDepthMm': track['sectorDepthMm'],
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG, 'lensRadiusMm': LENS_RADIUS_MM,
        'poseRecipeSha256': pose_recipe_sha256(track['id']),
        'modelRecipeSha256': model_recipe_sha256(),
        'sectionPaletteSha256': abdomen.section_palette_sha256(track),
        'rasterPitchMm': float(grid.x[0, 1] - grid.x[0, 0]),
        'apSpanMethod': ('Longest contiguous 0.5-isovalue segmentation chord crossing the trunk core, '
                         'parallel to patient AP projected into a plane normal to the local aortic centerline. '
                         'Offsets are restricted to 5 mm on either side of the core.'),
        'axialStationsCaseVox': STATIONS, 'proximalIliacMaskSliceVox': iliac_start,
        'centerRayMaximumAirAndBoneSamples': np.max(rays, axis=0).tolist(),
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *masks]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path, help='Native pinned s1233 CT and segmentations directory')
    parser.add_argument('sweeps_dir', type=Path)
    args = parser.parse_args()
    track, = read_tracks()
    destination = args.sweeps_dir / track['id']
    if destination.exists():
        parser.error(f'Choose a fresh staging directory: {destination}')
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.sweeps_dir) as stage:
        source = Path(stage) / track['id']
        source.mkdir()
        build(args.case, source, track)
        source.rename(destination)


if __name__ == '__main__':
    main()
