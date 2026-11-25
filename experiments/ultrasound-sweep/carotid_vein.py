"""Trace the visible right cervical venous lumen in TotalSegmentator case s1127."""

import numpy as np
from scipy import ndimage as nd
from skimage.draw import polygon

# Reviewed native axial locations, following the contrast column cranially from
# the right brachiocephalic confluence. Coordinates are indices on the s1127 CT.
SEEDS = np.array([
    (375, 152.7, 128.6), (379, 150.3, 128.9), (383, 149.1, 128.2),
    (387, 147.9, 127.8), (391, 148.1, 128.6), (395, 149.4, 128.6),
    (399, 150.7, 128.9), (403, 151.6, 128.7), (408, 152.7, 129.4),
])


def right_jugular(ct, cca):
    """Sample the contrast boundary along rays; leave other vessels and slices unlabelled."""
    levels = np.arange(int(SEEDS[0, 0]), int(SEEDS[-1, 0]) + 1)
    centers = np.stack([np.interp(levels, SEEDS[:, 0], SEEDS[:, i]) for i in (1, 2)], axis=1)
    angles = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    directions = np.stack((np.cos(angles), np.sin(angles)))
    radii = np.arange(0, 8.1, .125)  # Native 1.5 mm voxels.
    edges = []
    for z, center in zip(levels, centers, strict=True):
        crop = ct[136:166, 117:142, z].astype(float)
        xy = (center - [136, 117])[:, None, None] + directions[:, :, None] * radii
        hu = nd.map_coordinates(nd.gaussian_filter(crop, .55), xy, order=1, mode='nearest')
        # Seek the strongest descending boundary of the bright venous column.
        # The seed limits prevent a lateral tributary or adjacent opacified
        # artery from becoming the outer contour when their borders touch.
        score = -np.gradient(hu, radii, axis=1) - 1.6 * (radii - 4.7) ** 2
        eligible = (radii >= 2.1) & (radii <= 7)
        edges.append(radii[eligible][score[:, eligible].argmax(axis=1)])
    edges = nd.median_filter(np.pad(edges, ((1, 1), (0, 0)), mode='edge'),
                             size=(3, 5), mode='wrap')[1:-1]
    edges = nd.gaussian_filter(edges, (.55, 1.0), mode=('nearest', 'wrap'))
    vein = np.zeros_like(cca, dtype='u1')
    for z, center, radius in zip(levels, centers, edges, strict=True):
        ring = center[:, None] + directions * radius
        x, y = polygon(*ring, shape=ct.shape[:2])
        vein[x, y, z] = 1
    if np.any(vein & cca):
        raise ValueError('Traced jugular contour crosses the source carotid segmentation')
    return vein
