"""Sample an illustrative HRA breast volume with a linear-array probe."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial.transform import Rotation, Slerp

from build_abdomen import axes, measure_landmark, overlay, section_palette, section_palette_sha256
from build_study import fine_scatter
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, RASTER_SIZE, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
CASE = 'hra-breast-right'
POSES = (
    ((82, 307), (.19, 1, .32), (1, 0, -1.12)),
    ((79.257, 300.394), (.1078, 1, .3228), (1, 0, -1.2488)),
    ((62.2353, 263.0027), (-.05451787, .99803226, -.03097420), (.99840205, .05494759, .01319522)),
)


def read_breast_tracks():
    return [json.loads((HERE / 'breast-track.json').read_text())]


def pose_recipe_sha256(sweep_id):
    if sweep_id != 'breast':
        raise ValueError(f'Unknown breast sweep: {sweep_id}')
    return sha256(json.dumps({'windowPoses': POSES, 'keyframes': (0, *KEYFRAMES),
                              'angleOriginFrame': 0}, separators=(',', ':')).encode())


def grid_axes(track):
    """Use isotropic pixels and reserve the excess raster area as black surround."""
    width, height = RASTER_SIZE
    pitch = max(track['fieldWidthMm'] / (width - 14), track['sectorDepthMm'] / (height - 14))
    lateral = (np.arange(width) + .5 - width / 2) * pitch
    depth = (np.arange(height) + .5 - 7) * pitch
    x, y = np.meshgrid(lateral, depth)
    field = (np.abs(x) <= track['fieldWidthMm'] / 2) & (y >= 0) & (y <= track['sectorDepthMm'])
    return lateral, depth, field


def slice_segments(mesh, contact, width, beam):
    """Intersect mesh triangles with the image plane in millimetre coordinates."""
    vertices, faces = mesh
    normal = np.cross(width, beam)
    local = np.einsum('ij,kj->ik', (vertices - contact) * VOXEL_MM, np.stack((width, beam, normal)))
    signed = local[:, 2] - 1e-7
    z = signed[faces]
    crosses = (z.min(1) <= 0) & (z.max(1) > 0)
    faces = faces[crosses]
    z = z[crosses]
    end = np.roll(z, -1, axis=1)
    crossing_edge = (z > 0) != (end > 0)
    start = faces[crossing_edge]
    stop = np.roll(faces, -1, axis=1)[crossing_edge]
    fraction = signed[start] / (signed[start] - signed[stop])
    xy = local[start, :2] + fraction[:, None] * (local[stop, :2] - local[start, :2])
    return xy.reshape(-1, 2, 2)


def bounded_fill(segments, lateral, depth):
    """Fill paired crossings along each line, excluding unidentified tails."""
    marks = np.zeros((len(depth) + 1, len(lateral)), dtype=np.uint16)
    if not len(segments):
        return marks[:-1].astype(bool)
    # Treat the left endpoint as closed and the right as open, so a shared
    # vertex at a raster column contributes exactly one crossing per boundary.
    start, end = segments.transpose(1, 0, 2)
    forward = start[:, 0] < end[:, 0]
    low = np.where(forward[:, None], start, end)
    high = np.where(forward[:, None], end, start)
    ranges = np.searchsorted(lateral, np.column_stack((low[:, 0], high[:, 0])))
    lengths = ranges[:, 1] - ranges[:, 0]
    valid = lengths > 0
    low, high, ranges, lengths = low[valid], high[valid], ranges[valid], lengths[valid]
    indices = np.repeat(np.arange(len(ranges)), lengths)
    col = np.arange(indices.size) - np.repeat(np.cumsum(lengths) - lengths - ranges[:, 0], lengths)
    slope = (high[:, 1] - low[:, 1]) / (high[:, 0] - low[:, 0])
    hits = low[indices, 1] + (lateral[col] - low[indices, 0]) * slope[indices]
    row = np.searchsorted(depth, hits)
    np.add.at(marks, (row, col), 1)
    odd = np.bincount(col, minlength=len(lateral)) % 2 != 0
    # Clip below the final crossing in open columns rather than invent tissue.
    last = np.zeros(len(lateral), dtype=int)
    np.maximum.at(last, col, row)
    mask = np.cumsum(marks[:-1], axis=0) % 2 != 0
    mask[:, odd] &= np.arange(len(depth))[:, None] < last[odd]
    return mask


def section_mask(mesh, contact, width, beam, lateral, depth):
    """Keep only the section interior supported by both raster directions.

    The sculpted atlas includes open components. Single-axis parity can turn a
    missing boundary into a long false streak. The same triangle segments must
    bound a region in both independent directions before it is filled.
    """
    through_depth, across_image = orthogonal_sections(mesh, contact, width, beam, lateral, depth)
    return through_depth & across_image


def orthogonal_sections(mesh, contact, width, beam, lateral, depth):
    segments = slice_segments(mesh, contact, width, beam)
    return (bounded_fill(segments, lateral, depth),
            bounded_fill(segments[..., ::-1], depth, lateral).T)


def first_profile(mesh, frames, width_mm):
    contacts, beams, widths = (np.array([frame[key] for frame in frames]) for key in ('contact', 'beam', 'width'))
    lateral = np.linspace(-width_mm / 2, width_mm / 2, 17)
    rays = contacts[:, None] + widths[:, None] * lateral[None, :, None] / VOXEL_MM
    offsets = outer_contact_offsets(*mesh, rays.reshape(-1, 3), np.repeat(beams, len(lateral), axis=0))
    offsets = offsets.reshape(-1, len(lateral))
    return offsets, {'lateralMm': lateral.tolist(),
                     'minSignedFirstHitMm': offsets.min(0).round(3).tolist(),
                     'maxSignedFirstHitMm': offsets.max(0).round(3).tolist()}


def frames_from_windows(anatomy):
    """Slide from the upper outer breast toward an off-nipple radial window."""
    stations = (0, *KEYFRAMES)
    centers = np.array([pose[0] for pose in POSES])
    rotations = Rotation.from_matrix([axes(*pose[1:]) for pose in POSES])
    path = Slerp(stations, rotations)
    for i in range(FRAME_COUNT):
        site = np.array([np.interp(i, stations, centers[:, j]) for j in range(2)])
        rotation = path(i)
        width, _, beam = rotation.as_matrix().T
        contact = np.asarray(anatomy.contact(*site))
        # Contact is measured along the actual incoming ray, rather than the
        # center of the containing mesh. Pose interpolation uses the same frame.
        adjust = outer_contact_offsets(*anatomy.meshes['torso'], [contact], [beam])[0]
        if abs(adjust) > 1:
            raise ValueError(f'Probe origin is {adjust:+.2f} mm from the outer surface at frame {i}')
        contact += beam * adjust / VOXEL_MM
        yield {'contact': contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist(),
               'degrees': round(np.rad2deg((rotation * rotations[0].inv()).magnitude()), 1)}


def sampled_section(anatomy, frame, grid):
    lateral, depth, field = grid
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    xyz = (contact[:, None, None] + (width[:, None, None] * lateral[None, None, :]
           + beam[:, None, None] * depth[None, :, None]) / VOXEL_MM)
    labels = {name: section_mask(mesh, contact, width, beam, lateral, depth) & field
              for name, mesh in anatomy.meshes.items()
              if name != 'torso'}
    # Keep one anatomical ownership per pixel where sculpted source tissues touch.
    gland = labels['mammary_lobes'] | labels['lactiferous_ducts']
    labels['breast_fat'] &= ~gland
    labels['deep_fat'] &= ~(gland | labels['breast_fat'])
    return labels, xyz


def brightness(labels, xyz, grid, skin, inside, stromal_support):
    _, depth, field = grid
    fat = nd.gaussian_filter(labels['breast_fat'].astype('f'), .8)
    glands = nd.gaussian_filter(labels['mammary_lobes'].astype('f'), .7)
    ducts = nd.gaussian_filter(labels['lactiferous_ducts'].astype('f'), .8)
    pectoral = nd.gaussian_filter(labels['pectoralis'].astype('f'), .7)
    wall = nd.gaussian_filter(labels['chest_wall'].astype('f'), .7)
    retro = nd.gaussian_filter(labels['retromammary_fat'].astype('f'), .7)
    deep_fat = nd.gaussian_filter(labels['deep_fat'].astype('f'), .8)
    ligament = nd.gaussian_filter(labels['suspensory_ligaments'].astype('f'), .6)
    nipple = labels.get('nipple', np.zeros_like(field))

    # Use stationary fields so texture follows the shared geometry while moving.
    noise = fine_scatter(xyz)
    broad = fine_scatter(xyz * .24 + np.array([.27, .44, .06])[:, None, None])
    fine = nd.gaussian_filter(noise, (.35, .8))
    tissue = np.maximum.reduce([fat, deep_fat, glands, pectoral, wall, retro, ducts, nipple])
    # Integrate a shallow elevational neighborhood in the real geometry, then
    # soften the echoes over nearby mixed tissue. The overlay keeps the center cut.
    stroma = nd.gaussian_filter(stromal_support, (9.2, 13.0))
    stromal_distance = nd.distance_transform_edt(stromal_support < .2, sampling=(depth[1] - depth[0],) * 2)
    stromal_mix = np.maximum(stroma, .57 * np.exp(-(stromal_distance / 4.1) ** 1.6))
    local_stroma = np.clip(stromal_mix * (1.12 + .36 * broad + .15 * fine), 0, 1) * inside
    # The source structures do not tile the whole tissue volume. Use a
    # schematic acoustic background only inside the actual exterior envelope.
    b = (40 + 14*broad + 64*fine) * np.clip(inside - tissue, 0, 1)
    b += (43 + 16*broad + 67*fine) * (fat + .93 * deep_fat)
    b += (44 + 15*broad + 63*fine) * glands
    b += (30 + 10*broad + 50*fine) * retro
    b += (48 + 11*broad + 44*fine) * pectoral
    b += (37 + 9*broad + 39*fine) * wall
    b += (34 + 32*fine) * nipple
    # The modeled stromal return is continuous through the lobe neighborhood.
    # Mesh-only labels are kept exact and do not grow to match this acoustic cue.
    b += (78 + 27*fine + 29*broad) * local_stroma + 36 * ligament
    b = b * (1 - .94 * ducts) + ducts * (5 + 7*fine)
    interfaces = (np.abs(np.gradient(stroma + retro, axis=0)) * 59
                  + np.abs(np.gradient(pectoral, axis=0)) * 145
                  + np.abs(np.gradient(ducts, axis=0)) * 27
                  + np.abs(np.gradient(wall, axis=0)) * 65)
    # Muscular striation is an illustrative 3D texture on the authored wall.
    striation = np.clip(np.sin((.64 * xyz[1] + .069 * xyz[0] + .055 * xyz[2]) * 2.4) + .18*broad, 0, 1)
    b += pectoral * striation * 13
    shadow = np.exp(-nd.gaussian_filter(np.cumsum(nipple, axis=0).astype('f'), (1.5, 1.3)) * .016)
    gray = (b + interfaces + 144 * nd.gaussian_filter(skin.astype('f'), (.55, .85))) * shadow * np.exp(-np.maximum(depth, 0)[:, None] / 280)
    return np.where(field, np.clip(gray, 0, 240), 0).astype('u1')


def exposed_skin(mesh, contact, width, beam, lateral, depth, field):
    """Return the superficial skin echo and the enclosing soft-tissue volume."""
    edges = slice_segments(mesh, contact, width, beam)
    if not len(edges):
        raise ValueError('The specified plane misses the breast exterior')
    first = np.full(len(lateral), np.inf)
    last = np.full(len(lateral), -np.inf)
    for a, b in edges:
        if abs(a[0] - b[0]) < 1e-6:
            continue
        lo, hi = np.searchsorted(lateral, sorted((a[0], b[0])))
        x = lateral[lo:hi]
        y = a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
        first[lo:hi] = np.minimum(first[lo:hi], y)
        last[lo:hi] = np.maximum(last[lo:hi], y)
    bottom = depth[:, None] - first
    return ((bottom >= -.18) & (bottom < 1.05) & field,
            (bottom >= 0) & (depth[:, None] < last) & field)


def radial_evidence(labels, gray, lateral, depth):
    nipple = labels['nipple']
    if not nipple.any():
        raise ValueError('Radial section misses the modeled nipple')
    distance = nd.distance_transform_edt(~nipple, sampling=(depth[1]-depth[0], lateral[1]-lateral[0]))
    components, _ = nd.label(labels['lactiferous_ducts'])
    counts = np.bincount(components.ravel())
    counts[0] = 0
    candidates = []
    for label in np.flatnonzero(counts >= 40):
        main = components == label
        clearance = distance[main].min()
        if clearance > 9:
            continue
        rows, cols = np.nonzero(main)
        coordinates = np.column_stack((lateral[cols], depth[rows]))
        extent, directions = np.linalg.eigh(np.cov(coordinates.T))
        span_mm = float(np.ptp(np.einsum('ij,j->i', coordinates, directions[:, -1])))
        elongation = float(np.sqrt(extent[1] / max(extent[0], 1e-4)))
        if elongation >= 2.2 and span_mm >= 20:
            candidates.append((span_mm, label, elongation, clearance))
    if not candidates:
        raise ValueError('Radial section misses an elongated modeled duct near the nipple')
    span, label, elongation, clearance = max(candidates)
    return {**measure_landmark(components == label, gray), 'elongation': round(elongation, 2),
            'projectedSpanMm': round(span, 2),
            'clearanceToNippleMm': round(float(clearance), 2)}


def layer_evidence(labels, skin, gray, depth):
    front_to_back = ('breast_fat', 'mammary_lobes', 'retromammary_fat', 'pectoralis', 'chest_wall')
    area = {name: measure_landmark(labels[name], gray)['largestSectionPixels'] for name in front_to_back}
    if not skin.any() or any(count < minimum for count, minimum in zip(area.values(), (500, 160, 140, 150, 30), strict=True)):
        raise ValueError(f'Peripheral section misses an intended layer: {area}')
    # Every ray need not show all tissues. Require a substantial group in which
    # the labeled layers occur in the demonstrated order.
    rows = np.arange(len(depth))[:, None]
    end = np.full(labels['breast_fat'].shape[1], -1)
    ordered = np.any(skin, axis=0)
    for name in front_to_back[:-1]:
        intervals = labels[name] & (rows > end)
        ordered &= np.any(intervals, axis=0)
        end = np.where(intervals, rows, len(depth)).min(axis=0)
    runs, _ = nd.label(ordered)
    counts = np.bincount(runs)
    counts[0] = 0
    ordered_width = counts.max() * (depth[1]-depth[0])
    if ordered_width < 8:
        raise ValueError(f'Peripheral section retains only {ordered_width:.1f} mm with contiguous ordered layers')
    return {'orderedLayerColumns': int(ordered.sum()), 'largestOrderedBandMm': round(float(ordered_width), 2),
            'orderedLayerWidthMm': round(float(ordered.sum() * (depth[1]-depth[0])), 2),
            'skinSectionPixels': int(skin.sum()), 'layerSectionPixels': area}


def build(track, output, anatomy):
    grid = grid_axes(track)
    lateral, depth, field = grid
    frames = list(frames_from_windows(anatomy))
    offsets, profile = first_profile(anatomy.meshes['torso'], frames, track['fieldWidthMm'])
    max_contact = float(np.max(np.abs(offsets[:, offsets.shape[1] // 2])))
    if max_contact > .5 or offsets.min() < -4:
        raise ValueError(f'Breast probe fit exceeds the limit (central {max_contact:.2f} mm; '
                         f'max edge overlap {-offsets.min():.2f} mm)')
    parts = [part['id'] for part in track['parts']]
    palette = section_palette(track)
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    for name in ['torso', *parts]:
        (scenes / f'{name}.mesh').write_bytes(mesh_bytes(*anatomy.meshes[name]))
    evidence = {}
    for i, frame in enumerate(frames):
        labels, xyz = sampled_section(anatomy, frame, grid)
        c, w, b = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
        skin, inside = exposed_skin(anatomy.meshes['torso'], c, w, b, lateral, depth, field)
        normal = np.cross(w, b)
        support = labels['mammary_lobes'].astype('f') * .48
        for millimetres in (-2.2, 2.2):
            neighbor = c + normal * millimetres / VOXEL_MM
            support += .26 * section_mask(anatomy.meshes['mammary_lobes'], neighbor, w, b, lateral, depth) * field
        gray = brightness(labels, xyz, grid, skin, inside, support)
        if not skin.any() or labels['breast_fat'].sum() < 500:
            raise ValueError(f'Frame {i} misses the modeled breast')
        if i in KEYFRAMES:
            receipt = {name: measure_landmark(labels[name], gray) for name in parts}
            receipt['sourceLigamentPixels'] = int(labels['suspensory_ligaments'].sum())
            receipt['backgroundContinuationPixels'] = int(np.count_nonzero(
                inside & ~np.logical_or.reduce([labels[name] for name in parts])))
            if i == KEYFRAMES[0]:
                receipt.update(layer_evidence(labels, skin, gray, depth))
            else:
                along, across = orthogonal_sections(anatomy.meshes['lactiferous_ducts'], c, w, b, lateral, depth)
                overlap = int(np.count_nonzero(along & across & field))
                union = int(np.count_nonzero((along | across) & field))
                agreement = overlap / union if union else 0
                if agreement < .98:
                    raise ValueError(f'Radial duct cross-section fill agreement is only {agreement:.1%}')
                receipt['modeledDuctAlongAxis'] = {
                    **radial_evidence(labels, gray, lateral, depth),
                    'orthogonalFillAgreementIoU': round(agreement, 4),
                }
            evidence[str(i)] = receipt
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=91)
        Image.fromarray(overlay(gray, labels, palette)).save(media / f'section-{i:02}.webp', quality=88)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        **anatomy.receipt,
        'case': CASE, 'coordinateFrame': 'HRA native glTF transformed to 1.5 mm RAS voxels',
        'probeType': 'linear', 'fieldShape': 'rectangle', 'voxelMm': VOXEL_MM,
        'fieldWidthMm': track['fieldWidthMm'], 'sectorDepthMm': track['sectorDepthMm'],
        'samplePitchMm': round(float(depth[1]-depth[0]), 8), 'exterior': track['exterior'],
        'surfaceMaxOuterContactErrorMm': round(max_contact, 3),
        'apertureOffsetsMm': profile, 'angleOriginFrame': 0,
        'poseRecipeSha256': pose_recipe_sha256(track['id']), 'sectionPaletteSha256': section_palette_sha256(track),
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *parts]))
    print(f'Breast: 49 poses checked, first incoming contact residual {max_contact:.3f} mm', flush=True)


def main():
    from breast_anatomy import FEMALE_SKIN, load_anatomy

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    parser.add_argument('--skin', type=Path, default=FEMALE_SKIN, help='Pinned female HRA skin GLB')
    args = parser.parse_args()
    if (args.sweeps_dir / 'breast').exists():
        parser.error('Choose a fresh destination for breast.')
    [track] = read_breast_tracks()
    anatomy = load_anatomy(args.skin)
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage:
        output = Path(stage) / 'breast'
        output.mkdir()
        build(track, output, anatomy)
        output.rename(args.sweeps_dir / 'breast')


if __name__ == '__main__':
    main()
