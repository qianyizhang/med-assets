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
from breast_compression import contact_rows, sample_contact_plate, smoothstep
from build_abdomen import measure_landmark, overlay, section_palette, section_palette_sha256
from build_breast import exposed_skin, footprint_hits, grid_axes, seat_contact_face, section_mask
from build_study import fine_scatter
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
CASE = 'hra-right-axilla-teaching'
STOP_ROTATION_DEG = 90
PORTRAIT_DEPTH_MM = 21.5


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
    names = ('axilla_anatomy.py', 'build_axilla.py', 'build_breast.py', 'breast_compression.py', 'build_study.py')
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


def seat_frame(torso, frame, width_mm):
    seated = seat_contact_face(torso, frame, width_mm, preserve_plane=True)
    rig = seated['contactRig']
    rig['featherMm'] = 8
    lateral = np.linspace(-width_mm / 2, width_mm / 2, 33)
    elevation = np.linspace(-rig['faceElevationMm'] / 2, rig['faceElevationMm'] / 2, 17)
    hits = footprint_hits(torso, seated, lateral, elevation)
    # Advance to the deepest checked native point. Seating pushes skin inward.
    advance = hits.max() + .01
    seated['contact'] = (np.asarray(seated['contact']) + np.asarray(seated['beam']) * advance / VOXEL_MM).tolist()
    rig['surfaceMm'] = (np.asarray(rig['surfaceMm']) - advance).round(5).tolist()
    vertices, faces = torso
    contact, width, beam = (np.asarray(seated[key]) for key in ('contact', 'width', 'beam'))
    basis = np.stack((width, np.cross(beam, width), beam))
    x, y, z = np.einsum('ij,kj->ki', basis, (vertices - contact)*VOXEL_MM).T
    shift = (deformed_skin_depth(rig, x, y, z) - z) / VOXEL_MM
    rendered_vertices = vertices + shift[:, None] * beam
    deformed_hits = footprint_hits((rendered_vertices, faces), seated, lateral, elevation)
    return seated, hits - advance, deformed_hits


def deformed_skin_depth(rig, lateral, elevation, native):
    x, y = np.broadcast_arrays(lateral, elevation)
    half_x, half_y = rig['faceWidthMm'] / 2, rig['faceElevationMm'] / 2
    grid_x = np.clip((x + half_x) / (2 * half_x), 0, 1) * (len(rig['lateralMm']) - 1)
    grid_y = np.clip((y + half_y) / (2 * half_y), 0, 1) * (len(rig['elevationMm']) - 1)
    surface = nd.map_coordinates(np.asarray(rig['surfaceMm']), (grid_y, grid_x), order=1)
    ux = (np.abs(x) - half_x) / rig['featherMm']
    uy = (np.abs(y) - half_y) / rig['featherMm']
    footprint = (1 - smoothstep(ux)) * (1 - smoothstep(uy))
    depth_weight = 1 - smoothstep((native - surface) / rig['settleDepthMm'])
    return native - surface * footprint * depth_weight


def approach_clearance(torso, frames, width_mm):
    """Measure the shared linear housing and proximal cable against the skin."""
    contacts = np.asarray([f['contact'] for f in frames])
    contact = contacts[0]
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
    sample_shell, lateral_mm, elevation_mm = [], [], []
    for outward, lateral, thickness, exponent in profiles:
        u = lateral * np.sign(x) * np.abs(x)**exponent
        v = thickness * np.sign(y) * np.abs(y)**exponent
        lateral_mm.append(u)
        elevation_mm.append(v)
        sample_shell.append(contacts[:, None] + (widths[:, None] * u[None, :, None]
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
    depths = np.array(profiles)[:, 0, None]
    clearances = np.stack([depths + deformed_skin_depth(frame['contactRig'], lateral_mm, elevation_mm, native - depths)
                           for frame, native in zip(frames, hits.reshape(len(frames), len(profiles), -1), strict=True)])
    return {'minimumHousingClearanceMm': round(float(clearances[:, :-2].min()), 3),
            'minimumProximalCableClearanceMm': round(float(clearances[:, -2:].min()), 3),
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
    hilar_strands = np.clip(np.cos(2.4*(down + .10*along - .18*across) + 2.5*broad), 0, 1)**4
    b = b * (1 - hilum) + hilum * (108 + 69 * fine + 37 * broad + 21*hilar_strands)
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
    if (np.any(vessels[0] & vessels[1])
            or any(np.any(vessel & ~inside) or np.any(vessel & node) for vessel in vessels)):
        raise ValueError(f'Frame {frame_index} does not show separate regional structures')
    if frame_index == KEYFRAMES[0] and sum(vessel.sum() for vessel in vessels) > .06 * node.sum():
        raise ValueError('Long-axis portrait includes too much of the regional vessels')
    if frame_index == KEYFRAMES[1] and any(vessel.sum() < 40 for vessel in vessels):
        raise ValueError('Short-axis regional field misses one of the vessels')
    node_front = depth[np.where(node)[0]].min()
    node_back = depth[np.where(node)[0]].max()
    for vessel in vessels:
        if vessel.any() and depth[np.where(vessel)[0]].min() < node_front + 5:
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
    if not (.44 < superficial < 2.6 and .44 < deep < 2.6):
        raise ValueError(f'Frame {frame_index} does not show a thin cortex either side of the hilum '
                         f'({superficial:.2f}, {deep:.2f} mm)')
    vessel_centroids = []
    for vessel in vessels:
        rows, cols = np.nonzero(vessel)
        center = [round(float(lateral[cols].mean()), 2), round(float(depth[rows].mean()), 2)] if len(rows) else None
        vessel_centroids.append(center)
    return {'outerSpanMm': [round(major, 2), round(minor, 2)],
            'nodeAnteriorPosteriorDepthMm': [round(float(node_front), 2), round(float(node_back), 2)],
            'vesselPixels': [int(vessel.sum()) for vessel in vessels],
            'centralSuperficialCortexMm': round(superficial, 2), 'centralDeepCortexMm': round(deep, 2),
            'vesselCentersLateralDepthMm': dict(zip(('axillary_vein', 'axillary_artery'), vessel_centroids, strict=True)),
            'medianHilumCortexGrayDifference': float(contrast)}


def acquisition_grid(track, imaging_depth_mm):
    grid = grid_axes({**track, 'sectorDepthMm': imaging_depth_mm})
    lateral, depth, field = grid
    pitch = depth[1] - depth[0]
    pad = int(np.ceil(10 / pitch))
    native_depth = depth[0] + np.arange(-pad, len(depth) + pad) * pitch
    native_field = np.broadcast_to(abs(lateral) <= track['fieldWidthMm'] / 2,
                                   (len(native_depth), len(lateral)))
    return grid, (lateral, native_depth, native_field)


def imaging_depth(index, regional_depth_mm):
    slide = smoothstep((index - KEYFRAMES[0]) / (KEYFRAMES[1] - KEYFRAMES[0]))
    return round(float(PORTRAIT_DEPTH_MM + slide * (regional_depth_mm - PORTRAIT_DEPTH_MM)), 3)


def build(track, output, anatomy):
    torso = anatomy.meshes['torso']
    fitted = [seat_frame(torso, frame, track['fieldWidthMm']) for frame in frames_from_windows(anatomy)]
    frames, offsets, corrected = zip(*fitted, strict=True)
    offsets, corrected = np.asarray(offsets), np.asarray(corrected)
    approach = approach_clearance(torso, frames, track['fieldWidthMm'])
    max_contact = float(np.abs(corrected).max())
    if max_contact > .38 or offsets.min() < -6 or offsets.max() > 0:
        raise ValueError(f'Axilla footprint fit exceeds limits: {max_contact:.2f} mm post-seat, '
                         f'{offsets.min():+.2f} to {offsets.max():+.2f} mm native.')
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
        frame['imagingDepthMm'] = imaging_depth(index, track['sectorDepthMm'])
        grid, native_grid = acquisition_grid(track, frame['imagingDepthMm'])
        lateral, depth, field = grid
        _, native_depth, _ = native_grid
        labels, xyz, skin, inside = sampled_section(anatomy, frame, native_grid)
        gray = brightness(labels, xyz, native_grid, skin, inside, anatomy)
        rows = contact_rows(frame['contactRig'], lateral, depth)
        gray = sample_contact_plate(gray, native_depth, rows, order=1, field=field)
        labels = {name: sample_contact_plate(mask, native_depth, rows, order=0, field=field).astype(bool)
                  for name, mask in labels.items()}
        inside = sample_contact_plate(inside, native_depth, rows, order=0, field=field).astype(bool)
        sampled_skin = sample_contact_plate(skin, native_depth, rows, order=0, field=field)
        per_column = np.any(sampled_skin & (depth[:, None] < 1.8), axis=0)
        if (per_column & field.any(0)).sum() < .94 * field.any(0).sum():
            raise ValueError(f'Frame {index} misses flat acoustic contact across the active aperture.')
        morphology = validate_frame(index, labels, inside, gray, grid)
        labels['axillary_node'] &= ~labels['fatty_hilum']
        if index in KEYFRAMES:
            evidence[str(index)] = {**morphology, 'imagingDepthMm': frame['imagingDepthMm'],
                                    'samplePitchMm': round(float(depth[1] - depth[0]), 8),
                                    **{name: measure_landmark(labels[name], gray) for name in parts}}
        Image.fromarray(gray).save(media / f'scan-{index:02}.webp', quality=91)
        Image.fromarray(overlay(gray, labels, palette)).save(media / f'section-{index:02}.webp', quality=88)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        **anatomy.receipt,
        'case': CASE, 'probeType': 'linear', 'fieldShape': 'rectangle', 'voxelMm': VOXEL_MM,
        'fieldWidthMm': track['fieldWidthMm'], 'sectorDepthMm': track['sectorDepthMm'],
        'imagingDepthMmRange': [PORTRAIT_DEPTH_MM, track['sectorDepthMm']], 'exterior': track['exterior'],
        'surfaceMaxOuterContactErrorMm': round(max_contact, 4),
        'contactFit': {'samplesPerFrame': offsets.size // len(frames),
                       'nativeMinSignedFirstHitMm': round(float(offsets.min()), 4),
                       'nativeMaxSignedFirstHitMm': round(float(offsets.max()), 4),
                       'seatedMaxAbsFirstHitMm': round(max_contact, 4)},
        'approachClearance': approach,
        'angleOriginFrame': 0, 'framesChecked': len(frames),
        'poseRecipeSha256': pose_recipe_sha256(track['id']), 'sectionPaletteSha256': section_palette_sha256(track),
        'renderRecipeSha256': render_recipe_sha256(track['id']),
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *parts]))
    print(f'Axilla: {len(frames)} poses checked, seated footprint residual {max_contact:.3f} mm')


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
