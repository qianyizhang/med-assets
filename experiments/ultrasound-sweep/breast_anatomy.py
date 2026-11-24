"""Prepare the female HRA breast exterior and a schematic posterior teaching wall."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage as nd
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree

from display_body import ROOT, atlas, primitive_stream, ras_from_gltf
from geometry import VOXEL_MM

MAMMARY = 'models/breasts_hra/exports/teaching-economy-r01/breasts_hra_native_frame.glb'
MAMMARY_SHA = '2a7d6d05e06fa8d86adffdf0fd324389cf23ac736b3b659f7c227b96e499fe51'
FEMALE_SKIN = ROOT / '.artifacts/breast-tour/source/3d-vh-f-skin.glb'
FEMALE_SKIN_URL = 'https://cdn.humanatlas.io/digital-objects/ref-organ/skin-female/v1.3/assets/3d-vh-f-skin.glb'
FEMALE_SKIN_SHA = '0fc377c7a2e7e9644b81d318feda9d0b2c5a38f39bd14e74966f8b6364eb0a78'
TISSUES = {
    'breast_fat': 'fat',
    'mammary_lobes': 'mammary_lobes',
    'lactiferous_ducts': 'main_lactiferous_ducts',
    'suspensory_ligaments': 'suspensory_ligaments',
    'nipple': 'nipple',
    'areola': 'areola',
}
CHEST_CENTER = (3, 274)
CHEST_RADII = (92, 87)
PECTORAL_WIDTH = np.array([3, 12, 29, 47, 65, 80, 91, 95])
PECTORAL_INFERIOR = PchipInterpolator(PECTORAL_WIDTH, [223, 218, 221, 229, 242, 264, 292, 311],
                                     extrapolate=False)
PECTORAL_SUPERIOR = PchipInterpolator(PECTORAL_WIDTH, [334, 349, 359, 355, 347, 338, 331, 322],
                                     extrapolate=False)


def mesh_for(doc, binary, node_name):
    node = next(node for node in doc['nodes'] if node.get('name') == node_name)
    if {'matrix', 'translation', 'scale', 'rotation'} & node.keys():
        raise ValueError(f'Unexpected native atlas node transform: {node_name}')
    primitive, = doc['meshes'][node['mesh']]['primitives']
    positions = primitive_stream(doc, binary, primitive['attributes']['POSITION']).reshape(-1, 3)
    faces = primitive_stream(doc, binary, primitive['indices']).reshape(-1, 3)
    vertices = ras_from_gltf(positions).astype(float) * (1000 / VOXEL_MM)
    return vertices, faces


def concatenate(meshes):
    points, triangles = [], []
    offset = 0
    for vertices, faces in meshes:
        points.append(vertices)
        triangles.append(faces.astype(np.uint32) + offset)
        offset += len(vertices)
    return np.concatenate(points), np.concatenate(triangles)


def close_duct_tips(vertices, faces):
    """Close the pinned atlas tube ends for section fill, without joining ducts."""
    points, renumbered = np.unique(vertices, axis=0, return_inverse=True)
    faces = renumbered[faces]
    directed = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    _, edge_index, uses = np.unique(
        np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True,
    )
    boundary = directed[uses[edge_index] == 1]
    successors = dict(boundary.tolist())
    if (np.any(uses > 2) or len(successors) != len(boundary)
            or successors.keys() != set(successors.values())):
        raise ValueError('Expected disjoint duct tip boundaries in pinned breast atlas')

    centers, caps = [], []
    while successors:
        start = next(iter(successors))
        ring = [start]
        vertex = successors.pop(start)
        while vertex != start:
            ring.append(vertex)
            vertex = successors.pop(vertex)
        ring = np.array(ring)
        perimeter = points[ring]
        center = perimeter.mean(axis=0)
        offsets = perimeter - center
        _, _, axes = np.linalg.svd(offsets, full_matrices=False)
        normal = axes[-1]
        winding = np.cross(offsets, np.roll(offsets, -1, axis=0)) @ normal
        if (np.linalg.norm(np.ptp(perimeter, axis=0)) * VOXEL_MM > 3
                or np.max(np.abs(offsets @ normal)) * VOXEL_MM > .05
                or not (np.all(winding > 0) or np.all(winding < 0))):
            raise ValueError('Duct boundary is too large or irregular for a local cap')
        caps.extend(zip(np.roll(ring, -1), ring, np.repeat(len(points) + len(centers), len(ring))))
        centers.append(center)
    if len(centers) != 30:
        raise ValueError('Expected 30 duct tip boundaries per side in pinned breast atlas')
    return np.concatenate([points, centers]), np.concatenate([faces, caps])


def select_faces(vertices, faces, chosen):
    used, renumbered = np.unique(faces[chosen], return_inverse=True)
    return vertices[used], renumbered.reshape(-1, 3)


class AnteriorSurface:
    """Intersect the exact display mesh along the anterior case axis."""

    def __init__(self, vertices, faces):
        self.triangles = vertices[faces]
        xz = self.triangles[..., [0, 2]]
        centers = xz.mean(1)
        self.radius = np.max(np.linalg.norm(xz - centers[:, None, :], axis=2))
        self.index = cKDTree(centers)

    def extrema(self, x, z):
        here = np.array([x, z])
        nearby = self.triangles[self.index.query_ball_point(here, self.radius + 1e-6)]
        a, b, c = nearby[..., [0, 2]].transpose(1, 0, 2)
        ab, ac = b - a, c - a
        delta = here - a
        det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
        valid = np.abs(det) > 1e-9
        d, ab, ac, delta = det[valid], ab[valid], ac[valid], delta[valid]
        u = (delta[:, 0] * ac[:, 1] - delta[:, 1] * ac[:, 0]) / d
        v = (ab[:, 0] * delta[:, 1] - ab[:, 1] * delta[:, 0]) / d
        inside = (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8)
        if not inside.any():
            return None
        y = nearby[valid, :, 1][inside]
        height = y[:, 0] + (y[:, 1] - y[:, 0]) * u[inside] + (y[:, 2] - y[:, 0]) * v[inside]
        return float(height.min()), float(height.max())

    def contact(self, x, z):
        height = self.extrema(x, z)
        if height is None:
            raise ValueError(f'Breast contact lies off the displayed exterior: X={x:.2f}, Z={z:.2f}')
        return np.array([x, height[1], z])


def wall_front(base, x, z):
    return base + 4.2 - .0011 * x**2 - .0006 * (z - 256)**2


def wall_layer(base, thickness):
    """Build a closed, smoothly rounded regional layer on the breast bed."""
    steps, rings = 72, 18
    angles = np.arange(steps) * (2 * np.pi / steps)
    radial = np.arange(1, rings + 1) / rings
    rho, theta = np.meshgrid(radial, angles, indexing='ij')
    x = CHEST_CENTER[0] + np.r_[0, (CHEST_RADII[0] * rho * np.cos(theta)).ravel()]
    z = CHEST_CENTER[1] + np.r_[0, (CHEST_RADII[1] * rho * np.sin(theta)).ravel()]
    edge = np.r_[0, rho.ravel()]
    width = thickness * (.22 + .78 * (1 - edge ** 3))
    y = wall_front(base, x, z)
    front = np.column_stack((x, y, z))
    back = front.copy()
    back[:, 1] -= width
    near = np.arange(steps)
    nxt = np.roll(near, -1)
    disc = [np.column_stack((np.zeros(steps, dtype=int), 1 + nxt, 1 + near))]
    for row in range(rings - 1):
        first = row * steps + 1
        a, b = first + near, first + nxt
        c, d = b + steps, a + steps
        disc.extend([np.column_stack((a, b, c)), np.column_stack((a, c, d))])
    disc = np.concatenate(disc)
    count = len(front)
    a = (rings - 1) * steps + 1 + near
    b = np.roll(a, -1)
    side = [np.column_stack((a, b, a + count)), np.column_stack((b, b + count, a + count))]
    return np.concatenate((front, back)), np.concatenate((disc, disc[:, ::-1] + count, *side))


def grid_triangles(shape, valid):
    idx = np.arange(np.prod(shape)).reshape(shape)
    a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    cells = np.stack((a, b, c, d), axis=-1).reshape(-1, 4)
    a, b, c, d = cells[np.all(valid.ravel()[cells], axis=1)].T
    return np.concatenate((np.column_stack((a, b, c)), np.column_stack((a, c, d))))


def boundary_edges(forward):
    directed = forward[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    _, ids, counts = np.unique(np.sort(directed, axis=1), axis=0, return_index=True, return_counts=True)
    return directed[ids[counts == 1]]


def closed_layer(front, back, forward):
    a, b = boundary_edges(forward).T
    size = len(front)
    wall = [np.column_stack((a, a + size, b)), np.column_stack((b, a + size, b + size))]
    faces = np.concatenate((forward, forward[:, ::-1] + size, *wall))
    return select_faces(np.concatenate((front, back)), faces, np.ones(len(faces), dtype=bool))


def pectoralis_layer(side):
    """Taper the broad sternal origin toward the narrower upper-lateral edge."""
    x = np.linspace(PECTORAL_WIDTH[0], PECTORAL_WIDTH[-1], 49)
    low, high = PECTORAL_INFERIOR(x), PECTORAL_SUPERIOR(x)
    fraction = np.linspace(0, 1, 54)
    z = np.sort(low[:, None] + (high - low)[:, None] * fraction, axis=1)
    xx = np.broadcast_to(side * x[:, None], z.shape)
    y = wall_front(-15, xx, z)
    width = 1.2 + 5.2 * np.sin(np.pi * fraction) ** .7 * (1 - (x[:, None] / 102) ** 3)
    front = np.column_stack((xx.ravel(), y.ravel(), z.ravel()))
    back = np.column_stack((xx.ravel(), (y - width).ravel(), z.ravel()))
    triangles = grid_triangles(z.shape, np.ones_like(z, dtype=bool))
    return closed_layer(front, back, triangles if side > 0 else triangles[:, ::-1])


def fat_bed_layers(mesh):
    """Join the fascia to the posterior fat footprint as an illustrative fat bed."""
    vertices, _ = mesh
    lower, upper = np.floor(vertices[:, [0, 2]].min(0)), np.ceil(vertices[:, [0, 2]].max(0))
    x, z = np.meshgrid(np.arange(lower[0], upper[0] + 1, 1.4),
                       np.arange(lower[1], upper[1] + 1, 1.4), indexing='ij')
    fat = AnteriorSurface(*mesh)
    bounds = [fat.extrema(a, b) for a, b in zip(x.ravel(), z.ravel(), strict=True)]
    posterior = np.array([item[0] if item else np.nan for item in bounds]).reshape(x.shape)
    fascia = wall_front(-15, x, z)
    usable = (np.isfinite(posterior) & (z > PECTORAL_INFERIOR(np.abs(x)) + 1)
              & (z < PECTORAL_SUPERIOR(np.abs(x)) - 1))
    # Fit the shared posterior boundary exactly. Smooth the sampled anterior fat
    # envelope to avoid reproducing tiny holes or jagged mesh edges in this layer.
    lookup = nd.distance_transform_edt(~usable, return_distances=False, return_indices=True)
    smooth = nd.gaussian_filter(posterior[tuple(lookup)], 1.15)
    gap = np.clip(np.maximum(smooth, posterior) + .4 - fascia, .3, 18)
    forward = grid_triangles(x.shape, usable)
    edges = boundary_edges(forward)
    start, end = np.concatenate((edges, edges[:, ::-1])).T
    counts = np.bincount(start, minlength=x.size)
    boundary = np.flatnonzero(counts)
    xz = np.column_stack((x.ravel(), z.ravel()))
    # Remove the sampling-grid steps from the thin shared outline. Interior
    # sections and the independently supplied atlas fat remain unchanged.
    rounded = xz.copy()
    for _ in range(3):
        sums = np.column_stack([np.bincount(start, weights=axis[end], minlength=x.size) for axis in rounded.T])
        rounded[boundary] += .52 * (sums[boundary] / counts[boundary, None] - rounded[boundary])
    delta = rounded - xz
    xz += delta * (.9 / np.maximum(.9, np.linalg.norm(delta, axis=1)))[:, None]
    x, z = xz.T
    fascia = wall_front(-15, x, z)
    gap = gap.ravel()
    retromammary = fascia + np.minimum(gap / 2, 3)
    fascia_xyz, retromammary_xyz, anterior_xyz = (
        np.column_stack((x, y, z))
        for y in (fascia, retromammary, fascia + gap)
    )
    return (
        closed_layer(anterior_xyz, retromammary_xyz, forward),
        closed_layer(retromammary_xyz, fascia_xyz, forward),
    )


@dataclass
class BreastAnatomy:
    meshes: dict
    receipt: dict
    exterior: AnteriorSurface

    def contact(self, x, z):
        return self.exterior.contact(x, z)


def load_anatomy(skin_path=FEMALE_SKIN):
    source, binary = atlas(MAMMARY, MAMMARY_SHA)
    female, skin_data = atlas(Path(skin_path), FEMALE_SKIN_SHA)
    body, faces = mesh_for(female, skin_data, 'VH_F_skin')
    # The cut lies well below the chest framing. Retain the neck, shoulders and
    # the exact source surface throughout the probe and visible breast region.
    torso = select_faces(body, faces, np.all(body[faces, 2] > 112, axis=1))
    meshes = {'torso': torso}
    nipples = {}
    for key, name in TISSUES.items():
        sides = [mesh_for(source, binary, f'VH_F_{name}_{side}') for side in ('R', 'L')]
        if key == 'areola':
            sides.extend(mesh_for(source, binary, f'VH_F_areolar_tubercles_{side}') for side in ('R', 'L'))
        if key == 'lactiferous_ducts':
            sides = [close_duct_tips(*side) for side in sides]
        meshes[key] = concatenate(sides)
        if key == 'nipple':
            for side, (vertices, _) in zip(('right', 'left'), sides, strict=True):
                nipples[side] = ((vertices.min(0) + vertices.max(0)) / 2).round(4).tolist()
    meshes['pectoralis'] = concatenate([pectoralis_layer(side) for side in (1, -1)])
    meshes['chest_wall'] = wall_layer(-22.5, 5)
    beds = [fat_bed_layers(mesh_for(source, binary, f'VH_F_fat_{side}')) for side in ('R', 'L')]
    meshes['deep_fat'], meshes['retromammary_fat'] = map(concatenate, zip(*beds, strict=True))
    return BreastAnatomy(meshes, {
        'mammaryAtlasSha256': MAMMARY_SHA,
        'femaleSkinSha256': FEMALE_SKIN_SHA,
        'femaleSkinSource': FEMALE_SKIN_URL,
        'femaleSkinDoi': 'https://doi.org/10.48539/HBM466.LKPQ.876',
        'coordinateTransform': 'RAS voxel = (-glTF X, glTF Z, glTF Y) * 1000 / voxelMm.',
        'sourceEdits': 'Skin truncated below the regional view. Both native tubercle meshes are grouped with their areola.',
        'ductTopology': 'Exact duplicate vertices welded and 30 small terminal loops per side capped locally for section fill. Source vertices retained. Caps do not join ducts or infer lumen continuity.',
        'nippleCentersVox': nipples,
        'posteriorLayers': 'Authored deep fat, thin retromammary fat, pectoralis and chest-wall teaching layers in the HRA mammary frame.',
    }, AnteriorSurface(*torso))
