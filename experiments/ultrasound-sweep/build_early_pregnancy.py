"""Replay an authored transabdominal route through the early-pregnancy landmarks."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation, Slerp
from skimage.measure import marching_cubes

from build_abdomen import ImagingGrid, axes, measure_landmark, overlay, section_palette, section_palette_sha256
from build_study import fine_scatter
from delivery import detail_files, sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM
from pregnancy_anatomy import FIELDS as LATE_FIELDS
from pregnancy_anatomy import ellipsoid, smooth_union, tapered_segment, torso
from prepare_scenes import mesh_bytes

TRACK_PATH = Path(__file__).with_name('early-pregnancy-track.json')
SAC_CENTRE = (3.6, -8, 0)
SAC_RADII = (12, 12, 13.1)
AMNION_CENTRE = (3.6, -10.0, 2.0)
AMNION_RADII = (7.8, 7.5, 8.2)
YOLK_CENTRE = (4.1, -4.2, -7.9)
YOLK_RADII = (2.25, 2.22, 2.37)
CARDIAC_CENTRE = (3.6, -8.0, 1.65)
CROWN = (3.6, -8.5, 6.7)
RUMP = (3.6, -8.5, -4.0)


def read_tracks():
    return [json.loads(TRACK_PATH.read_text())]


def pose_recipe_sha256(slug):
    track = next(track for track in read_tracks() if track['id'] == slug)
    recipe = [track['windows'], track['landmarkMinimums'],
              [(stop['frame'], stop['detail']['roi']) for stop in track['stops']]]
    return sha256(json.dumps(recipe, separators=(',', ':')).encode())


def model_recipe_sha256():
    # Include the supplier of the reused skin field and field primitives.
    source = Path(__file__)
    return sha256(source.read_bytes() + source.with_name('pregnancy_anatomy.py').read_bytes())


def uterine_corpus(xyz):
    x, y, z = xyz
    y, z = y + 18, z + 13
    # The superior end of the corpus tips forward from the cervix.
    local = (x, .895*y - .446*z, .446*y + .895*z)
    return ellipsoid(local, (0, 0, 0), (36, 26, 40))


def gestational_rim(xyz):
    outer = ellipsoid(xyz, SAC_CENTRE, (14.4, 14.6, 15.65))
    return np.maximum(outer, -gestational_sac(xyz))


def gestational_sac(xyz):
    return ellipsoid(xyz, SAC_CENTRE, SAC_RADII)


def uterus(xyz):
    cervix = tapered_segment(xyz, (0, -33, -38), (0, -35, -61), 12, 9.5)
    exterior = smooth_union(uterine_corpus(xyz), cervix, 6)
    return np.maximum.reduce((exterior, -gestational_rim(xyz), -gestational_sac(xyz)))


def maternal_bladder(xyz):
    # A filled anterior bladder provides the suprapubic acoustic window.
    return ellipsoid(xyz, (0, 39, -35), (42, 23, 31))


def amnion_envelope(xyz):
    return ellipsoid(xyz, AMNION_CENTRE, AMNION_RADII)


def amnion(xyz):
    envelope = amnion_envelope(xyz)
    return np.maximum(envelope, -envelope - .45)


def yolk_lumen(xyz):
    return ellipsoid(xyz, YOLK_CENTRE, tuple(radius - .55 for radius in YOLK_RADII))


def yolk_sac(xyz):
    return np.maximum(ellipsoid(xyz, YOLK_CENTRE, YOLK_RADII), -yolk_lumen(xyz))


def embryo(xyz):
    # A flexed cranial end and continuous curved trunk retain embryonic proportions.
    head = ellipsoid(xyz, (3.6, -8.5, 4.1), (2.15, 2.8, 2.6))
    upper_trunk = tapered_segment(xyz, (3.6, -10.65, 3.2), (3.6, -10.3, -.8), 1.62, 1.6)
    caudal = tapered_segment(xyz, (3.6, -10.3, -.8), (3.6, -8.5, -2.6), 1.6, 1.4)
    thorax = ellipsoid(xyz, (3.6, -8.15, 1.15), (1.58, 1.44, 1.95))
    return smooth_union(smooth_union(head, upper_trunk, .62), smooth_union(caudal, thorax, .65), .8)


def cardiac_region(xyz):
    # Teaching overlay only. This field does not alter the modeled grayscale.
    return ellipsoid(xyz, CARDIAC_CENTRE, (.9, .93, 1.12))


FIELDS = {
    'torso': LATE_FIELDS['torso'],
    'uterus': (uterus, (-39, -48, -73), (39, 16, 30), .8),
    'maternal_bladder': (maternal_bladder, (-44, 14, -71), (44, 65, -2), .8),
    'gestational_rim': (gestational_rim, (-13, -24, -18), (20, 8, 18), .25),
    'gestational_sac': (gestational_sac, (-10, -22, -16), (18, 6, 16), .28),
    'amnion': (amnion, (-5, -19, -7), (12, -2, 11), .13),
    'yolk_sac': (yolk_sac, (0, -8, -12), (8, -1, -4), .09),
    'embryo': (embryo, (0, -14, -5.5), (8, -4, 8), .12),
    'cardiac_region': (cardiac_region, (2, -10, -.1), (5, -6, 3.4), .075),
}


def mesh_for(name):
    field, lo, hi, step = FIELDS[name]
    grid = [np.arange(a, b + step, step, dtype=np.float32) for a, b in zip(lo, hi, strict=True)]
    values = field(np.meshgrid(*grid, indexing='ij', sparse=True))
    if any(np.min(np.take(values, [0, -1], axis=axis)) <= 0 for axis in range(3)):
        raise ValueError(f'{name} crosses its mesh bounds')
    vertices, faces, _, _ = marching_cubes(values, 0, spacing=(step,) * 3, gradient_direction='descent')
    return (vertices + lo) / VOXEL_MM, faces


def poses(track, exterior):
    windows = track['windows']
    stations = [window['frame'] for window in windows]
    sites = np.asarray([window['skinSiteMm'] for window in windows])
    orientations = Rotation.from_matrix([axes(window['outward'], window['marker']) for window in windows])
    turn = Slerp(stations, orientations)
    frames = []
    for i in range(FRAME_COUNT):
        x, z = [np.interp(i, stations, positions) for positions in sites.T]
        y = brentq(lambda y: torso((x, y, z)), 0, 120)
        pose = turn(i)
        width, _, beam = pose.as_matrix().T
        frames.append({
            'contact': (np.array([x, y, z]) / VOXEL_MM).tolist(),
            'width': width.tolist(),
            'beam': beam.tolist(),
            'degrees': round(np.rad2deg((pose * orientations[0].inv()).magnitude()), 1),
        })
    contacts, beams = (np.asarray([frame[key] for frame in frames]) for key in ('contact', 'beam'))
    max_error = float(np.max(np.abs(outer_contact_offsets(*exterior, contacts, beams))))
    travel = np.linalg.norm(np.diff(contacts, axis=0), axis=1) * VOXEL_MM
    if max_error > .2 or travel.min() < .2 or travel.max() > 3:
        raise ValueError(f'Probe contact error {max_error:.3f} mm, travel {travel.min():.2f}–{travel.max():.2f} mm/frame')
    return frames, {
        'surfaceMaxOuterContactErrorMm': round(max_error, 3),
        'skinTravelMm': round(float(travel.sum()), 2),
    }


def sample_section(grid, frame):
    scene = ImagingGrid.coordinates(frame, grid.x, grid.y)
    mm = scene * VOXEL_MM
    fields = {name: field(mm) for name, (field, _, _, _) in FIELDS.items()}
    masks = {name: (field <= 0) & grid.field for name, field in fields.items()}
    regions = dict(masks)
    regions['gestational_sac'] = masks['gestational_sac'] & ~(masks['yolk_sac'] | masks['amnion'] | masks['embryo'])
    regions['embryo'] = masks['embryo'] & ~masks['cardiac_region']

    skin_distance = -fields['torso']
    # Sample the scatter bands in the patient coordinate frame. Blur the
    # anatomical returns, then apply the high-frequency echo texture so
    # a magnified section preserves fine grains along the same interfaces.
    background = fine_scatter(scene * .46)
    resolved = fine_scatter(scene * 1.3)
    micro = fine_scatter(scene * 2.5 + np.array([.61, .27, .16])[:, None, None])
    streak = fine_scatter(scene * np.array([.85, .53, 1.55])[:, None, None])
    texture = 84 * resolved + 57 * micro + 27 * streak
    fascia = 29 * np.exp(-((skin_distance - 13 - 2.4 * background) / 1.8)**2)
    tissue = 46 + 12 * background + fascia - 9 * np.exp(-((skin_distance - 6) / 4.6)**2)
    tissue = np.where(masks['uterus'], 54 + 14 * background, tissue)
    endometrial_line = tapered_segment(mm, (1, -27, -32), (3.6, -12, -7), .62, 1.3)
    tissue += np.clip(.72 - endometrial_line, 0, 1) * 25 * masks['uterus']
    # Chorion, amnion and yolk sac have distinct return levels. Keep the
    # fluid-filled regions dark and suppress their fine scattering.
    fluid = masks['maternal_bladder'] | regions['gestational_sac']
    for name, level in (('gestational_rim', 112), ('amnion', 83), ('yolk_sac', 170), ('embryo', 110)):
        tissue = np.where(masks[name], level + 9 * background, tissue)
    tissue = np.where(fluid, 3, tissue)

    pitch = grid.x[0, 1] - grid.x[0, 0]
    scale = .41 / pitch
    blur = (.62 * scale, .85 * scale)
    soft = nd.gaussian_filter(tissue, blur)
    scatter = nd.gaussian_filter(np.where(fluid, .055, .85), blur)
    dy, dx = np.gradient(soft)
    edge = np.abs(dy * np.cos(grid.angle) + dx * np.sin(grid.angle))
    skin = np.exp(-((skin_distance - .72) / .88)**2)
    gray = (soft + scatter * texture + 1.15 * edge * scale + 62 * skin) * np.exp(-np.maximum(grid.depth, 0) / 290)
    gray = np.where(masks['torso'], np.clip(gray, 0, 242), 0).astype(np.uint8)
    return gray, masks, regions


def check_anatomy(meshes):
    mm = {name: verts.T * VOXEL_MM for name, (verts, _) in meshes.items()}
    margin_tests = {
        'maternalSkin': min(-np.max(torso(points)) for name, points in mm.items() if name != 'torso'),
        'intrauterineSac': -np.max(uterine_corpus(mm['gestational_rim'])),
        'bladderOutsideUterus': np.min(uterine_corpus(mm['maternal_bladder'])),
        'yolkInsideGestationalSac': -np.max(gestational_sac(mm['yolk_sac'])),
        'yolkOutsideAmnion': np.min(amnion_envelope(mm['yolk_sac'])),
        'embryoInsideAmnion': -np.max(amnion_envelope(mm['embryo'])),
        'amnionInsideGestationalSac': -np.max(gestational_sac(mm['amnion'])),
        'cardiacRegionInsideEmbryo': -np.max(embryo(mm['cardiac_region'])),
    }
    if min(margin_tests.values()) <= 0:
        raise ValueError(f'Early-pregnancy containment failed: {margin_tests}')
    if max(abs(embryo(CROWN)), abs(embryo(RUMP))) > .12:
        raise ValueError('Modeled crown and rump points no longer lie on the embryo surface')
    points = np.ogrid[-5:13:.4, -19:-1:.4, -8:12:.4]
    fluid = (amnion_envelope(points) < -.45) & (embryo(points) > 0)
    fluid_ml = np.count_nonzero(fluid) * .4**3 / 1000
    if not 1.2 < fluid_ml < 5:
        raise ValueError(f'Recheck the authored seven-week amniotic space: {fluid_ml:.2f} mL')
    return {
        'modeledAmnioticFluidMl': round(fluid_ml, 2),
        'positiveClearanceFieldMm': {name: round(float(value), 3) for name, value in margin_tests.items()},
        'modeledCrownRumpMm': round(float(np.linalg.norm(np.subtract(CROWN, RUMP))), 2),
        'gestationalSacInnerDiametersMm': [2 * radius for radius in SAC_RADII],
        'yolkSacOuterDiametersMm': [2 * radius for radius in YOLK_RADII],
    }


def build_track(track, output):
    meshes = {name: mesh_for(name) for name in FIELDS}
    anatomy = check_anatomy(meshes)
    frames, contact = poses(track, meshes['torso'])
    grid = ImagingGrid(track['sectorDepthMm'])
    palette = section_palette(track)
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    for name, mesh in meshes.items():
        (scenes / f'{name}.mesh').write_bytes(mesh_bytes(*mesh))
    details = {stop['frame']: ImagingGrid(track['sectorDepthMm'], roi=stop['detail']['roi'])
               for stop in track['stops']}
    evidence = {}
    for i, pose in enumerate(frames):
        gray, masks, regions = sample_section(grid, pose)
        if np.count_nonzero(masks['gestational_sac']) < 900:
            raise ValueError(f'Frame {i} loses the gestational sac')
        if minimums := track['landmarkMinimums'].get(str(i)):
            evidence[str(i)] = {name: measure_landmark(masks[name], gray) for name in minimums}
            for name, minimum in minimums.items():
                if evidence[str(i)][name]['largestSectionPixels'] < minimum:
                    raise ValueError(f'Frame {i} misses {name}: {evidence[str(i)][name]}')
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=91)
        Image.fromarray(overlay(gray, regions, palette)).save(media / f'section-{i:02}.webp', quality=88)
        if i in details:
            detail_gray, _, detail_regions = sample_section(details[i], pose)
            Image.fromarray(detail_gray).save(media / f'detail-scan-{i:02}.webp', quality=93)
            Image.fromarray(overlay(detail_gray, detail_regions, palette)).save(
                media / f'detail-section-{i:02}.webp', quality=91)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    receipt = {
        'case': track['case'],
        'coordinateFrame': 'authored maternal RAS in 1.5 mm scene units',
        'voxelMm': VOXEL_MM,
        'exterior': track['exterior'],
        'sectorDepthMm': track['sectorDepthMm'],
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG,
        'lensRadiusMm': LENS_RADIUS_MM,
        'poseRecipeSha256': pose_recipe_sha256(track['id']),
        'modelRecipeSha256': model_recipe_sha256(),
        'sectionPaletteSha256': section_palette_sha256(track),
        **contact,
        **anatomy,
        'frames': evidence,
    }
    (output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    write_manifest(output, sweep_files(meshes) + detail_files(track['stops']))
    print(f'{track["id"]}: {len(frames)} poses, {contact["skinTravelMm"]:.1f} mm skin travel, '
          f'{contact["surfaceMaxOuterContactErrorMm"]:.3f} mm maximum central contact error', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    args = parser.parse_args()
    track, = read_tracks()
    output = args.sweeps_dir / track['id']
    if output.exists():
        parser.error('Choose a fresh destination for the early-pregnancy sweep.')
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage:
        staged = Path(stage) / track['id']
        staged.mkdir()
        build_track(track, staged)
        staged.rename(output)


if __name__ == '__main__':
    main()
