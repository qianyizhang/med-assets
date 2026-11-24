"""An illustrative spatial scatter model for normal breast fat. Coordinates are atlas RAS voxels."""

from functools import cache

import numpy as np
from scipy.spatial import cKDTree

from geometry import VOXEL_MM


@cache
def fat_lobules():
    """A persistent distribution of scatter compartments in material coordinates."""
    cells = np.stack(np.meshgrid(np.arange(-9, 10), np.arange(-10, 11), np.arange(-15, 14),
                                 indexing='ij'), axis=-1).reshape(-1, 3)
    rng = np.random.default_rng(306)
    return cKDTree(cells + rng.uniform(-.41, .41, cells.shape))


def septal_echo(xyz, broad):
    """Fine sloping septa between flattened fat lobules, sampled in the same 3D frame at every pose."""
    x, y, z = xyz
    x = (x - 76.93) * VOXEL_MM
    y = (y - 57.27) * VOXEL_MM
    z = (z - 261.50) * VOXEL_MM
    across = .93 * x - .37 * y
    normal = .37 * x + .93 * y - .09 * z
    undulation = 1.1 * np.sin(z / 5.8 + across / 5) + .76 * np.cos(across / 4.2 - normal / 5.5)
    local = np.stack((across / 10.5, z / 9,
                      (normal + .005 * across**2 + .004 * z**2 + undulation) / 3.4), axis=-1)
    tree = fat_lobules()
    dist, indices = tree.query(local, k=2)
    delta = tree.data[indices[..., 1]] - tree.data[indices[..., 0]]
    # Strongest reflections from septa whose normals point toward the near surface.
    orientation = np.abs(delta[..., 2]) / np.maximum(.1, np.linalg.norm(delta, axis=-1))
    boundary = np.exp(-((dist[..., 1] - dist[..., 0]) / .10) ** 2)
    return boundary * (.14 + .86 * orientation) * np.clip(.88 + .45 * broad, .3, 1.3)
