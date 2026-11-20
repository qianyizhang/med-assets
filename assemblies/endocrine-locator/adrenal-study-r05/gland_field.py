"""Interpolate the traced gland exterior on the shared 0.6 mm work grid."""

import argparse
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from skimage.measure import euler_number, marching_cubes


def ease(value):
    t = np.clip(value, 0, 1)
    return t * t * (3 - 2 * t)


def reconstruct(mask, origin, step, right):
    filled = ndi.binary_fill_holes(mask)
    signed = (
        np.where(filled, ndi.distance_transform_edt(filled) - 0.5, 0.5 - ndi.distance_transform_edt(~filled))
        * step
    )
    axes = [origin[i] + step * np.arange(n) for i, n in enumerate(mask.shape)]
    x, y, z = np.meshgrid(*axes, indexing="ij", sparse=True)
    specimen_z = axes[2][np.any(mask, axis=(0, 1))]
    # Soften the axial staircase. Use a narrower kernel around the two ends
    # where a single global smoothing length consumed the thin right apex.
    body = ndi.gaussian_filter(signed, np.array([1.45, 1.45, 2.0]) / step)
    endpoint = ndi.gaussian_filter(signed, np.array([0.95, 0.95, 1.25]) / step)
    from_end = np.minimum(z - specimen_z.min(), specimen_z.max() - z)
    alpha = ease((from_end - 1.0) / 5.0)
    field = endpoint * (1 - alpha) + body * alpha
    if right:
        # r02 has two approaching limbs in the lateral half of its inferior
        # axial section. Preserve that open cleft with the narrower field.
        region = ease((-x - 27) / 5) * ease((y - 3) / 5) * ease((-z - 62) / 5)
        field += region * np.minimum(0, endpoint + 0.12 - field)
        # In three neighboring 1.5 mm label planes the limbs turn back
        # around a thin diagonal cleft. Locally recover the measured slot.
        band = 1 - ease((np.abs(x + y + 21.0) - 3.0) / 5.0)
        band = band * ease((y - 1.0) / 4.0) * ease((z + 71.0) / 2.0) * (1 - ease((z + 64.0) / 2.2))
        gap = ndi.gaussian_filter(signed, np.array([0.44, 0.44, 0.64]) / step)
        field += band * np.minimum(0, gap - 0.32 - field)
    # Round off the near-horizontal end-slice contour on both glands.
    # The lowest traced slice is broad in X. Turn the outside of that
    # plateau up while anchoring its middle. The guide comes from this
    # case's lowest occupied 1.5 mm, not the gross specimen photograph.
    inferior = np.argwhere(mask & (z <= specimen_z.min() + 1.5))
    xy = origin[:2] + step * inferior[:, :2]
    center = (xy.min(0) + xy.max(0)) / 2
    radius = np.maximum((xy.max(0) - xy.min(0)) / 2, step)
    spread = np.sqrt(((x - center[0]) / radius[0]) ** 2 + ((y - center[1]) / radius[1]) ** 2)
    if right:
        in_terminal = 1 - ease((np.abs(y - center[1]) - radius[1]) / 7)
        rise = 3.0 * ease(spread / 1.10) * in_terminal
    else:
        rise = 1.15 * ease(spread / 1.25)
    rise = rise * (1 - ease((z - specimen_z.min()) / 8))
    grid = np.indices(mask.shape, dtype=float)
    grid[2] -= rise / step
    field = ndi.map_coordinates(field, grid, order=1, mode="nearest", prefilter=False)
    # Retain the source-supported bulk while capping outward compensation.
    rank = field.size - np.count_nonzero(mask)
    partition = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(partition[rank - 1 : rank + 1].mean(), -0.375, 0.375))
    inside = field > level
    if ndi.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Gland field must have one closed exterior")
    points, faces, _, _ = marching_cubes(
        field, level=level, spacing=(step,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    # Low-frequency local solid fraction provides one continuous palette
    # coordinate. It follows the modeled exterior and carries no tissue label.
    solid_fraction = ndi.gaussian_filter(inside.astype(np.float32), 4.5 / step)
    return {
        "solidFraction": solid_fraction,
        "vertices": (points + origin) / 1000,
        "faces": faces,
        "levelMm": level,
        "terminalCenterMm": center,
        "terminalRadiiMm": radius,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with np.load(args.input, allow_pickle=False) as data:
        result = reconstruct(data["mask"], data["origin"], data["step"].item(), data["right"].item())
    np.savez(args.output, **result)


if __name__ == "__main__":
    main()
