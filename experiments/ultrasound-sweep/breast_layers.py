"""Illustrative mixed stroma around retained HRA lobes, in the shared RAS frame."""

import numpy as np
from scipy import ndimage as nd

from breast_anatomy import AnteriorSurface, closed_layer, grid_triangles


def organ_heights(mesh, x, z):
    surface = AnteriorSurface(*mesh)
    crossings = [surface.extrema(a, b) for a, b in zip(x.ravel(), z.ravel(), strict=True)]
    heights = np.array([crossing if crossing is not None else (np.nan, np.nan) for crossing in crossings])
    return heights.reshape(*x.shape, 2)


def layered_stroma(anatomy):
    """Loft a mantle around observed lobes, preserving the exact source meshes.

    The mantle represents mixed fibroglandular stroma outside separately
    retained lobules. It is an authored volume, constrained by the native
    lobular footprint, the skin, and the native fat envelope.
    """
    vertices, faces = anatomy.meshes['mammary_lobes']
    right = (vertices[faces, 0] > 0).all(axis=1)
    vertices_used = vertices[np.unique(faces[right])]
    xy_min = vertices_used[:, [0, 2]].min(0) - 6
    xy_max = vertices_used[:, [0, 2]].max(0) + 6
    pitch = 1.5
    x, z = np.meshgrid(np.arange(xy_min[0], xy_max[0] + pitch, pitch),
                       np.arange(xy_min[1], xy_max[1] + pitch, pitch), indexing='ij')
    lobes = organ_heights((vertices, faces[right]), x, z)
    fat = organ_heights(anatomy.meshes['breast_fat'], x, z)
    supported = np.isfinite(lobes[..., 0])
    distance, nearest = nd.distance_transform_edt(~supported, sampling=pitch, return_indices=True)
    expanded = nd.binary_fill_holes(nd.binary_closing(supported, iterations=2))
    permitted = (distance < 6) & (expanded | (distance < 3.5)) & np.isfinite(fat[..., 0])
    depth = nd.gaussian_filter(lobes[tuple(nearest)].mean(axis=-1), 1.6)
    spread = nd.gaussian_filter(np.ptp(lobes[tuple(nearest)], axis=-1), 1.35)
    taper = np.clip(1 - distance / 6, .15, 1)
    half = (1.9 + .45 * spread) * (.62 + .38 * taper)
    front_y = np.minimum(depth + half, fat[..., 1] - 2.6)
    back_y = np.maximum(depth - half, fat[..., 0] + 1.0)
    present = permitted & (front_y > back_y + .45)
    included = grid_triangles(x.shape, present)
    if not len(included):
        raise ValueError('No continuous stroma footprint within the HRA fat envelope')
    # Invalid columns are outside all emitted triangles.
    front = np.column_stack((x.ravel(), np.nan_to_num(front_y).ravel(), z.ravel()))
    back = np.column_stack((x.ravel(), np.nan_to_num(back_y).ravel(), z.ravel()))
    return closed_layer(front, back, included)


def survey_fat_layers(anatomy):
    """Continue the right fat bed around the pectoral margin without a slab cut."""
    from breast_anatomy import PECTORAL_INFERIOR, PECTORAL_SUPERIOR, PECTORAL_WIDTH, select_faces, wall_front

    vertices, faces = anatomy.meshes['breast_fat']
    right = (vertices[faces, 0] > 0).all(axis=1)
    native = vertices[np.unique(faces[right])]
    corner = native[:, [0, 2]]
    lo, hi = np.floor(corner.min(0)), np.ceil(corner.max(0))
    x, z = np.meshgrid(np.arange(lo[0], hi[0] + 1, 1.35), np.arange(lo[1], hi[1] + 1, 1.35), indexing='ij')
    fat = organ_heights((vertices, faces[right]), x, z)
    observed = np.isfinite(fat[..., 0])
    within = nd.binary_fill_holes(nd.binary_closing(observed, iterations=2))
    near, lookup = nd.distance_transform_edt(~observed, sampling=1.35, return_indices=True)
    skin = organ_heights(anatomy.meshes['torso'], x, z)
    # A small sampled continuation maintains the shape in uneven source-edge
    # areas. Bound every newly authored column to the female skin.
    usable = (within | (near < 2.25)) & np.isfinite(skin[..., 0])
    posterior = fat[..., 0][tuple(lookup)]
    derived = nd.gaussian_filter(posterior, 1.15)
    signed_pectoral = np.minimum.reduce((
        x - PECTORAL_WIDTH[0], PECTORAL_WIDTH[-1] - x,
        z - PECTORAL_INFERIOR(x), PECTORAL_SUPERIOR(x) - z,
    ))
    influence = nd.gaussian_filter(np.clip((signed_pectoral + 4) / 8, 0, 1), 1.15)
    fascia = wall_front(-15, x, z)
    rear = np.maximum(fascia - (1 - influence) * 3, skin[..., 0] + 2)
    front = np.minimum(np.maximum(posterior, derived) + .55, skin[..., 1] - 1.0)
    usable &= front > rear + .65
    # Close over the sternocostal margins continuously. Keep the thin labeled
    # retromammary portion immediately anterior to modeled pectoralis.
    retro = np.minimum((front - rear) * .32, 2.8) * np.clip(signed_pectoral / 7, 0, 1)
    retro = np.where((retro > .12) & usable, retro, 0)
    upper, middle, lower = (
        np.column_stack((x.ravel(), np.nan_to_num(y).ravel(), z.ravel()))
        for y in (front, rear + retro, rear)
    )
    right_deep = closed_layer(upper, middle, grid_triangles(x.shape, usable))
    right_retro = closed_layer(middle, lower, grid_triangles(x.shape, retro > .12))

    def retain_left(right_mesh, name):
        from breast_anatomy import concatenate

        v, f = anatomy.meshes[name]
        left = select_faces(v, f, (v[f, 0] < 0).all(axis=1))
        return concatenate((right_mesh, left))

    return retain_left(right_deep, 'deep_fat'), retain_left(right_retro, 'retromammary_fat')
