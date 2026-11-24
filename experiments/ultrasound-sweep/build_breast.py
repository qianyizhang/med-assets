"""Sample an illustrative HRA breast volume with a linear-array probe."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial.transform import Rotation, Slerp
from skimage.draw import polygon

from build_abdomen import axes, measure_landmark, overlay, section_palette, section_palette_sha256
from build_study import fine_scatter
from breast_compression import SETTLE_DEPTH_MM, compress_plates
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, RASTER_SIZE, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
CASE = 'hra-breast-right'
# Four adjoining oblique lines run medial–lateral and progress inferiorly.
SURVEY_WINDOWS = (
    (0, (52, 308), (-.24, 1, .45)),
    (5, (72, 314), (.03, 1, .55)),
    (10, (92, 320), (.43, 1, .55)),
    (12, (79.257, 300.394), (.1078, 1, .3228)),
    (16, (68, 298), (-.11, 1, .49)),
    (22, (52, 292), (-.24, 1, .40)),
    (25, (52, 280), (-.25, 1, .48)),
    (30, (72, 285), (.02, 1, .52)),
    (35, (92, 291), (.50, 1, .46)),
    (37, (92, 274), (.46, 1, .24)),
    (42, (72, 269), (.03, 1, .22)),
    (48, (52, 264), (-.21, 1, .10)),
)
SURVEY_MARKER = (1, 0, -1.2488)
SURVEY_PASSES = (
    {'label': 'Superior outward pass', 'firstFrame': 0, 'lastFrame': 10},
    {'label': 'Upper inward pass', 'firstFrame': 11, 'lastFrame': 22},
    {'label': 'Mid-breast outward pass', 'firstFrame': 25, 'lastFrame': 35},
    {'label': 'Lower inward pass', 'firstFrame': 37, 'lastFrame': 48},
)
ACCEPTED_RADIAL = ((62.2353, 263.0027), (-.05451787, .99803226, -.03097420), (.99840205, .05494759, .01319522))
SLIDE_MM = (0, 11, 22.15)
SLIDE_DIRECTION = (0.9952, -0.09786)  # Medial toward the native nipple center in RAS XZ.
BASELINE_YAW_CHANGE = .085  # Align the zero-tilt face to the curvature along the slide.
ROTATE_DEG = (0, 20.5, 41, 61.5, 82)
HEEL_TOE_DEG = (-4, 0, 8)
SNAKE = ((0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0), (2, 0), (2, 1), (2, 2))
RETURN = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (1, 1), (0, 1))


def steering_recipe():
    """Keep all 45 controls independent, with four interpolated transit frames."""
    axes = [
        {'label': 'Slide', 'unit': 'mm', 'values': SLIDE_MM},
        {'label': 'Rotate', 'unit': '°', 'values': ROTATE_DEG},
        {'label': 'Heel–toe', 'unit': '°', 'values': HEEL_TOE_DEG},
    ]
    motions, cells = [], []
    for rotation in reversed(range(len(ROTATE_DEG))):
        path = RETURN if rotation == 0 else (SNAKE if rotation % 2 == 0 else SNAKE[::-1])
        for i, (slide, rock) in enumerate(path):
            values = (SLIDE_MM[slide], ROTATE_DEG[rotation], HEEL_TOE_DEG[rock])
            if rotation == 4 and i in (3, 6, 7, 8):
                motions.append(tuple((a + b) / 2 for a, b in zip(motions[-1], values, strict=True)))
            cells.append({'frame': len(motions), 'indices': [slide, rotation, rock]})
            motions.append(values)
    if len(motions) != FRAME_COUNT:
        raise ValueError('Subareolar steering must cover the 49-frame tour')
    return {'axes': axes, 'cells': cells}, motions


def read_breast_tracks():
    recipe = json.loads((HERE / 'breast-track.json').read_text())
    common = recipe['common']
    tracks = [{**common, **item, 'parts': common['parts'] + item.get('extraParts', [])}
              for item in recipe['sweeps']]
    for track in tracks:
        track.pop('extraParts', None)
        if track['id'] == 'breast-subareolar':
            track['steering'], _ = steering_recipe()
        else:
            track['showRoute'] = True
            track['coveragePasses'] = SURVEY_PASSES
            track['phases'] = [{'frame': item['firstFrame'], 'label': item['label']} for item in SURVEY_PASSES]
    return tracks


def pose_recipe_sha256(sweep_id):
    if sweep_id == 'breast':
        recipe = {'windows': SURVEY_WINDOWS, 'marker': SURVEY_MARKER, 'passes': SURVEY_PASSES}
    elif sweep_id == 'breast-subareolar':
        steering, motions = steering_recipe()
        recipe = {'anchor': ACCEPTED_RADIAL, 'slideDirectionXZ': SLIDE_DIRECTION,
                  'steering': steering, 'positions': motions, 'baselineYawChange': BASELINE_YAW_CHANGE,
                  'surface': 'mammary skin and gel standoff'}
    else:
        raise ValueError(f'Unknown breast sweep: {sweep_id}')
    return sha256(json.dumps({**recipe, 'angleOriginFrame': 0}, separators=(',', ':')).encode())


def render_recipe_sha256(sweep_id):
    """Bind delivery to the source anatomy and route-specific render recipe."""
    route = {'breast': 'breast_layers.py', 'breast-subareolar': 'breast_compression.py'}
    names = ('build_breast.py', 'breast_anatomy.py', route[sweep_id])
    recipe = {name: sha256((HERE / name).read_bytes()) for name in names}
    return sha256(json.dumps(recipe, sort_keys=True, separators=(',', ':')).encode())


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


def frame_at(anatomy, site, width, beam):
    contact = anatomy.contact(*site)
    adjust = outer_contact_offsets(*anatomy.meshes['torso'], [contact], [beam])[0]
    if abs(adjust) > 1:
        raise ValueError(f'Probe origin is {adjust:+.2f} mm from the outer surface at site {site}')
    contact += beam * adjust / VOXEL_MM
    return {'contact': contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist()}


def seat_survey_face(anatomy, frame, width_mm):
    """Balance the rigid array on the curved atlas without changing its section plane."""
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    section_normal = np.cross(width, beam)
    samples = np.linspace(-width_mm / 2, width_mm / 2, 17)

    def fit_score(w, b):
        origins = contact + samples[:, None] * w / VOXEL_MM
        offsets = outer_contact_offsets(*anatomy.meshes['torso'], origins, np.broadcast_to(b, origins.shape))
        return max(0, -offsets.min() - 2) * 10 + max(0, offsets.max() - 14)

    initial = fit_score(width, beam)
    if initial == 0:
        return frame
    best = (initial, width, beam)
    for angle in (-10, -6, -3, 3, 6, 10):
        w, b = Rotation.from_rotvec(section_normal * np.deg2rad(angle)).apply([width, beam])
        score = fit_score(w, b) + abs(angle) * .12
        if score < best[0]:
            best = (score, w, b)
    _, width, beam = best
    return frame_at(anatomy, contact[[0, 2]], width, beam)


def nipple_exterior(anatomy):
    from breast_anatomy import concatenate

    return concatenate([anatomy.meshes[name] for name in ('torso', 'areola', 'nipple')])


def seat_nipple_face(exterior, frame, width_mm):
    """Allow gel to couple a rigid array to the projecting native nipple."""
    c, w, b = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    origins = c + np.linspace(-width_mm / 2, width_mm / 2, 89)[:, None] * w / VOXEL_MM
    offsets = outer_contact_offsets(*exterior, origins, np.broadcast_to(b, origins.shape))
    lift = max(0, .65 - offsets.min())
    return {**frame, 'contact': (c - b * lift / VOXEL_MM).tolist(), 'gelLiftMm': round(float(lift), 4)}


def frames_from_windows(anatomy, sweep_id='breast', field_width_mm=52):
    if sweep_id == 'breast':
        stations, centers, outward = zip(*SURVEY_WINDOWS, strict=True)
        centers = np.asarray(centers)
        path = Slerp(stations, Rotation.from_matrix([axes(axis, SURVEY_MARKER) for axis in outward]))
        poses = [(np.array([np.interp(i, stations, coordinate) for coordinate in centers.T]), path(i))
                 for i in range(FRAME_COUNT)]
    else:
        site, outward, marker = ACCEPTED_RADIAL
        _, motions = steering_recipe()
        poses = []
        for slide, rotate, heel in motions:
            neutral = np.asarray(outward) + [BASELINE_YAW_CHANGE * slide / SLIDE_MM[-1], 0, 0]
            base_width, _, base_beam = axes(neutral, marker).T
            width = Rotation.from_rotvec(-base_beam * np.deg2rad(rotate)).apply(base_width)
            rock = Rotation.from_rotvec(np.cross(width, base_beam) * np.deg2rad(heel))
            width, beam = rock.apply([width, base_beam])
            basis = np.column_stack((width, np.cross(beam, width), beam))
            poses.append((np.asarray(site) + np.asarray(SLIDE_DIRECTION) * slide / VOXEL_MM,
                          Rotation.from_matrix(basis)))
    frames = []
    exterior = nipple_exterior(anatomy) if sweep_id == 'breast-subareolar' else None
    for site, rotation in poses:
        width, _, beam = rotation.as_matrix().T
        frame = frame_at(anatomy, site, width, beam)
        if sweep_id == 'breast':
            frame = seat_survey_face(anatomy, frame, field_width_mm)
        if exterior is not None:
            frame = seat_nipple_face(exterior, frame, field_width_mm)
        frames.append(frame)
    bases = []
    for frame in frames:
        w, b = (np.asarray(frame[key]) for key in ('width', 'beam'))
        bases.append(np.column_stack((w, np.cross(b, w), b)))
    orientations = Rotation.from_matrix(bases)
    angles = np.rad2deg((orientations * orientations[0].inv()).magnitude())
    for frame, angle in zip(frames, angles, strict=True):
        yield {**frame, 'degrees': round(float(angle), 1)}


def sampled_section(anatomy, frame, grid):
    lateral, depth, field = grid
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    xyz = (contact[:, None, None] + (width[:, None, None] * lateral[None, None, :]
           + beam[:, None, None] * depth[None, :, None]) / VOXEL_MM)
    labels = {name: section_mask(mesh, contact, width, beam, lateral, depth) & field
              for name, mesh in anatomy.meshes.items()
              if name != 'torso'}
    # Keep one anatomical ownership per pixel where sculpted source tissues touch.
    zone = labels.get('fibroglandular_zone')
    if zone is not None:
        zone &= ~labels['mammary_lobes']
    gland = labels['mammary_lobes'] | labels['lactiferous_ducts']
    if zone is not None:
        gland |= zone
    labels['breast_fat'] &= ~gland
    labels['deep_fat'] &= ~(gland | labels['breast_fat'])
    return labels, xyz


def brightness(labels, xyz, grid, skin, inside, stromal_support):
    _, depth, field = grid
    fat = nd.gaussian_filter(labels['breast_fat'].astype('f'), .8)
    glands = nd.gaussian_filter(labels['mammary_lobes'].astype('f'), .7)
    zone = nd.gaussian_filter(labels.get('fibroglandular_zone', np.zeros_like(field)).astype('f'), (2.25, 3.0))
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
    tissue = np.maximum.reduce([fat, deep_fat, glands, zone, pectoral, wall, retro, ducts, nipple])
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
    b += (66 + 20*broad + 71*fine) * zone
    b += (30 + 10*broad + 50*fine) * retro
    b += (48 + 11*broad + 44*fine) * pectoral
    b += (37 + 9*broad + 39*fine) * wall
    b += (34 + 32*fine) * nipple
    # The modeled stromal return is continuous through the lobe neighborhood.
    # Mesh-only labels are kept exact and do not grow to match this acoustic cue.
    b += (78 + 27*fine + 29*broad) * local_stroma + 36 * ligament
    b = b * (1 - .94 * ducts) + ducts * (5 + 7*fine)
    interfaces = (np.abs(np.gradient(stroma + zone * .4 + retro, axis=0)) * 59
                  + np.abs(np.gradient(pectoral, axis=0)) * 145
                  + np.abs(np.gradient(ducts, axis=0)) * 27
                  + np.abs(np.gradient(wall, axis=0)) * 65)
    # Muscular striation is an illustrative 3D texture on the authored wall.
    striation = np.clip(np.sin((.64 * xyz[1] + .069 * xyz[0] + .055 * xyz[2]) * 2.4) + .18*broad, 0, 1)
    if 'fibroglandular_zone' in labels:
        x, y, z = xyz
        # These stationary acoustic patterns model thin septal reflections and
        # fascia-parallel muscle texture, without adding structural labels.
        perturbation = fine_scatter(xyz * .047 + np.array([.26, .72, .38])[:, None, None])
        septal_phase = .69 * y + .068 * x - .112 * z + 2.1 * perturbation
        septa = np.exp(-(np.sin(septal_phase) / .22) ** 2)
        coherence = .32 + .68 * np.clip(.55 + .85 * broad, 0, 1)
        b += np.maximum(fat, deep_fat) * septa * coherence * 24
        fascia = -10.8 - .0011 * x**2 - .0006 * (z - 256)**2
        bundle = np.clip(np.sin((y - fascia) * 3.3 + .4 * perturbation) + .27, 0, 1)
        b += pectoral * bundle * (24 + 10 * broad)
    else:
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


def layer_evidence(labels, skin, gray, depth, *, require_order=True):
    layered = {**labels, 'fibroglandular_zone': labels['mammary_lobes'] | labels['fibroglandular_zone']}
    front_to_back = ('breast_fat', 'fibroglandular_zone', 'retromammary_fat', 'pectoralis', 'chest_wall')
    area = {name: measure_landmark(layered[name], gray)['largestSectionPixels'] for name in front_to_back}
    if require_order and (not skin.any() or any(count < minimum for count, minimum in
                          zip(list(area.values())[:-1], (500, 160, 140, 150), strict=True))):
        raise ValueError(f'Peripheral section misses an intended layer: {area}')
    # Every ray need not show all tissues. Require a substantial group in which
    # the labeled layers occur in the demonstrated order.
    rows = np.arange(len(depth))[:, None]
    end = np.full(labels['breast_fat'].shape[1], -1)
    ordered = np.any(skin, axis=0)
    for name in front_to_back[:-1]:
        intervals = layered[name] & (rows > end)
        ordered &= np.any(intervals, axis=0)
        end = np.where(intervals, rows, len(depth)).min(axis=0)
    runs, _ = nd.label(ordered)
    counts = np.bincount(runs)
    counts[0] = 0
    ordered_width = counts.max() * (depth[1]-depth[0])
    if require_order and ordered_width < 8:
        raise ValueError(f'Peripheral section retains only {ordered_width:.1f} mm with contiguous ordered layers')
    return {'orderedLayerColumns': int(ordered.sum()), 'largestOrderedBandMm': round(float(ordered_width), 2),
            'orderedLayerWidthMm': round(float(ordered.sum() * (depth[1]-depth[0])), 2),
            'skinSectionPixels': int(skin.sum()), 'layerSectionPixels': area}


def coverage_evidence(anatomy, frames, offsets, width_mm, frame_layers):
    # Project the physical aperture's skin-entry ribbon. This does not estimate
    # skin pressure, diagnostic coverage, or tissue hidden behind each plane.
    contacts, widths, beams = (np.array([frame[key] for frame in frames]) for key in ('contact', 'width', 'beam'))
    along = np.cross(widths, beams)
    lateral = np.linspace(-width_mm / 2, width_mm / 2, offsets.shape[1])
    surface = contacts[:, None, :] * VOXEL_MM + lateral[None, :, None] * widths[:, None, :]
    surface += offsets[:, :, None] * beams[:, None, :]
    xz = surface[..., [0, 2]]
    vertices, faces = anatomy.meshes['breast_fat']
    right = (vertices[faces, 0] > 0).all(axis=1)
    native = vertices[faces[right]][..., [0, 2]] * VOXEL_MM
    margin, pitch = 8, .75
    origin = np.minimum(xz.min(axis=(0, 1)), native.min(axis=(0, 1))) - margin
    limits = np.maximum(xz.max(axis=(0, 1)), native.max(axis=(0, 1))) + margin
    shape = tuple((np.ceil((limits - origin) / pitch) + 1).astype(int))
    footprint = np.zeros(shape, dtype=bool)
    projected = (native - origin) / pitch
    valid = (np.ceil(projected.min(1)) <= np.floor(projected.max(1))).all(1)
    for triangle in projected[valid]:
        i, j = polygon(triangle[:, 0], triangle[:, 1], shape)
        footprint[i, j] = True
    bands, passes = [], []
    for description in SURVEY_PASSES:
        first, last = (description[key] for key in ('firstFrame', 'lastFrame'))
        ribbon = np.zeros(shape, dtype=bool)
        for i in range(first, last + 1):
            elevational = along[i, [0, 2]] * 6.5
            for a, b in zip(xz[i, :-1], xz[i, 1:], strict=True):
                points = (np.stack((a - elevational, b - elevational, b + elevational, a + elevational)) - origin) / pitch
                rr, cc = polygon(points[:, 0], points[:, 1], ribbon.shape)
                ribbon[rr, cc] = True
        bands.append(ribbon)
        path = contacts[first:last+1]
        rich = max(range(first, last + 1), key=lambda i: frame_layers[i]['largestOrderedBandMm'])
        passes.append({**description, 'strongestLayerFrame': rich,
                       'largestOrderedBandMm': frame_layers[rich]['largestOrderedBandMm'],
                       'surfaceCenterlineMm': round(float(
            np.linalg.norm(np.diff(path, axis=0), axis=1).sum() * VOXEL_MM), 1),
            'centerLateralRangeMm': (np.array([path[:, 0].min(), path[:, 0].max()]) * VOXEL_MM).round(1).tolist(),
            'projectedApertureMm2': round(float(ribbon.sum() * pitch ** 2), 1)})
    occupancy = np.sum(bands, axis=0)
    overlap = int(np.count_nonzero(occupancy >= 2))
    union = int(np.count_nonzero(occupancy))
    adjacent = [round(float(np.count_nonzero(a & b) * pitch ** 2), 1) for a, b in zip(bands, bands[1:])]
    if any(area == 0 for area in adjacent):
        raise ValueError('Adjacent modeled peripheral passes must overlap in front projection')
    inside = (occupancy > 0) & footprint
    nipple = np.array(anatomy.receipt['nippleCentersVox']['right'])[[0, 2]] * VOXEL_MM
    x, z = np.indices(shape) * pitch + origin[:, None, None]
    portions = {}
    for label, mask in (
        ('upperMedial', (x < nipple[0]) & (z >= nipple[1])),
        ('upperLateral', (x >= nipple[0]) & (z >= nipple[1])),
        ('lowerMedial', (x < nipple[0]) & (z < nipple[1])),
        ('lowerLateral', (x >= nipple[0]) & (z < nipple[1])),
    ):
        area = int(np.count_nonzero(footprint & mask))
        if area:
            portions[label] = round(float(np.count_nonzero(inside & mask) / area), 3)
    return {'meaning': 'Front-on XZ projection of modeled beam entry, including a 13 mm physical aperture height. '
                       'Relative areas use the source right HRA fat silhouette and do not measure tissue or exam coverage.',
            'passes': passes, 'adjacentPassOverlapMm2': adjacent,
            'projectedUnionMm2': round(union * pitch ** 2, 1),
            'projectedOverlapMm2': round(overlap * pitch ** 2, 1),
            'projectedOverlapFraction': round(overlap / union, 3),
            'sourceProjectionObservedFraction': round(float(inside.sum() / footprint.sum()), 3),
            'sourceProjectionUnvisitedMm2': round(float((footprint & ~inside).sum() * pitch ** 2), 1),
            'observedFractionByRegion': portions}


def render_frame(anatomy, frame, grid):
    lateral, depth, field = grid
    labels, xyz = sampled_section(anatomy, frame, grid)
    c, w, b = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    exterior = nipple_exterior(anatomy) if 'gelLiftMm' in frame else anatomy.meshes['torso']
    skin, inside = exposed_skin(exterior, c, w, b, lateral, depth, field)
    normal = np.cross(w, b)
    support = labels['mammary_lobes'].astype('f') * .48
    for millimetres in (-2.2, 2.2):
        neighbor = c + normal * millimetres / VOXEL_MM
        support += .26 * section_mask(anatomy.meshes['mammary_lobes'], neighbor, w, b, lateral, depth) * field
    gray = brightness(labels, xyz, grid, skin, inside, support)
    return gray, labels, skin, inside


def build(track, output, anatomy):
    grid = grid_axes(track)
    lateral, depth, field = grid
    sweep_id = track['id']
    frames = list(frames_from_windows(anatomy, sweep_id, track['fieldWidthMm']))
    focused = sweep_id == 'breast-subareolar'
    exterior = nipple_exterior(anatomy) if focused else anatomy.meshes['torso']
    offsets, profile = first_profile(exterior, frames, track['fieldWidthMm'])
    if focused:
        if offsets.min() < -.3 or offsets.min(axis=1).max() > 2:
            raise ValueError('Nipple gel footprint overlaps tissue or clears all contact rays')
        origin_mesh = anatomy.meshes['torso']
        seated = [{**frame, 'contact': (np.asarray(frame['contact']) + np.asarray(frame['beam']) *
                   frame['gelLiftMm'] / VOXEL_MM).tolist()} for frame in frames]
        center_offsets, _ = first_profile(origin_mesh, seated, track['fieldWidthMm'])
    else:
        center_offsets = offsets
    max_contact = float(np.max(np.abs(center_offsets[:, center_offsets.shape[1] // 2])))
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
    evidence, frame_layers, pressure_names = {}, {}, []
    compression_mm = track.get('compressionMm')
    for i, frame in enumerate(frames):
        gray, labels, skin, inside = render_frame(anatomy, frame, grid)
        c, w, b = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
        if not skin.any() or labels['breast_fat'].sum() < 500:
            raise ValueError(f'Frame {i} misses the modeled breast')
        if sweep_id == 'breast':
            frame_layers[i] = layer_evidence(labels, skin, gray, depth, require_order=i in KEYFRAMES)
        if i in KEYFRAMES:
            receipt = {name: measure_landmark(labels[name], gray) for name in parts}
            receipt['sourceLigamentPixels'] = int(labels['suspensory_ligaments'].sum())
            receipt['backgroundContinuationPixels'] = int(np.count_nonzero(
                inside & ~np.logical_or.reduce([labels[name] for name in parts])))
            if sweep_id == 'breast':
                receipt.update(frame_layers[i])
            elif i == KEYFRAMES[0]:
                if np.count_nonzero(labels['nipple']) < 16 or np.count_nonzero(labels['areola']) < 95:
                    raise ValueError('Cross-duct stop misses the nipple and areola')
                rows, columns = np.nonzero(labels['nipple'] & inside)
                width_mm = (np.ptp(columns) + 1) * (lateral[1] - lateral[0])
                depth_mm = (np.ptp(rows) + 1) * (depth[1] - depth[0])
                if width_mm < 3 or depth_mm < 1.5:
                    raise ValueError(f'Across-nipple profile is only {width_mm:.2f} × {depth_mm:.2f} mm')
                receipt['acrossNipple'] = {'visibleWidthMm': round(width_mm, 2),
                                            'visibleDepthMm': round(depth_mm, 2),
                                            'lateralCenterMm': round(float(lateral[columns].mean()), 2)}
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
        section = overlay(gray, labels, palette)
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=91)
        Image.fromarray(section).save(media / f'section-{i:02}.webp', quality=88)
        if compression_mm:
            pressed_scan, pressed_section = compress_plates(
                gray, section, depth, field, compression_mm=compression_mm, depth_mm=track['sectorDepthMm'])
            for kind, plate, quality in (('scan', pressed_scan, 91), ('section', pressed_section, 88)):
                name = f'press-{kind}-{i:02}.webp'
                Image.fromarray(plate).save(media / name, quality=quality)
                pressure_names.append(f'media/{name}')
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    tour_evidence = ({'coverage': coverage_evidence(anatomy, frames, offsets, track['fieldWidthMm'], frame_layers)}
                     if sweep_id == 'breast' else {'steering': track['steering']})
    if focused:
        tour_evidence['gelStandoff'] = {
            'method': 'First surface is the anterior union of the native skin, nipple and areola. '
                      'An illustrative gel layer fills clearance between the rigid probe and this surface.',
            'maxLiftFromNativeSkinMm': max(frame['gelLiftMm'] for frame in frames),
            'keyframeLiftMm': {str(i): frames[i]['gelLiftMm'] for i in KEYFRAMES},
            'maxNearestRayClearanceMm': round(float(offsets.min(axis=1).max()), 3),
        }
    if compression_mm:
        tour_evidence.update(compressionMm=compression_mm, compressionSettleDepthMm=SETTLE_DEPTH_MM)
    (output / 'verification.json').write_text(json.dumps({
        **anatomy.receipt, **tour_evidence,
        'case': CASE, 'coordinateFrame': 'HRA native glTF transformed to 1.5 mm RAS voxels',
        'probeType': 'linear', 'fieldShape': 'rectangle', 'voxelMm': VOXEL_MM,
        'fieldWidthMm': track['fieldWidthMm'], 'sectorDepthMm': track['sectorDepthMm'],
        'samplePitchMm': round(float(depth[1]-depth[0]), 8), 'exterior': track['exterior'],
        'surfaceMaxOuterContactErrorMm': round(max_contact, 3),
        'apertureOffsetsMm': profile, 'angleOriginFrame': 0,
        'poseRecipeSha256': pose_recipe_sha256(track['id']), 'sectionPaletteSha256': section_palette_sha256(track),
        'renderRecipeSha256': render_recipe_sha256(sweep_id),
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *parts]) + pressure_names)
    print(f'{sweep_id}: 49 poses checked, first incoming contact residual {max_contact:.3f} mm', flush=True)


def main():
    from dataclasses import replace
    from breast_anatomy import FEMALE_SKIN, load_anatomy
    from breast_layers import layered_stroma, survey_fat_layers

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    parser.add_argument('--skin', type=Path, default=FEMALE_SKIN, help='Pinned female HRA skin GLB')
    parser.add_argument('--track', choices=('breast', 'breast-subareolar'), action='append')
    args = parser.parse_args()
    tracks = [track for track in read_breast_tracks() if args.track is None or track['id'] in args.track]
    for track in tracks:
        if (args.sweeps_dir / track['id']).exists():
            parser.error(f'Choose a fresh destination for {track["id"]}.')
    anatomy = load_anatomy(args.skin)
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        model = anatomy
        if track['id'] == 'breast':
            deep, retro = survey_fat_layers(anatomy)
            model = replace(anatomy, meshes={
                **anatomy.meshes, 'fibroglandular_zone': layered_stroma(anatomy),
                'deep_fat': deep, 'retromammary_fat': retro,
            }, receipt={**anatomy.receipt, 'fibroglandularZone': (
                'Authored envelope around the right HRA lobes, bounded by the source fat envelope. '
                'Native gland meshes and tissue labels remain separate.'),
                'surveyFatContinuity': ('Modeled right deep fat continues off the pectoral margins within the HRA skin. '
                                        'The thin retromammary compartment remains at the modeled muscle fascia.')})
        with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage:
            output = Path(stage) / track['id']
            output.mkdir()
            build(track, output, model)
            output.rename(args.sweeps_dir / track['id'])


if __name__ == '__main__':
    main()
