"""Place illustrative right axillary landmarks in the pinned HRA skin frame."""

from dataclasses import dataclass

import numpy as np
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial.transform import Rotation

from breast_anatomy import (
    AnteriorSurface, FEMALE_SKIN, FEMALE_SKIN_SHA, FEMALE_SKIN_URL, mesh_for, select_faces,
)
from build_abdomen import axes
from display_body import atlas
from fit_abdomen import mesh_graph, ramp
from geometry import VOXEL_MM

WINDOW_XZ = (110, 350)
NODE_DEPTH_MM = 16
NODE_RADII_MM = (9.4, 4.2, 4.6)
HILUM_RADII_MM = (7.2, 2.75, 3.0)
MARKER_ANGLE = -.59
START_ROTATION_DEG = -23
ARM_ABDUCTION_DEG = 36


@dataclass
class AxillaAnatomy:
    meshes: dict
    contact: np.ndarray
    basis: np.ndarray
    node: np.ndarray
    receipt: dict


def shell(rings, first, last):
    """Join ordered rings between two end points."""
    size, count = rings.shape[:2]
    points = np.vstack((first, rings.reshape(-1, 3), last))
    strips = np.arange(1, 1 + size * count).reshape(size, count)
    next_ring_index = np.roll(strips, -1, axis=1)
    sides_a = np.stack((strips[:-1], next_ring_index[:-1], strips[1:]), axis=-1)
    sides_b = np.stack((next_ring_index[:-1], next_ring_index[1:], strips[1:]), axis=-1)
    start = np.column_stack((np.zeros(count, dtype=int), next_ring_index[0], strips[0]))
    finish = np.column_stack((strips[-1], next_ring_index[-1], np.full(count, len(points) - 1)))
    faces = np.vstack((start, sides_a.reshape(-1, 3), sides_b.reshape(-1, 3), finish))
    # Orient toward the outside regardless of the coordinate basis handedness.
    triangles = points[faces] - points.mean(axis=0)
    volume = np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum()
    return points, faces if volume > 0 else faces[:, ::-1]


def oval(center, basis, radii, notch_mm=0):
    theta = np.linspace(0, np.pi, 33)[1:-1, None]
    phi = np.linspace(0, 2 * np.pi, 64, endpoint=False)[None, :]
    a, b, c = np.array(radii) / VOXEL_MM
    u = np.broadcast_to(a * np.cos(theta), (len(theta), phi.size))
    v = b * np.sin(theta) * np.cos(phi)
    w = c * np.sin(theta) * np.sin(phi)
    # A slight shallow indentation on the hilar side mimics the reniform outline.
    w -= notch_mm / VOXEL_MM * np.exp(-((u + a * .12) / (a * .43))**2) * np.maximum(np.sin(phi), 0)**8
    v *= 1 - .14 * u / a
    w += .09 * u * (1 - (u / a)**2)
    surface = center + np.stack((u, v, w), axis=-1) @ basis.T
    return shell(surface, center + a * basis[:, 0], center - a * basis[:, 0])


def vessel(contact, basis, offset, half_length, radii, skew):
    """Build a curved local vessel segment with closed section ends."""
    x = np.linspace(-1, 1, 34)[1:-1]
    phi = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    u, v, w = basis.T

    def centers(t):
        return (contact + (np.asarray(t)[..., None] * half_length * u
                + (offset[0] + skew * np.asarray(t)[..., None] + 3 * np.asarray(t)[..., None]**2) * v
                + (offset[1] + 4 * np.asarray(t)[..., None]**2) * w) / VOXEL_MM)

    centerline = centers(x)
    cross_section = (radii[0] * np.cos(phi[:, None]) * v
                     + radii[1] * np.sin(phi[:, None]) * w) / VOXEL_MM
    taper = np.sqrt(1 - x**8)
    return shell(centerline[:, None] + taper[:, None, None] * cross_section, centers(-1), centers(1))


def expose_axilla(vertices, faces, contact):
    """Articulate the atlas right arm while keeping the contact patch native."""
    vertices, vertex_index = np.unique(vertices, axis=0, return_inverse=True)
    faces = vertex_index[faces]
    vertices, faces = select_faces(vertices, faces, np.all(vertices[faces, 2] > 145, axis=1))
    graph = mesh_graph(vertices, faces)
    below_fold = np.flatnonzero(vertices[:, 2] < 239)
    _, labels = connected_components(graph[below_fold][:, below_fold], directed=False)
    regions = [below_fold[labels == i] for i, count in enumerate(np.bincount(labels)) if count > 500]
    if len(regions) != 3:
        raise ValueError('Expected separate atlas arms and trunk below the axillary folds')
    right_arm = max(regions, key=lambda region: np.median(vertices[region, 0]))
    trunk = min(regions, key=lambda region: abs(np.median(vertices[region, 0])))
    from_arm = dijkstra(graph, indices=right_arm, min_only=True)
    from_trunk = dijkstra(graph, indices=trunk, min_only=True)
    finite = np.isfinite(from_arm) & np.isfinite(from_trunk)
    preference = np.subtract(from_trunk, from_arm, out=np.zeros_like(from_arm), where=finite)
    x, _, z = vertices.T
    weight = ramp((preference + 17) / 67) * ramp((x - 78) / 44) * ramp((425 - z) / 65)
    weight[right_arm] = 1
    weight[trunk] = 0
    weight *= ramp((np.linalg.norm(vertices - contact, axis=1) - 18) / 30)
    moving = weight > 0
    pivot = np.array([137, -55, 359])
    rotation = np.deg2rad([8, -ARM_ABDUCTION_DEG, 0]) * weight[moving, None]
    posed = vertices.copy()
    posed[moving] = Rotation.from_rotvec(rotation).apply(vertices[moving] - pivot) + pivot
    return posed, faces


def load_anatomy(skin_path=FEMALE_SKIN):
    document, binary = atlas(skin_path, FEMALE_SKIN_SHA)
    skin_points, skin_faces = mesh_for(document, binary, 'VH_F_skin')
    native_torso = select_faces(skin_points, skin_faces, np.all(skin_points[skin_faces, 2] > 220, axis=1))
    skin = AnteriorSurface(*native_torso)
    x, z = WINDOW_XZ
    contact = skin.contact(x, z)
    x_slope = (skin.contact(x + .4, z)[1] - skin.contact(x - .4, z)[1]) / .8
    z_slope = (skin.contact(x, z + .4)[1] - skin.contact(x, z - .4)[1]) / .8
    basis = axes([-x_slope, 1, -z_slope], [np.cos(MARKER_ANGLE), 0, np.sin(MARKER_ANGLE)])
    torso = expose_axilla(skin_points, skin_faces, contact)
    long_axis, cross_axis, beam = basis.T
    node = contact + NODE_DEPTH_MM / VOXEL_MM * beam
    muscle_center = contact + (46 * beam + 16 * cross_axis) / VOXEL_MM
    muscle_basis = np.column_stack((long_axis, cross_axis, beam))
    meshes = {
        'torso': torso,
        'axillary_node': oval(node, basis, NODE_RADII_MM, notch_mm=.97),
        'fatty_hilum': oval(node + .35 / VOXEL_MM * beam, basis, HILUM_RADII_MM, notch_mm=.38),
        'axillary_vein': vessel(contact, basis, (-1.8, 28.5), 42, (4.5, 2.7), -5),
        'axillary_artery': vessel(contact, basis, (2.4, 37.5), 45, (3.1, 3.1), 8),
        'axillary_muscle': oval(muscle_center, muscle_basis, (50, 20, 7)),
    }
    return AxillaAnatomy(meshes, contact, basis, node, {
        'femaleSkinSha256': FEMALE_SKIN_SHA,
        'femaleSkinSource': FEMALE_SKIN_URL,
        'femaleSkinDoi': 'https://doi.org/10.48539/HBM466.LKPQ.876',
        'coordinateFrame': 'HRA skin native glTF transformed to 1.5 mm RAS voxels',
        'sourceEdits': 'The right HRA upper arm is posed outward for access, with the native probe-contact '
                       'patch held fixed. The node, hilum, vessels and muscle are authored in the right anterior fold.',
        'rightArmAbductionFromAtlasDeg': ARM_ABDUCTION_DEG,
        'morphologySources': [
            'https://pmc.ncbi.nlm.nih.gov/articles/PMC8724375/',
            'https://pmc.ncbi.nlm.nih.gov/articles/PMC10175532/',
            'https://doi.org/10.1002/jmrs.840',
        ],
        'nodeOuterDiametersMm': [2 * size for size in NODE_RADII_MM],
        'hilumDiametersMm': [2 * size for size in HILUM_RADII_MM],
        'nodeCenterDepthMm': NODE_DEPTH_MM,
        'nodeCenterVox': node.round(6).tolist(),
        'nodeLongAxisRas': long_axis.round(6).tolist(),
    })
