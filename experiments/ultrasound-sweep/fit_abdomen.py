"""Fit the illustrative atlas to abdominal contact windows in the s1233 CT."""

import numpy as np
from scipy import ndimage as nd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from geometry import VOXEL_MM

CONTACT_TOLERANCE_MM = 1
ARM_EXTENSION_DEGREES = 25
ARM_ABDUCTION_DEGREES = 20


def ramp(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def mesh_graph(vertices, faces):
    edges = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    start, end = np.unique(np.r_[edges, edges[:, ::-1]], axis=0).T
    lengths = np.linalg.norm(vertices[start] - vertices[end], axis=1)
    return csr_matrix((lengths, (start, end)), shape=(len(vertices), len(vertices)))


def open_flanks(vertices, faces):
    """Move the atlas arms slightly back and out, preserving distal arm geometry."""
    graph = mesh_graph(vertices, faces)
    below_axilla = np.flatnonzero(vertices[:, 2] < 250)
    _, cut = connected_components(graph[below_axilla][:, below_axilla], directed=False)
    groups = [below_axilla[cut == i] for i, count in enumerate(np.bincount(cut)) if count > 100]
    trunk = np.concatenate([group for group in groups if len(group) > 20_000])
    collar = trunk[vertices[trunk, 2] >= 220]
    from_torso = dijkstra(graph, indices=collar, min_only=True, limit=56)
    result = vertices.copy()
    shoulder_weight = np.zeros(len(vertices))
    for side in (-1, 1):
        # The atlas includes a thin inner shell and both surfaces must follow the arm.
        distal = [group for group in groups if side * (np.median(vertices[group, 0]) - 152) > 120]
        if len(distal) != 2:
            raise ValueError('Could not isolate both atlas arm surfaces below the shoulder.')
        arm = np.concatenate(distal)
        upper = arm[vertices[arm, 2] >= 235]
        # Use a common pivot for both skin surfaces. The upper arm centroid sets the
        # lateral and posterior position. The pivot height lies above the axilla.
        pivot = np.r_[vertices[upper, :2].mean(0) - [side * 14, 0], 282]
        distance = dijkstra(graph, indices=upper, min_only=True, limit=95)
        weight = (1 - ramp(distance / 95)) * ramp(from_torso / 56)
        weight[arm] = 1
        shoulder_weight = np.maximum(weight, shoulder_weight)
        move = weight > 0
        angle = np.deg2rad([-ARM_EXTENSION_DEGREES, -side * ARM_ABDUCTION_DEGREES, 0])
        rotvec = weight[move, None] * angle
        result[move] = Rotation.from_rotvec(rotvec).apply(vertices[move] - pivot) + pivot
    return result, shoulder_weight


def surface_height(shell, axis, side):
    """Sample the outermost CT shell crossing along a signed case axis."""
    depth_first = np.moveaxis(shell, axis, 0)
    if side == -1:
        depth_first = depth_first[::-1]
    index = np.arange(depth_first.shape[0])[:, None, None]
    inside = np.where(depth_first > .5, index, -1).max(0)
    before = np.take_along_axis(depth_first, np.maximum(inside, 0)[None], axis=0)[0]
    after = np.take_along_axis(depth_first, np.minimum(inside + 1, len(depth_first) - 1)[None], axis=0)[0]
    valid = (inside >= 0) & (inside < len(depth_first) - 1) & (before > after)
    fraction = np.divide(before - .5, before - after, where=valid, out=np.zeros_like(before))
    height = inside + fraction
    if side == -1:
        height = len(depth_first) - 1 - height
    return np.where(valid, height * 2, np.nan)


def fit_window(vertices, shell, contacts, beams, arm_weight, axis=None):
    """Conform a bounded front or flank patch to the sampled CT exterior."""
    outward = -beams.mean(0)
    if axis is None:
        axis = int(np.argmax(np.abs(outward)))
    side = int(np.sign(outward[axis]))
    tangent = [coordinate for coordinate in range(3) if coordinate != axis]
    projected = vertices[:, tangent]
    dist, _ = cKDTree(contacts[:, tangent]).query(projected)
    weight = 1 - ramp((dist - 26) / (73 - 26))
    # Confine conformance to the intended external sheet. The opposite trunk wall
    # and abducted upper arm must remain part of their own surfaces.
    exterior = side * (vertices[:, axis] - contacts[:, axis].mean())
    weight *= ramp((exterior + 65) / 29)
    weight *= 1 - ramp(arm_weight * 3)
    roi = np.flatnonzero(weight > 0)
    heights = nd.map_coordinates(surface_height(shell, axis, side), projected[roi].T / 2,
                                 order=1, mode='constant', cval=np.nan, prefilter=False)
    valid = np.isfinite(heights)
    result = vertices.copy()
    i = roi[valid]
    result[i, axis] += weight[i] * (heights[valid] - result[i, axis])
    return result


def outer_contact_offsets(vertices, faces, contacts, beams):
    """Return first intersections of incoming rays with the whole exterior."""
    triangles = vertices[faces]
    a, b, c = triangles.transpose(1, 0, 2)
    ab, ac = b - a, c - a
    centers = triangles.mean(axis=1)
    radii = np.max(np.linalg.norm(triangles - centers[:, None, :], axis=2), axis=1)
    offsets = []
    for contact, beam in zip(contacts, beams, strict=True):
        diff = centers - contact
        along = np.einsum('ij,j->i', diff, beam)
        near = (np.linalg.norm(diff - along[:, None] * beam, axis=1) <= radii + 1e-6)
        idx = np.flatnonzero(near)
        h = np.cross(beam, ac[idx])
        det = np.einsum('ij,ij->i', ab[idx], h)
        valid = np.abs(det) > 1e-10
        idx, h, det = idx[valid], h[valid], det[valid]
        offset = contact - a[idx]
        cross = np.cross(offset, ab[idx])
        u = np.einsum('ij,ij->i', offset, h) / det
        v = np.einsum('ij,j->i', cross, beam) / det
        distances = np.einsum('ij,ij->i', ac[idx], cross) / det
        hits = distances[(u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8)]
        if not hits.size:
            raise ValueError('Incoming probe ray misses the exterior.')
        offsets.append(hits.min() * VOXEL_MM)
    return np.array(offsets)


def max_outer_error(vertices, faces, contacts, beams):
    offsets = outer_contact_offsets(vertices, faces, contacts, beams)
    return float(np.max(np.abs(offsets)))
