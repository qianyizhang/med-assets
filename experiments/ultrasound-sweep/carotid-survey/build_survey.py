"""Sample bilateral arterial surfaces and replay a tracked transverse reconstruction."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.measure import find_contours

SHARED = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SHARED))
from build_breast import footprint_hits, orthogonal_sections, slice_segments
from build_study import unit
from geometry import VOXEL_MM
from prepare_scenes import mesh_bytes
from reconstruction import agreement, plane_to_world, raster_grid, reconstruct, world_to_pixel
from bmode_volume import write_volumes
from survey_delivery import acquisition_recipe_sha256
from survey_echo import acoustic_sample
from branch_geometry import separate_daughters

W = 280
PITCH = .15
APERTURE_MM = W * PITCH
SEGMENTS = {
    'cca-prox': ('cca', .23, 'Proximal common carotid'),
    'cca-dist': ('cca', .72, 'Distal common carotid'),
    'bulb': ('cca', .94, 'Distal common carotid / bulb'),
    'ica-prox': ('ica', .17, 'Proximal internal carotid'),
    'ica-mid': ('ica', .44, 'Mid internal carotid'),
    'ica-dist': ('ica', .59, 'Distal visualized cervical internal carotid'),
    'eca': ('eca', .23, 'External carotid'),
    'vertebral': ('vertebral', .30, 'Vertebral artery'),
    'subclavian': ('subclavian', .24, 'Subclavian artery'),
}
TRUNK = ('cca', 'ica', 'eca')


def load_mesh(path):
    with np.load(path, allow_pickle=False) as data:
        return np.asarray(data['vertices'], dtype=float), np.asarray(data['faces'], dtype=np.int32)


def load_line(path, name, side):
    with np.load(path, allow_pickle=False) as data:
        points = np.asarray(data['centerline'], dtype=float)
    axis = 0 if name == 'subclavian' else 2
    direction = -1 if name == 'subclavian' and side == 'left' else 1
    if direction * (points[-1, axis] - points[0, axis]) < 0:
        points = points[::-1]
    keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > .02]
    return points[keep]


def at_fraction(points, fraction):
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    center = np.array([np.interp(fraction * distance[-1], distance, axis) for axis in points.T])
    neighboring = np.array([[np.interp(np.clip(fraction * distance[-1] + offset, 0, distance[-1]),
                                      distance, axis) for axis in points.T] for offset in (-1.8, 1.8)])
    return center, unit(neighboring[1] - neighboring[0])


def file_identity(path, expected=None):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and actual != expected:
        raise ValueError(f'Source identity differs: {path}')
    return actual


def closed_tube(mesh):
    """Close only the two source end rings so longitudinal parity is defined."""
    vertices, faces = mesh
    directed = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    _, indices, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    if np.any(counts > 2):
        raise ValueError('Unexpected nonmanifold source artery')
    boundary = directed[counts[indices] == 1]
    if not len(boundary):
        return mesh
    links = {int(a): int(b) for a, b in boundary}
    if len(links) != len(boundary):
        raise ValueError('Source open edge is not a terminal ring')
    rings = []
    while links:
        start = next(iter(links))
        ring = [start]
        while True:
            following = links.pop(ring[-1])
            if following == start:
                break
            ring.append(following)
        rings.append(ring)
    if len(rings) != 2 or any(len(ring) < 5 for ring in rings):
        raise ValueError('Expected exactly two source terminal rings')
    for ring in rings:
        points = vertices[ring]
        center = points.mean(0)
        normal = np.linalg.svd(points-center)[2][-1]
        if np.max(abs((points-center) @ normal)) > .35:
            raise ValueError('Terminal cap would extend beyond the source ring plane')
        faces = np.vstack((faces, np.column_stack((np.roll(ring, -1), ring, np.full(len(ring), len(vertices))))))
        vertices = np.vstack((vertices, center))
    return vertices, faces


def as_kernel(mesh):
    return mesh[0] / VOXEL_MM, mesh[1]


def mask_at(mesh, center, width, beam, lateral, depth):
    a, b = orthogonal_sections(mesh, np.asarray(center) / VOXEL_MM, width, beam, lateral, depth)
    return a & b


def sections(parts, origin, width, beam, lateral, depth):
    return {key: mask_at(mesh, origin, width, beam, lateral, depth) for key, mesh in parts.items()}


def local_axes(tangent, longitudinal, outward=None):
    if outward is None:
        outward = np.array([0., 1., -.18 if longitudinal else 0.])
    if not longitudinal:
        beam = -unit(np.array([outward[0], outward[1], 0.]))
        return np.cross(beam, [0., 0., -1.]), beam
    # The long-axis plane contains the native flow tangent.
    outward -= tangent * (outward @ tangent)
    beam = -unit(outward)
    if tangent[2] > .4:
        width = -tangent
    else:
        width = tangent * np.sign(tangent[0])
    return width, beam


def scan_pose(skin, target, width, beam):
    width = unit(width - beam * (width @ beam))
    frame = {'contact': target / VOXEL_MM, 'width': width, 'beam': beam}
    distance = footprint_hits(skin, frame, np.array([0.]), np.array([0.]))[0, 0]
    if distance >= -1 or distance < -110:
        raise ValueError(f'No anterior skin contact for target {target.round(1).tolist()}')
    return target + beam * distance


def view_at(skin, target, width, beam, *, steer_origin=None):
    aim = target.copy()
    if steer_origin is not None:
        offset = ((steer_origin - target) @ width) / 2
        aim += width * np.clip(offset, -APERTURE_MM / 2 + 4, APERTURE_MM / 2 - 4)
    contact = scan_pose(skin, aim, width, beam)
    depth = (target - contact) @ beam
    if depth <= 0:
        raise ValueError('Target lies anterior to this sampled skin window')
    height = max(240, int(np.ceil((depth + 13) / PITCH)) + 10)
    return {'widthPx': W, 'heightPx': height, 'mmPerPx': PITCH, 'faceWidthMm': APERTURE_MM,
            'centerPx': [(W - 1) / 2, 6.], 'contact': contact.tolist(),
            'width': width.tolist(), 'beam': beam.tolist()}


def anterior_rows(skin, center, width, beam, lateral):
    """First skin hit per ray, even for the atlas's open named skin patches."""
    contours = slice_segments(skin, np.asarray(center) / VOXEL_MM, width, beam)
    front = np.full(len(lateral), np.inf)
    for a, b in contours:
        if abs(a[0] - b[0]) < 1e-7:
            continue
        start, stop = np.searchsorted(lateral, sorted([a[0], b[0]]))
        x = lateral[start:stop]
        depth = a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
        front[start:stop] = np.minimum(front[start:stop], depth)
    return front


def section_observation(view, artery_meshes, context):
    lateral, depth = raster_grid(view)
    coord = [view[key] for key in ('contact', 'width', 'beam')]
    masks = sections(artery_meshes, *coord, lateral, depth)
    anatomy = sections({key: mesh for key, mesh in context.items() if key != 'skin'}, *coord, lateral, depth)
    front = anterior_rows(context['skin'], *coord, lateral)
    anatomy['skin'] = depth[:, None] >= front
    blocked = np.zeros_like(anatomy['skin'])
    for key, region in anatomy.items():
        if key in ('mandible', 'clavicle', 'first-rib', 'temporal-bone', 'c3', 'c4', 'c5', 'c6', 'c7'):
            blocked |= np.maximum.accumulate(region, axis=0)
    visible = anatomy['skin'] & ~blocked
    return masks, anatomy, visible, blocked


def scan(root, name, view, artery_meshes, context, selected=None, observation=None):
    masks, anatomy, visible, blocked = observation or section_observation(view, artery_meshes, context)
    gray, lumen = acoustic_sample(view, masks, anatomy)
    gray = (gray * np.where(blocked, .22, 1)).astype('u1')
    lumen &= visible
    path = f'media/{name}.webp'
    mask_path = f'media/{name}-mask.png'
    Image.fromarray(gray).save(root / path, quality=89)
    Image.fromarray(lumen.astype('u1') * 255).save(root / mask_path)
    outlines = [plane_to_world(view, ring[::2, ::-1]).round(3).tolist()
                for ring in find_contours(lumen, .5) if len(ring) >= 12]
    target = masks[selected] & lumen if selected else lumen
    if selected in ('ica', 'eca'):
        rival = 'eca' if selected == 'ica' else 'ica'
        target &= ~masks[rival]
    target_data = {}
    if selected:
        name = f'media/{name}-target.png'
        Image.fromarray(target.astype('u1') * 255).save(root / name)
        target_data['dopplerMaskPath'] = name
    return {**view, 'path': path, 'lumenMaskPath': mask_path, 'contours': outlines, **target_data}, target


def chord(view, mask, center, direction):
    offsets = np.linspace(-25, 25, 501)
    points = center + offsets[:, None] * direction
    coords = world_to_pixel(view, points)
    inside = nd.map_coordinates(mask.astype('f4'), coords.T[::-1], order=1, mode='constant') >= .5
    if not inside[len(offsets) // 2]:
        return None
    first = np.flatnonzero(~inside[:250])
    last = np.flatnonzero(~inside[250:])
    if not len(first) or not len(last):
        return None
    a, b = points[first[-1]+1], points[250+last[0]-1]
    return np.linalg.norm(b-a), [a.round(3).tolist(), b.round(3).tolist()]


def gate_window(skin, anchor, w, b, tangent, polarity, framing_shift=0):
    steer = unit(b + polarity * tangent * np.tan(np.deg2rad(30)))
    skin_point = scan_pose(skin, anchor, w, steer)
    view = view_at(skin, anchor + framing_shift*tangent, w, b, steer_origin=skin_point)
    clearance = float((skin_point - view['contact']) @ b)
    face = skin_point - steer * clearance / (steer @ b)
    return view, (steer, skin_point, face, clearance)


def gate_is_supported(view, anchor, route, observation):
    _, skin_point, face, clearance = route
    col = world_to_pixel(view, face)[0]
    if col < 2 or col > view['widthPx'] - 3 or abs(clearance) > 4:
        return False
    line = skin_point[None, :] + np.linspace(.04, .94, 80)[:, None] * (anchor-skin_point)
    xy = world_to_pixel(view, line)
    return not any(nd.map_coordinates(part.astype('u1'), xy.T[::-1], order=0, mode='constant').any()
                   for name, part in observation[1].items()
                   if name in ('mandible', 'clavicle', 'first-rib', 'temporal-bone', 'c3', 'c4', 'c5', 'c6', 'c7'))


def gate_payload(view, anchor, tangent, route, diameter, supported):
    transmit, skin_contact, face, clearance = route
    return {'center': anchor.round(4).tolist(), 'centerPx': world_to_pixel(view, anchor).round(4).tolist(),
            'wallPoints': diameter[1], 'diameterMm': round(float(diameter[0]), 2),
            'flowDirection': tangent.tolist(), 'beamDirection': transmit.tolist(),
            'steeringSupported': supported, 'steeredOriginPx': world_to_pixel(view, face).round(4).tolist(),
            'steeredOriginMm': face.round(4).tolist(), 'steeredSkinContactMm': skin_contact.round(4).tolist(),
            'steeredSkinClearanceMm': round(clearance, 4)}


def station(root, side, segment, row, artery_meshes, paths, skin, context):
    artery, fraction, label = row
    if artery not in paths:
        return None
    name = f'{side}-{segment}'
    candidate = None
    sign = 1 if side == 'right' else -1
    # Search a small span of each original curve. A viewing window may move,
    # but every emitted scan intersects the unchanged native tube.
    if segment == 'subclavian':
        shifts = (0., -.065, .065, .13, -.13, .22, .32, .43)
    elif segment == 'ica-dist':
        shifts = (0., -.065, .065, .13, -.13)
    else:
        shifts = (0., -.045, .045)
    for shift in shifts:
        anchor, tangent = at_fraction(paths[artery], float(np.clip(fraction + shift, .05, .92)))
        if segment.startswith('ica-') and anchor[2] > 1563:
            continue
        hits = []
        for kind in ('transverse', 'longitudinal'):
            options = []
            angles = (0, 20, 38, 56, 68, 78, 88, 95, -15)
            for degrees in angles:
                yaw = np.deg2rad(degrees)
                for pitch in (-.46, -.18, .16, .40, .64) if segment == 'subclavian' else (
                        (-.18, .16, .40) if segment == 'ica-dist' else (-.18,)):
                    w, b = local_axes(tangent, kind == 'longitudinal',
                                      np.array([sign*np.sin(yaw), np.cos(yaw), pitch]))
                    polarities = (1, -1) if kind == 'longitudinal' and side == 'left' and segment in ('cca-prox', 'subclavian') else (1,)
                    for polarity in polarities:
                        route = None
                        try:
                            if kind == 'longitudinal':
                                view, route = gate_window(skin, anchor, w, b, tangent, polarity)
                            else:
                                view = view_at(skin, anchor, w, b)
                        except ValueError:
                            continue
                        depth_mm = float((anchor - view['contact']) @ b)
                        if depth_mm > 78:
                            continue
                        observation = section_observation(view, artery_meshes, context)
                        vessel, visible = observation[0][artery], observation[2]
                        focused = vessel & visible
                        if artery in ('ica', 'eca'):
                            alternate = 'eca' if artery == 'ica' else 'ica'
                            cc, rr = world_to_pixel(view, anchor)
                            if nd.map_coordinates(observation[0][alternate].astype('u1'),
                                                  [[rr], [cc]], order=0, mode='constant')[0]:
                                continue
                        axis_a, axis_b = (b, w) if kind == 'longitudinal' else (np.array([0., -1, 0]), np.array([1., 0, 0]))
                        first = chord(view, focused, anchor, axis_a)
                        second = chord(view, focused, anchor, axis_b)
                        if first is None or (kind == 'transverse' and second is None) or focused.sum() < 22:
                            continue
                        clear = focused.sum() / max(vessel.sum(), 1)
                        supported = route is not None and gate_is_supported(view, anchor, route, observation)
                        score = clear * 2.6 - depth_mm / 43 - abs(yaw) * .31 + 1.7 * supported
                        options.append((score, kind, view, observation, first, second, route, supported))
            if not options:
                break
            hits.append(max(options, key=lambda option: option[0]))
        if len(hits) == 2:
            score = sum(option[0] for option in hits) - abs(shift) * 5
            if candidate is None or score > candidate[0]:
                candidate = score, anchor, tangent, hits
    if candidate is None:
        return {'id': name, 'side': side, 'segment': segment, 'label': label, 'available': False,
                'reason': 'An anterior or anterolateral atlas window did not show a full native arterial section.'}
    _, anchor, tangent, hits = candidate
    views = {}
    for _, kind, view, observation, *_ in hits:
        views[kind], _ = scan(root, f'{name}-{kind}', view, artery_meshes, context, artery, observation)
    ap, tx = hits[0][4:6]
    diameter = hits[1][4]
    route, supported = hits[1][-2:]
    return {'id': name, 'side': side, 'segment': segment, 'label': label, 'available': True,
            'views': views, 'measurements': {'apMm': round(float(ap[0]), 2), 'leftRightMm': round(float(tx[0]), 2)},
            'gate': gate_payload(views['longitudinal'], anchor, tangent, route, diameter, supported)}


def height_point(path, z):
    index = int(np.argmin(abs(path[:, 2] - z)))
    return path[index].copy()


def bifurcation(root, side, station_data, artery_meshes, paths, skin, context):
    # Verify a daughter-only short section and a parent/daughter long section
    # from the evaluated named source meshes. No duplicate "two circles" cue
    # from the neighboring jugular is accepted as a fork.
    fork = paths['cca'][-1]
    sign = 1 if side == 'right' else -1
    short = []
    for cranial in (10., 11., 12., 14., 17., 21., 25., 29., 35., 39.):
        level = fork[2] + cranial
        a, b = (height_point(paths[artery], level) for artery in ('ica', 'eca'))
        anchor = (a + b) / 2
        anchor[2] = level
        for degrees in (0, 25, 45, 60, 75, 87, 95):
            angle = np.deg2rad(degrees)
            w, b = local_axes(None, False, np.array([sign*np.sin(angle), np.cos(angle), 0.]))
            try:
                view = view_at(skin, anchor, w, b)
            except ValueError:
                continue
            observed = section_observation(view, artery_meshes, context)
            ica, eca = [observed[0][key] & observed[2] for key in ('ica','eca')]
            if min(ica.sum(), eca.sum()) < 45 or np.count_nonzero(ica & eca) > 0:
                continue
            score = min(ica.sum(), eca.sum()) / 180 - cranial * .025 - angle * .22
            short.append((score, view, observed, float(level)))
    long = []
    for caudal in (3., 5., 8., 11.):
        anchor = height_point(paths['cca'], fork[2] - caudal)
        tangent = unit(fork - anchor)
        for degrees in range(-25, 106, 5):
            angle = np.deg2rad(degrees)
            w, b = local_axes(tangent, True, np.array([sign*np.sin(angle), np.cos(angle), 0.]))
            for framing_shift in (0., 6., 11., 15.):
                for polarity in ((1, -1) if side == 'left' else (1,)):
                    try:
                        view, route = gate_window(skin, anchor, w, b, tangent, polarity, framing_shift)
                    except ValueError:
                        continue
                    observation = section_observation(view, artery_meshes, context)
                    cca, ica, eca = [observation[0][key] & observation[2] for key in TRUNK]
                    joined, _ = nd.label(cca | ica | eca)
                    sizes = np.bincount(joined[cca])
                    if len(sizes) < 2:
                        continue
                    sizes[0] = 0
                    component = joined == sizes.argmax()
                    owned_ica = ica & ~eca & component
                    owned_eca = eca & ~ica & component
                    # Require both daughter boundaries to separate downstream within
                    # at least one acquired detector column of the same connected fork.
                    separated = 0
                    for col in np.flatnonzero(owned_ica.any(0) & owned_eca.any(0)):
                        _, count = nd.label(component[:, col])
                        separated += count >= 2
                    if separated < 3 or min(owned_ica.sum(), owned_eca.sum()) < 36:
                        continue
                    diameter = chord(view, cca, anchor, b)
                    if diameter is None:
                        continue
                    supported = gate_is_supported(view, anchor, route, observation)
                    score = min(owned_ica.sum(), owned_eca.sum()) / 165 + separated / 30 + 1.4 * supported - abs(angle) * .19
                    long.append((score, view, observation, anchor, tangent, route, diameter, supported, int(separated)))
    if not short or not long:
        raise ValueError(f'{side}: cannot verify an exposed native three-vessel bifurcation')
    _, view_s, obs_s, level = max(short, key=lambda row: row[0])
    _, view_l, obs_l, a, t, route, d, supported, columns = max(long, key=lambda row: row[0])
    station_data['measurementView'] = station_data['views']['transverse']
    orphan = station_data['views']['longitudinal']
    for key in ('path', 'lumenMaskPath', 'dopplerMaskPath'):
        (root / orphan[key]).unlink()
    station_data['views']['transverse'], _ = scan(root, f'{side}-fork-transverse', view_s,
                                                  artery_meshes, context, observation=obs_s)
    station_data['views']['longitudinal'], _ = scan(root, f'{side}-fork-longitudinal', view_l,
                                                    artery_meshes, context, selected='cca', observation=obs_l)
    station_data['gate'] = gate_payload(station_data['views']['longitudinal'], a, t, route, d, supported)
    if not supported:
        # Color illustrates the projection directly, without a spectral trace
        # or angle-corrected velocity. Preserve the selected grayscale plane.
        w, b = (np.asarray(view_l[key]) for key in ('width', 'beam'))
        for degrees in (-30, 30, -25, 25, -20, 20, -15, 15, -10, 10):
            transmit = unit(b + t * np.tan(np.deg2rad(degrees)))
            try:
                contact = scan_pose(skin, a, w, transmit)
            except ValueError:
                continue
            clearance = float((contact - view_l['contact']) @ b)
            face = contact - transmit * clearance / (transmit @ b)
            color_route = transmit, contact, face, clearance
            if gate_is_supported(view_l, a, color_route, obs_l):
                station_data['colorGate'] = {
                    **gate_payload(view_l, a, t, color_route, d, True),
                    'steeringDeg': degrees, 'beamFlowAngleDeg': 90 - abs(degrees),
                }
                break
    station_data['label'] = 'Bulb and bifurcation'
    masks = {}
    for mode, data in (('transverse', obs_s), ('longitudinal', obs_l)):
        masks[mode] = {}
        for name in TRUNK:
            path = f'media/{side}-fork-{mode}-{name}-evidence.png'
            Image.fromarray((data[0][name] & data[2]).astype('u1') * 255).save(root/path)
            masks[mode][name] = path
    station_data['forkEvidence'] = {'forkMm': fork.round(4).tolist(),
                                    'transverseLevelMm': round(level, 3), 'distinctDaughters': ['ICA','ECA'],
                                    'arterialMaskPaths': masks,
                                    'longitudinalSplitColumns': columns,
                                    'caliperPlane': 'Original transverse bulb plane proximal to the split.'}
    return station_data


def tracked_stack(root, side, arteries, paths, skin, context):
    trunk = {key: arteries[key] for key in TRUNK}
    # Start above the thoracic origin and target the cervical rather than
    # intracranial ICA. The acquisition still stops at the first true blind plane.
    floor = max(float(np.min(paths['cca'][:, 2])) + 7, 1411)
    roof = min(float(np.max(paths['ica'][:, 2])) - 2, 1558.8)
    if roof - floor < 18:
        raise ValueError(f'{side}: source branch coverage too short for tracked survey')
    step = 1.3
    transition = 1548.
    levels = np.r_[np.linspace(floor, transition, int(np.ceil((transition - floor) / step)) + 1)[:-1],
                   np.linspace(transition, roof, int(np.ceil((roof - transition) / .65)) + 1)]
    sign = 1 if side == 'right' else -1
    frames = []
    blocked_at = None
    previous = 0.
    last_contact = None
    for idx, z in enumerate(levels):
        targets = {key: path[np.argmin(abs(path[:, 2] - z))] for key, path in paths.items()
                   if key in TRUNK and path[:, 2].min() <= z <= path[:, 2].max()}
        if not targets:
            if not frames:
                continue
            blocked_at = float(z)
            break
        mean_target = np.mean(list(targets.values()), axis=0)
        anchors = [mean_target]
        if z > 1535 and 'ica' in targets:
            anchors.append(targets['ica'].copy())
        options = []
        degrees = (-23, -12, 0, 12, 23, 32, 40, 46, 53) if z < 1530 else (
            -12, 0, 15, 25, 35, 45, 53, 60, 65, 70, 75, 80, 85, 90, 95)
        for center in anchors:
            center[2] = z
            for yaw in degrees:
                angle = np.deg2rad(yaw)
                width, beam = local_axes(None, False, np.array([sign*np.sin(angle), np.cos(angle), 0.]))
                try:
                    info = view_at(skin, center, width, beam)
                except ValueError:
                    continue
                contact = np.asarray(info['contact'])
                depth = np.linalg.norm(contact - center)
                travel = 0 if last_contact is None else np.linalg.norm(contact - last_contact)
                if depth > 78 or travel > 18:
                    continue
                obs = section_observation(info, trunk, context)
                source = np.logical_or.reduce(list(obs[0].values()))
                measured = source & obs[2]
                intact = measured.sum() / max(source.sum(), 1)
                if not measured.any() or intact < .18 or measured[:, (0, -1)].any() or measured[-1].any():
                    continue
                branch_visibility = {key: float((part & obs[2]).sum() / part.sum())
                                     for key, part in obs[0].items() if part.sum() >= 12}
                if z > 1492 and branch_visibility.get('ica', 0) < (.21 if z >= 1554 else .42):
                    continue
                minimum_branch = min(branch_visibility.values(), default=0)
                score = (3.5 * intact + 2.2 * minimum_branch + 3.4 * branch_visibility.get('ica', 0)
                         - abs(yaw - previous) * .019 - abs(yaw) * .008 - travel * .060)
                options.append((score, yaw, info, obs, intact, branch_visibility))
        if not options:
            if not frames:
                continue
            blocked_at = float(z)
            break
        _, previous, info, obs, intact, branch_visibility = max(options, key=lambda row: row[0])
        last_contact = np.asarray(info['contact'])
        id_ = f'{side}-tracked-{idx:03}'
        picture, _ = scan(root, id_, info, trunk, context, observation=obs)
        frames.append({**picture, 'id': id_, 'observedSourceFraction': round(float(intact), 4),
                       'branchVisibility': {key: round(value, 4) for key, value in branch_visibility.items()},
                       'segment': 'cca' if z < paths['cca'][-1, 2] - 2 else 'branches'})
    if not frames or frames[-1]['contact'][2] <= paths['cca'][-1, 2] + 5:
        raise ValueError(f'{side}: tracked window does not reach both post-bifurcation branches')
    mesh, field, axes = reconstruct(frames, root)
    width, beam = local_axes(None, False)
    def reference_plane(x, y, z):
        return np.logical_or.reduce([mask_at(part, [0, 0, z], width, beam, x, -y[::-1])[::-1].T
                                     for part in trunk.values()])
    observed_levels = np.asarray([frame['contact'][2] for frame in frames])
    metrics = agreement(field, axes, reference_plane, (observed_levels[:-1] + observed_levels[1:]) / 2)
    components, component_count = nd.label(field >= 0)
    sizes = np.bincount(components.ravel())[1:]
    metrics['largestReconstructedComponentFraction'] = round(float(sizes.max() / sizes.sum()), 3)
    metrics['reconstructedComponentCount'] = int(component_count)
    metrics['observedBranchSpansMm'] = {
        key: [round(float(min(levels)), 3), round(float(max(levels)), 3)] if levels else None
        for key in TRUNK for levels in [[frame['contact'][2] for frame in frames
                                        if frame['branchVisibility'].get(key, 0) >= .18]]
    }
    metrics['icaUnobservedFramesAboveBifurcation'] = sum(
        frame['branchVisibility'].get('ica', 0) < .2 for frame in frames
        if frame['contact'][2] >= paths['cca'][-1, 2] + 6
    )
    metrics.update(observedFrames=len(frames), slabBoundsMm=[float(observed_levels[0]), float(observed_levels[-1])],
                   firstBlockedPlaneMm=blocked_at,
                   plannedAxialSpanAcquiredFraction=round(float(
                       (observed_levels[-1] - observed_levels[0]) / (roof - floor)), 3),
                   sectionSpacingMm=round(float(np.median(np.diff(observed_levels))), 3),
                   maxProbeStepMm=round(float(np.linalg.norm(np.diff(
                       [frame['contact'] for frame in frames], axis=0), axis=1).max()), 3),
                   reconstructionGridPitchMm=round(float(axes[0][1]-axes[0][0]), 3))
    return frames, mesh, metrics


def build_assets(input_path, output):
    spec = json.loads(input_path.read_text())
    source = json.loads(Path(__file__).with_name('source-manifest.json').read_text())
    if spec['memberSha256'] != source['blendMemberSha256']:
        raise ValueError('Source Blender object identity differs')
    file_identity(input_path, source['files']['atlas.json'])
    root = input_path.parent
    if output.exists():
        raise ValueError(f'Choose a fresh output directory: {output}')
    (output / 'media').mkdir(parents=True)
    (output / 'scenes').mkdir()
    def resolve(item):
        path = root / (item['path'] if isinstance(item, dict) else item)
        file_identity(path, source['files'][path.name])
        return path
    skin = load_mesh(resolve(spec['skin']))
    (output / 'scenes/skin.mesh').write_bytes(mesh_bytes(*skin))
    outlines = {'skinPath': 'scenes/skin.mesh', 'parts': []}
    stations, tracking, reconstructions, corrections = [], {}, {}, {}
    for side, group in spec['sides'].items():
        files = {key: resolve(row) for key, row in group['arteries'].items()}
        meshes = {key: closed_tube(load_mesh(path)) for key, path in files.items()}
        paths = {key: load_line(path, key, side) for key, path in files.items()}
        corrections[side] = separate_daughters(meshes, paths)
        kernel = {key: as_kernel(mesh) for key, mesh in meshes.items()}
        context = {'skin': as_kernel(skin)}
        common_context = {key.removeprefix(side + '-'): value for key, value in spec.get('context', {}).items()
                          if key.startswith(side + '-') or key in ('mandible', 'thyroid', 'trachea', 'thyroid-cartilage', 'c3', 'c4', 'c5', 'c6', 'c7')}
        for name, value in (common_context | group.get('context', {})).items():
            mesh = load_mesh(resolve(value))
            dest = f'scenes/{side}-{name}.mesh'
            (output / dest).write_bytes(mesh_bytes(*mesh))
            context[name] = as_kernel(mesh)
            outlines['parts'].append({'side': side, 'id': name, 'path': dest})
        parts = {}
        for key, mesh in meshes.items():
            dest = f'scenes/{side}-{key}.mesh'
            (output / dest).write_bytes(mesh_bytes(*mesh))
            parts[key] = dest
        for seg, row in SEGMENTS.items():
            item = station(output, side, seg, row, kernel, paths, context['skin'], context)
            if item:
                stations.append(bifurcation(output, side, item, kernel, paths, context['skin'], context)
                                if seg == 'bulb' else item)
        tracking[side], stitched, metrics = tracked_stack(output, side, kernel, paths, context['skin'], context)
        for item in (station for station in stations if station['side'] == side and station['available']):
            height = item['gate']['center'][2]
            nearest = min(tracking[side], key=lambda frame: abs(frame['contact'][2] - height))
            if abs(nearest['contact'][2] - height) < 3:
                item['trackId'] = nearest['id']
        path = f'scenes/{side}-stitched.mesh'
        (output / path).write_bytes(mesh_bytes(*stitched))
        reconstructions[side] = {'sourcePaths': parts, 'reconstructionPath': path,
                                 'observedFrames': len(tracking[side]), 'metrics': metrics}
        print(side, metrics, flush=True)
    geometry = {'schemaVersion': 1, 'units': 'mm', 'orientation': 'RAS',
                'anatomySource': spec.get('anatomySource', {'label': spec['atlas'],
                    'url': 'https://www.z-anatomy.com/', 'license': 'CC BY-SA 4.0',
                    'licenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/'}), 'context': outlines,
                'stations': stations, 'tracking': tracking, 'reconstructions': reconstructions,
                'volumes': write_volumes(output, tracking),
                'sourceArchiveSha256': source['archive']['sha256'], 'authoredBranchSeparation': corrections,
                'coverageNote': ('The tracked cervical slab ends inferior to the temporal bone. '
                                 'The atlas source arteries extend beyond observed sections; '
                                 'bone-shadowed or out-of-window pixels do not contribute to the reconstruction.'),
                'sourceTopology': 'Source evaluated artery surfaces retain their vertices; two observed terminal end rings per tube are capped for section fill.',
                'reconstructionMethod': ('World-space compounding of paired masks from tracked parallel sections. '
                                         'Signed distances are interpolated between adjacent observations with no '
                                         'extrapolation beyond the observed slab. Comparisons sample held-out source cuts.')}
    geometry['acquisitionRecipeSha256'] = acquisition_recipe_sha256(Path(__file__).parent)
    (output / 'protocol-geometry.json').write_text(json.dumps(geometry, separators=(',', ':')) + '\n')
    names = sorted(path for path in output.rglob('*') if path.is_file())
    (output / 'delivery.json').write_text(json.dumps({str(p.relative_to(output)): file_identity(p) for p in names}, indent=2) + '\n')


def build(input_path, output):
    if output.exists():
        raise ValueError(f'Choose a fresh output directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as scratch:
        staged = Path(scratch) / 'acquisition'
        build_assets(input_path, staged)
        staged.rename(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.source_manifest, args.output)
