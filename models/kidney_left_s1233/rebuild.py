"""Rebuild the s1233 left kidney in its original voxel-index frame."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from scipy import ndimage
from skimage.measure import euler_number, marching_cubes

HERE = Path(__file__).resolve().parent
MASK_SHA = "e0c7e53f00a20cedbe3e13d687ffc6d5e03a33824d4e4c7124f25335179b794e"
STEP_MM = 0.6
SOURCE_MM = 1.5


def ease(value):
    t = np.clip(value, 0, 1)
    return t**2 * (3 - 2 * t)


def reconstruct(mask):
    occupied = np.column_stack(np.nonzero(mask))
    lower, upper = occupied.min(axis=0) - 6, occupied.max(axis=0) + 7
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    # The pinned label is one solid component with no enclosed cavity.
    clean = cropped.astype(bool)
    ratio = STEP_MM / SOURCE_MM
    size = tuple(np.ceil((np.array(clean.shape) - 1) / ratio).astype(int) + 1)
    fine = (
        ndimage.affine_transform(
            clean.astype(np.float32), np.eye(3) * ratio, output_shape=size, order=1
        )
        >= 0.5
    )
    signed = (
        np.where(
            fine,
            ndimage.distance_transform_edt(fine) - 0.5,
            0.5 - ndimage.distance_transform_edt(~fine),
        )
        * STEP_MM
    )
    x, y, z = [axis * STEP_MM for axis in np.indices(size, sparse=True)]
    source = np.column_stack(np.nonzero(clean)) * SOURCE_MM
    bottom, top = source[:, 2].min(), source[:, 2].max()
    center_z = (bottom + top) / 2
    center_x = np.median(source[:, 0])
    center_y = np.median(source[:, 1])
    # The medial concavity faces increasing RAS x. Blend into the narrower
    # filter in the medial middle third and within 7 mm of either pole.
    medial = ease((x - center_x + 2) / 13)
    hilum = (
        medial
        * (1 - ease((abs(z - center_z) - 10) / 15))
        * (1 - ease((abs(y - center_y) - 13) / 10))
    )
    pole = 1 - ease((np.minimum(z - bottom, top - z) - 1) / 7)
    protect = np.maximum(hilum, pole)
    broad = ndimage.gaussian_filter(signed, np.array([1.45, 1.45, 1.95]) / STEP_MM)
    narrow = ndimage.gaussian_filter(signed, np.array([0.95, 0.95, 1.20]) / STEP_MM)
    field = broad + protect * (narrow - broad)
    # Round the outer edge of each terminal plateau in field space.
    taper = np.zeros_like(field)
    for end, inward in ((bottom, 1), (top, -1)):
        cap = source[np.abs(source[:, 2] - end) <= SOURCE_MM, :2]
        center = (cap.min(0) + cap.max(0)) / 2
        radius = np.maximum((cap.max(0) - cap.min(0)) / 2, SOURCE_MM)
        spread = np.hypot((x - center[0]) / radius[0], (y - center[1]) / radius[1])
        taper += 0.3 * ease(spread) * (1 - ease((z - end) * inward / 3))
    field -= taper

    # Enclose the cleaned native label volume on the finer grid.
    count = round(np.count_nonzero(clean) * (SOURCE_MM / STEP_MM) ** 3)
    rank = field.size - count
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(ordered[rank - 1 : rank + 1].mean(), -0.45, 0.45))
    inside = field > level
    if ndimage.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Smoothed field must enclose one kidney without tunnels")
    points, faces, _, _ = marching_cubes(
        field, level, spacing=(STEP_MM,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    ras = points + lower * SOURCE_MM + AFFINE[:3, 3]
    a, b, c = (ras[faces] - ras.mean(0)).transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return ras, faces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="Fresh replay directory")
    parser.add_argument("--blender", required=True, type=Path)
    args = parser.parse_args()
    mask = volume(args.case / "segmentations/kidney_left.nii.gz", MASK_SHA, "u1")
    points, faces = reconstruct(mask)
    args.work.mkdir(parents=True)
    surface = args.work / "smooth.npz"
    export = args.work / "kidney-left.mesh"
    np.savez(surface, vertices=points, faces=faces, affine=AFFINE)
    subprocess.run(
        [
            str(args.blender),
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--python-exit-code",
            "1",
            "--python",
            str(HERE / "retopology.py"),
            "--",
            str(surface),
            str(export),
        ],
        check=True,
    )
    payload = export.read_bytes()
    record = HERE / "asset.record.json"
    pin = json.loads(record.read_text())["revisions"][0]["exports"][0]
    if len(payload) != pin["bytes"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
        raise ValueError("Replayed kidney differs from the r01 identity")
    print(f"{hashlib.sha256(payload).hexdigest()}  {len(payload)} bytes  {export}")


if __name__ == "__main__":
    main()
