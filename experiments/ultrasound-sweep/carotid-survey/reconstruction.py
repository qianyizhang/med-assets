"""Reconstruct a physical voxel field using only tracked binary section plates."""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.measure import marching_cubes


def raster_grid(view):
    pitch = view['mmPerPx']
    col, row = view['centerPx']
    return ((np.arange(view['widthPx']) - col) * pitch,
            (np.arange(view['heightPx']) - row) * pitch)


def world_to_pixel(view, points):
    delta = points - np.asarray(view['contact'])
    return np.stack([np.einsum('...i,i->...', delta, view['width']),
                     np.einsum('...i,i->...', delta, view['beam'])], axis=-1) / view['mmPerPx'] + view['centerPx']


def plane_to_world(view, points):
    delta = (np.asarray(points) - view['centerPx']) * view['mmPerPx']
    return (np.asarray(view['contact']) + delta[..., :1] * np.asarray(view['width'])
            + delta[..., 1:] * np.asarray(view['beam']))


def read_mask(root, view):
    path = Path(root) / view['lumenMaskPath']
    with Image.open(path) as image:
        return np.asarray(image.convert('L')) >= 128


def physical_bounds(views, root, pitch):
    corners = []
    for view in views:
        rows, cols = np.nonzero(read_mask(root, view))
        if len(rows):
            corners.append(plane_to_world(view, np.array([[c, r] for c in (cols.min(), cols.max())
                                                         for r in (rows.min(), rows.max())])))
    if not corners:
        raise ValueError('No observed arterial pixels to reconstruct')
    points = np.concatenate(corners)
    lower = np.floor(points.min(0) / pitch) * pitch - 2 * pitch
    upper = np.ceil(points.max(0) / pitch) * pitch + 2 * pitch
    return [np.arange(a, b + pitch * .5, pitch) for a, b in zip(lower, upper, strict=True)]


def signed_field(mask, pitch):
    return (nd.distance_transform_edt(mask) - nd.distance_transform_edt(~mask)) * pitch


def reconstruct(views, root, pitch=.55):
    """Resample acquired planes in world space and interpolate their signed masks.

    This implementation is for the parallel transverse acquisition. The only
    inputs are tracked plate metadata and emitted mask bytes. Output closes at
    observed acquisition bounds and does not extrapolate beyond either end.
    """
    if len(views) < 3:
        raise ValueError('A tracked artery stack requires at least three observations')
    z = np.array([frame['contact'][2] for frame in views])
    if np.any(np.diff(z) <= 0) or not all(
        abs(view['width'][2]) < 1e-8 and abs(view['beam'][2]) < 1e-8
        and np.allclose(np.asarray([view['width'], view['beam']]) @ np.asarray([view['width'], view['beam']]).T, np.eye(2))
        for view in views
    ):
        raise ValueError('Tracked transverse reconstruction requires ordered parallel RAS sections')
    axes = physical_bounds(views, root, pitch)
    x, y, zz = axes
    xx, yy = np.meshgrid(x, y, indexing='ij')
    points = np.stack([xx, yy, np.zeros_like(xx)], axis=-1)
    planes = []
    coverage = []
    for view in views:
        mask = read_mask(root, view)
        coordinates = world_to_pixel(view, points)
        col, row = coordinates.transpose(2, 0, 1)
        field = signed_field(mask, view['mmPerPx'])
        planes.append(nd.map_coordinates(field, [row, col], order=1, mode='constant', cval=-2))
        coverage.append((row >= 0) & (row < view['heightPx'] - 1)
                        & (col >= 0) & (col < view['widthPx'] - 1))
    fields = np.asarray(planes)
    coverage = np.asarray(coverage)
    volume = np.full((len(x), len(y), len(zz)), -pitch, dtype='f4')
    inside = (zz >= z[0]) & (zz <= z[-1])
    index = np.clip(np.searchsorted(z, zz[inside], side='right') - 1, 0, len(z) - 2)
    fraction = ((zz[inside] - z[index]) / (z[index + 1] - z[index]))[:, None, None]
    estimate = fields[index] * (1 - fraction) + fields[index + 1] * fraction
    known = coverage[index] & coverage[index + 1]
    volume[..., inside] = np.where(known, estimate, -pitch).transpose(1, 2, 0)
    vertices, faces, _, _ = marching_cubes(volume, 0, spacing=(pitch,) * 3)
    vertices += [axis[0] for axis in axes]
    return (vertices, faces[:, ::-1]), volume, axes


def agreement(volume, axes, reference_plane, levels):
    """Check geometry against independently sampled planes between observations."""
    x, y, z = axes
    uu, vv = np.meshgrid(x, y, indexing='ij')
    scores = []
    observed_heights = []
    reference_area = 0
    intersection_area = 0
    for height in levels:
        reference = reference_plane(x, y, height)
        if not reference.any():
            continue
        az = np.full_like(uu, (height - z[0]) / (z[1] - z[0]))
        indices = np.indices(uu.shape)
        estimate = nd.map_coordinates(volume, [indices[0], indices[1], az], order=1) > 0
        overlap = np.count_nonzero(reference & estimate)
        union = np.count_nonzero(reference | estimate)
        reference_area += np.count_nonzero(reference)
        intersection_area += overlap
        scores.append(overlap / union)
        observed_heights.append(float(height))
    if not scores:
        raise ValueError('No supported held-out source planes')
    return {'heldOutPlanes': len(scores), 'medianIoU': round(float(np.median(scores)), 3),
            'minimumIoU': round(float(min(scores)), 3),
            'minimumIoULevelMm': round(observed_heights[int(np.argmin(scores))], 2),
            'heldOutIoUAboveHalfFraction': round(float(np.mean(np.asarray(scores) >= .5)), 3),
            'sourceMaskRecallWithinAcquiredSlab': round(intersection_area / reference_area, 3)}
