"""Resample a breast plate after illustrative displacement under the probe face."""

import numpy as np

# Keep this matched to the scan-plane displacement in scene.js.
SETTLE_DEPTH_MM = 30.0


def smoothstep(fraction):
    t = np.clip(fraction, 0, 1)
    return t * t * (3 - 2 * t)


def contact_rows(rig, lateral, depth, *, pressure=0):
    """Invert the same axial displacement used to seat the displayed anatomy."""
    elevation = np.asarray(rig['elevationMm'])
    if elevation[len(elevation) // 2] != 0:
        raise ValueError('Contact rig requires a centered elevation row')
    surface = np.interp(lateral, rig['lateralMm'], rig['surfaceMm'][len(elevation) // 2])
    footprint = 1 - smoothstep((abs(lateral) - rig['faceWidthMm'] / 2) / rig['featherMm'])
    shift = np.maximum(pressure - surface, 0) * footprint
    display = depth[:, None] + pressure
    low = display - abs(shift)
    high = display + abs(shift)
    for _ in range(23):
        middle = (low + high) / 2
        mapped = middle + shift * (1 - smoothstep((middle - surface) / rig['settleDepthMm']))
        below = mapped < display
        low, high = np.where(below, middle, low), np.where(below, high, middle)
    return (low + high) / 2


def sample_contact_plate(image, native_depth, native_rows, *, order, field):
    from scipy.ndimage import map_coordinates

    ix = np.broadcast_to(np.arange(len(native_rows[0])), native_rows.shape)
    rows = (native_rows - native_depth[0]) / (native_depth[1] - native_depth[0])
    return np.where(field, map_coordinates(image, (rows, ix), order=order), 0)


def refine_contact_skin(vertices, faces, contact, *, radius=43):
    """Tessellate the native triangles for a smooth GPU displacement at the lens."""
    split_patterns = (
        ((0, 1, 2),),
        ((0, 3, 2), (3, 1, 2)),
        ((1, 4, 0), (4, 2, 0)),
        ((0, 3, 2), (3, 4, 2), (3, 1, 4)),
        ((2, 5, 1), (5, 0, 1)),
        ((2, 5, 1), (5, 3, 1), (5, 0, 3)),
        ((1, 4, 0), (4, 5, 0), (4, 2, 5)),
        ((0, 3, 5), (3, 1, 4), (5, 4, 2), (3, 4, 5)),
    )
    for _ in range(2):
        local = np.linalg.norm(vertices[faces].mean(1) - contact, axis=1) < radius
        edges = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
        unique, inverse = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True)
        face_edges = inverse.reshape(-1, 3)
        marked = np.unique(face_edges[local])
        midpoints = np.full(len(unique), -1)
        midpoints[marked] = np.arange(len(marked)) + len(vertices)
        # Split neighboring triangles on the same edge to avoid T junctions.
        mids = midpoints[face_edges]
        modes = (mids >= 0) @ np.array([1, 2, 4])
        ids = np.column_stack((faces, mids))
        vertices = np.concatenate((vertices, vertices[unique[marked]].mean(axis=1)))
        faces = np.concatenate([ids[modes == mode][:, pattern].reshape(-1, 3)
                                for mode, pattern in enumerate(split_patterns)])
    return vertices, faces
