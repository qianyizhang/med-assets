"""Build the right axillary normal-node B-mode teaching sweep."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd

from axilla_anatomy import MARKER_ANGLE, START_ROTATION_DEG, WINDOW_XZ, load_anatomy
from breast_anatomy import FEMALE_SKIN
from build_abdomen import measure_landmark, overlay, section_palette, section_palette_sha256
from build_breast import exposed_skin, first_profile, grid_axes, section_mask
from build_study import fine_scatter
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
CASE = 'hra-right-axilla-teaching'
STOP_ROTATION_DEG = 90
# Lens face superellipse from the shared linear-probe profile in scene.js.
LENS_HALF_DEPTH_MM = 6.5
LENS_ROUNDNESS = .35


def read_axilla_tracks():
    return [json.loads((HERE / 'axilla-track.json').read_text())]


def pose_recipe_sha256(sweep_id):
    if sweep_id != 'axilla':
        raise ValueError(f'Unknown axilla sweep: {sweep_id}')
    recipe = [WINDOW_XZ, MARKER_ANGLE, START_ROTATION_DEG, STOP_ROTATION_DEG, KEYFRAMES]
    return sha256(json.dumps(recipe, separators=(',', ':')).encode())


def render_recipe_sha256(sweep_id):
    """Bind delivery to the anatomy, section sampler and scatter recipe."""
    if sweep_id != 'axilla':
        raise ValueError(f'Unknown axilla sweep: {sweep_id}')
    names = ('axilla_anatomy.py', 'build_axilla.py', 'build_breast.py', 'build_study.py')
    recipe = {name: sha256((HERE / name).read_bytes()) for name in names}
    return sha256(json.dumps(recipe, sort_keys=True, separators=(',', ':')).encode())


def frames_from_windows(anatomy):
    along, across, beam = anatomy.basis.T
    for index in range(FRAME_COUNT):
        degrees = np.interp(index, (0, *KEYFRAMES), (START_ROTATION_DEG, 0, STOP_ROTATION_DEG))
        angle = np.deg2rad(degrees)
        width = np.cos(angle) * along + np.sin(angle) * across
        yield {'contact': anatomy.contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist(),
               'degrees': round(float(degrees - START_ROTATION_DEG), 1)}


def lens_rim_offsets(torso, frames, width_mm):
    angles = np.linspace(0, 2 * np.pi, 32, endpoint=False)
    x, y = np.cos(angles), np.sin(angles)
    lateral = np.sign(x) * np.abs(x)**LENS_ROUNDNESS * width_mm / 2
    elevational = np.sign(y) * np.abs(y)**LENS_ROUNDNESS * LENS_HALF_DEPTH_MM
    contacts, widths, beams = (np.asarray([pose[name] for pose in frames]) for name in ('contact', 'width', 'beam'))
    elevational_axes = np.cross(beams, widths)
    rim = contacts[:, None] + (lateral[None, :, None] * widths[:, None]
                              + elevational[None, :, None] * elevational_axes[:, None]) / VOXEL_MM
    return outer_contact_offsets(*torso, rim.reshape(-1, 3), np.repeat(beams, len(angles), axis=0))


def approach_clearance(torso, frames, width_mm):
    """Measure the shared linear housing and proximal cable against the skin."""
    contact = np.asarray(frames[0]['contact'])
    beam = np.asarray(frames[0]['beam'])
    widths = np.array([frame['width'] for frame in frames])
    elevation = np.cross(beam, widths)
    half, grip = width_mm / 2, width_mm / 2 * .45
    # Profiles sampled at the widest parts and transitions of the shared probe.
    profiles = [(3.2, half + .6, 8.3, .4), (5.6, half + 1, 10.7, .45),
                (11, half + .8, 12, .47), (18, half * .91, 12.8, .52),
                (26, half * .72, 13, .61), (35, grip + 1.5, 13.4, .78),
                (42, grip, 13.5, .87), (56, grip, 13.2, .87),
                (66, grip - 1.1, 11.8, .91), (72, grip - 3, 9.7, .93),
                (75, 7, 7.7, .95), (76, 5, 5.5, 1), (79.5, 4.7, 4.7, 1),
                (84, 2.8, 2.8, 1), (102, 1.65, 1.65, 1)]
    angles = np.arange(16) * np.pi / 8
    x, y = np.cos(angles), np.sin(angles)
    sample_shell = []
    for outward, lateral, thickness, exponent in profiles:
        u = lateral * np.sign(x) * np.abs(x)**exponent
        v = thickness * np.sign(y) * np.abs(y)**exponent
        sample_shell.append(contact + (widths[:, None] * u[None, :, None]
                            + elevation[:, None] * v[None, :, None] - beam * outward) / VOXEL_MM)
    samples = np.concatenate(sample_shell, axis=1).reshape(-1, 3)
    vertices, faces = torso
    triangles = vertices[faces]
    centered = triangles - contact
    span = np.einsum('ijk,k->ij', centered, beam)
    radial = centered - span[..., None] * beam
    center = radial.mean(axis=1)
    radius = np.linalg.norm(radial - center[:, None], axis=2).max(axis=1)
    region = np.linalg.norm(center, axis=1) - radius <= (half + 14) / VOXEL_MM
    hits = outer_contact_offsets(vertices, faces[region], samples, np.broadcast_to(beam, samples.shape))
    return {'minimumHousingClearanceMm': round(float(hits.min()), 3),
            'minimumProximalCableClearanceMm': round(float(hits.reshape(len(frames), len(profiles), -1)[:, -2:].min()), 3),
            'samplesPerFrame': len(profiles) * len(angles)}


def sampled_section(anatomy, frame, grid):
    lateral, depth, field = grid
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    xyz = (contact[:, None, None] + (width[:, None, None] * lateral[None, None, :]
           + beam[:, None, None] * depth[None, :, None]) / VOXEL_MM)
    labels = {name: section_mask(mesh, contact, width, beam, lateral, depth) & field
              for name, mesh in anatomy.meshes.items() if name != 'torso'}
    skin, inside = exposed_skin(anatomy.meshes['torso'], contact, width, beam, lateral, depth, field)
    return labels, xyz, skin, inside


def brightness(labels, xyz, grid, skin, inside, anatomy):
    _, depth, field = grid
    local = np.einsum('ij,ihw->jhw', anatomy.basis, xyz - anatomy.contact[:, None, None]) * VOXEL_MM
    along, across, down = local
    fine = nd.gaussian_filter(fine_scatter(xyz), (.54, 1.0))
    broad = fine_scatter(local * np.array([.040, .050, .073])[:, None, None])
    lobules = (np.cos(.61*along + .43*across + .12*down + 1.3*broad)
               + .8*np.cos(-.48*along + .72*across + .21*down - broad)
               + .63*np.cos(1.21*down + .15*along + .27*across + 1.6*broad))
    septa = np.exp(-((lobules - .24) / .27)**2)
    superficial = 1 / (1 + np.exp((down - 17) / 3))
    fascia_depth = down - (8.9 + .055*along - .051*across + 2.2*broad)
    fascia = np.exp(-(fascia_depth / .44)**2) + .42*np.exp(-((fascia_depth + 1.25) / .31)**2)

    cortex = nd.gaussian_filter(labels['axillary_node'].astype(float), (1.48, 2.20))
    hilum = nd.gaussian_filter(labels['fatty_hilum'].astype(float), (1.08, 1.66))
    muscle = nd.gaussian_filter(labels['axillary_muscle'].astype(float), (1.3, 1.9))
    vein = nd.gaussian_filter(labels['axillary_vein'].astype(float), (1.25, 1.85))
    artery = nd.gaussian_filter(labels['axillary_artery'].astype(float), (1.22, 1.78))
    vessel = np.maximum(vein, artery)
    fibers = np.clip(np.cos(2.8*(down - .12*along + .19*across + .013*across**2)
                            + broad*4.0), 0, 1)**4
    fiber_texture = fibers * np.clip(.5 + fine + 1.45*broad, .10, 1)
    deep_planes = np.clip(np.cos(1.48*down + .25*along - .13*across + broad*1.8), 0, 1)**9
    b = (57 + (64 + 34 * superficial) * fine + 18 * broad + 8 * lobules
         + (14 + 37 * superficial) * septa + 46 * fascia
         + 14 * (1 - superficial) * deep_planes) * inside
    b = b * (1 - muscle) + muscle * (36 + 46 * fine + 49 * fiber_texture + 23 * broad)
    b = b * (1 - cortex) + cortex * (25 + 34 * fine + 15 * broad)
    b = b * (1 - hilum) + hilum * (118 + 72 * fine + 36 * broad + 18*septa)
    b = b * (1 - vessel) + vessel * (8 + 16 * fine)
    b += (np.abs(np.gradient(cortex, axis=0)) * (59 + 28*broad)
          + np.abs(np.gradient(muscle, axis=0)) * (118 + 19*fine)
          + np.abs(np.gradient(vessel, axis=0)) * (101 + 31*broad))
    b += (115 + 38*fine) * nd.gaussian_filter(skin.astype(float), (.78, 1.25))
    b *= np.exp(-np.maximum(depth, 0)[:, None] / 153)
    return np.where(field, np.clip(b, 0, 239), 0).astype('u1')


def node_dimensions(node, lateral, depth):
    rows, cols = np.nonzero(node)
    coordinates = np.column_stack((lateral[cols], depth[rows]))
    _, directions = np.linalg.eigh(np.cov(coordinates.T))
    minor, major = np.ptp(np.einsum('ij,jk->ik', coordinates, directions), axis=0)
    return float(major), float(minor)


def validate_frame(frame_index, labels, inside, gray, grid):
    lateral, depth, _ = grid
    node, hilum = (labels[name] for name in ('axillary_node', 'fatty_hilum'))
    cortex = node & ~hilum
    if cortex.sum() < 200 or hilum.sum() < 200 or np.any(node & ~inside) or np.any(hilum & ~node):
        raise ValueError(f'Frame {frame_index} misses the enclosed node and hilum')
    vessels = [labels[key] for key in ('axillary_vein', 'axillary_artery')]
    if any(vessel.sum() < 40 or np.any(vessel & ~inside) or np.any(vessel & node) for vessel in vessels):
        raise ValueError(f'Frame {frame_index} misses separate deep regional vessels')
    node_front = depth[np.where(node)[0]].min()
    for vessel in vessels:
        if depth[np.where(vessel)[0]].min() < node_front + 5:
            raise ValueError(f'Frame {frame_index} loses the depth order from node to axillary vessels')
    contrast = np.median(gray[hilum]) - np.median(gray[cortex])
    if contrast < 65:
        raise ValueError(f'Frame {frame_index} loses the bright hilar fat / darker cortex contrast')
    major, minor = node_dimensions(node, lateral, depth)
    if ((frame_index == KEYFRAMES[0] and major / minor < 1.85)
            or (frame_index == KEYFRAMES[1] and major / minor > 1.25)):
        raise ValueError(f'Frame {frame_index} does not show the intended node axis')
    center_col = np.argmin(np.abs(lateral))
    cortex_depth = np.where(cortex[:, center_col])[0]
    hilum_center = np.where(hilum[:, center_col])[0]
    if not len(hilum_center):
        raise ValueError(f'Frame {frame_index} does not pass through the fatty hilum')
    sample = depth[1] - depth[0]
    superficial = np.count_nonzero(cortex_depth < hilum_center[0]) * sample
    deep = np.count_nonzero(cortex_depth > hilum_center[-1]) * sample
    if not (.6 < superficial < 2.6 and .6 < deep < 2.6):
        raise ValueError(f'Frame {frame_index} does not show a thin cortex either side of the hilum')
    return {'outerSpanMm': [round(major, 2), round(minor, 2)],
            'centralSuperficialCortexMm': round(superficial, 2), 'centralDeepCortexMm': round(deep, 2),
            'medianHilumCortexGrayDifference': float(contrast)}


def build(track, output, anatomy):
    grid = grid_axes(track)
    frames = list(frames_from_windows(anatomy))
    offsets, profile = first_profile(anatomy.meshes['torso'], frames, track['fieldWidthMm'])
    rim = lens_rim_offsets(anatomy.meshes['torso'], frames, track['fieldWidthMm'])
    approach = approach_clearance(anatomy.meshes['torso'], frames, track['fieldWidthMm'])
    max_contact = float(np.abs(offsets[:, offsets.shape[1] // 2]).max())
    extremes = min(offsets.min(), rim.min()), max(offsets.max(), rim.max())
    if max_contact > .35 or extremes[0] < -3 or extremes[1] > 3:
        raise ValueError(f'Axilla footprint fit exceeds limits: {extremes[0]:+.2f} to {extremes[1]:+.2f} mm')
    if approach['minimumHousingClearanceMm'] < 0:
        raise ValueError(f'Axilla approach intersects exterior: {approach}')
    parts = [part['id'] for part in track['parts']]
    palette = section_palette(track)
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    for name in ['torso', *parts]:
        (scenes / f'{name}.mesh').write_bytes(mesh_bytes(*anatomy.meshes[name]))
    evidence = {}
    for index, frame in enumerate(frames):
        labels, xyz, skin, inside = sampled_section(anatomy, frame, grid)
        gray = brightness(labels, xyz, grid, skin, inside, anatomy)
        morphology = validate_frame(index, labels, inside, gray, grid)
        labels['axillary_node'] &= ~labels['fatty_hilum']
        if index in KEYFRAMES:
            evidence[str(index)] = {**morphology,
                                    **{name: measure_landmark(labels[name], gray) for name in parts}}
        Image.fromarray(gray).save(media / f'scan-{index:02}.webp', quality=91)
        Image.fromarray(overlay(gray, labels, palette)).save(media / f'section-{index:02}.webp', quality=88)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        **anatomy.receipt,
        'case': CASE, 'probeType': 'linear', 'fieldShape': 'rectangle', 'voxelMm': VOXEL_MM,
        'fieldWidthMm': track['fieldWidthMm'], 'sectorDepthMm': track['sectorDepthMm'],
        'samplePitchMm': round(float(grid[1][1] - grid[1][0]), 8), 'exterior': track['exterior'],
        'surfaceMaxOuterContactErrorMm': round(max_contact, 4), 'apertureOffsetsMm': profile,
        'lensRimFirstHitMm': {'samplesPerFrame': rim.size // len(frames),
                              'min': round(float(rim.min()), 3), 'max': round(float(rim.max()), 3)},
        'approachClearance': approach,
        'angleOriginFrame': 0, 'framesChecked': len(frames),
        'poseRecipeSha256': pose_recipe_sha256(track['id']), 'sectionPaletteSha256': section_palette_sha256(track),
        'renderRecipeSha256': render_recipe_sha256(track['id']),
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *parts]))
    print(f'Axilla: {len(frames)} poses checked, footprint first-hit offsets {extremes[0]:+.2f} to {extremes[1]:+.2f} mm')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    parser.add_argument('--skin', type=Path, default=FEMALE_SKIN, help='Pinned female HRA skin GLB')
    args = parser.parse_args()
    target = args.sweeps_dir / 'axilla'
    if target.exists():
        parser.error('Choose a fresh destination for axilla.')
    [track] = read_axilla_tracks()
    anatomy = load_anatomy(args.skin)
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage:
        output = Path(stage) / 'axilla'
        output.mkdir()
        build(track, output, anatomy)
        output.rename(target)


if __name__ == '__main__':
    main()
