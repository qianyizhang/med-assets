"""Reconstruct a smooth exterior using a signed field on the sampled mesh grid."""

import argparse
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from skimage.measure import euler_number, marching_cubes


def ball(radius):
    x, y, z = np.ogrid[-radius:radius + 1, -radius:radius + 1, -radius:radius + 1]
    return (x*x + y*y + z*z) <= radius*radius


def signed_grid(mask):
    inside = ndi.distance_transform_edt(mask)
    outside = ndi.distance_transform_edt(~mask)
    return np.where(mask, inside - 0.5, 0.5 - outside)


def exterior(mask, points_mm, step_mm, sigma_mm, max_close_mm):
    """Use the smallest tested local closure that yields a single genus-zero exterior."""
    target_voxel_count = np.count_nonzero(mask)
    for radius in range(round(max_close_mm / step_mm) + 1):
        closed = ndi.binary_closing(mask, structure=ball(radius)) if radius else mask
        # Fill sealed cavities after local closure. Broad open concavities remain open.
        filled = ndi.binary_fill_holes(closed)
        smooth = ndi.gaussian_filter(signed_grid(filled), sigma=sigma_mm / step_mm)
        # Match the sampled interior count to counter smoothing erosion.
        # Cap compensation to a quarter of the original 1.5 mm mask spacing.
        rank = smooth.size - target_voxel_count
        partitioned = np.partition(smooth.ravel(), (rank - 1, rank))
        level = float(np.clip(partitioned[rank - 1:rank + 1].mean(), -0.375 / step_mm, 0.375 / step_mm))
        inside = smooth > level
        if ndi.label(inside)[1] == 1 and euler_number(inside, connectivity=1) == 1:
            break
    else:
        raise ValueError(f"No single genus-zero exterior up to {max_close_mm} mm closing radius")
    verts, faces, _, _ = marching_cubes(
        smooth, level=level, spacing=(step_mm,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    return {
        "vertices": (verts + points_mm) / 1000,
        "faces": faces,
        "closingRadiusMm": radius * step_mm,
        "gaussianSigmaMm": sigma_mm,
        "measuredInputInteriorVoxels": target_voxel_count,
        "workGridEulerBeforeSmoothing": euler_number(mask, connectivity=1),
        "isoValueShiftMm": level * step_mm,
        "measuredOutputInteriorVoxels": np.count_nonzero(inside),
        "addedVoxelsBeforeSmoothing": np.count_nonzero(filled & ~mask),
        "removedVoxelsBeforeSmoothing": np.count_nonzero(mask & ~filled),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with np.load(args.source, allow_pickle=False) as supplied:
        rebuilt = exterior(supplied["mask"], supplied["points_mm"], supplied["step_mm"].item(),
                           supplied["sigma_mm"].item(), supplied["max_close_mm"].item())
    np.savez(args.output, **rebuilt)


if __name__ == "__main__":
    main()
