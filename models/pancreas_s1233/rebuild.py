"""Rebuild the s1233 pancreas in its original voxel-index frame."""

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
MASK_SHA = "9f11083652d059e85514d419c90124911953dbbce2018ccc549eaa2c73b0968b"
STEP_MM = 0.6
SOURCE_MM = 1.5


def ease(value):
    t = np.clip(value, 0, 1)
    return t**2 * (3 - 2 * t)


def reconstruct(mask):
    points = np.column_stack(np.nonzero(mask))
    lower, upper = points.min(axis=0) - 6, points.max(axis=0) + 7
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    # Three enclosed label gaps near the pancreatic body are
    # absent from this whole-gland exterior. The raw comparison retains them.
    cropped = ndimage.binary_fill_holes(cropped)
    ratio = STEP_MM / SOURCE_MM
    size = tuple(np.ceil((np.array(cropped.shape) - 1) / ratio).astype(int) + 1)
    fine = (
        ndimage.affine_transform(
            cropped.astype(np.float32), np.eye(3) * ratio, output_shape=size, order=1
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
    x, _, z = [
        axis * STEP_MM + offset
        for axis, offset in zip(
            np.indices(size, sparse=True), lower * SOURCE_MM + AFFINE[:3, 3], strict=True
        )
    ]
    # Preserve the neck and upper tail with a tight kernel. The lower
    # near-tangent uncinate turn needs the same local protection.
    protect = np.maximum(ease((z - 320) / 18), 1 - ease((z - 292) / 15))
    protect = np.maximum(protect, 1 - ease((x + 23) / 13))
    broad = ndimage.gaussian_filter(signed, np.array([1.2, 1.1, 1.55]) / STEP_MM)
    narrow = ndimage.gaussian_filter(signed, np.array([0.74, 0.74, 0.9]) / STEP_MM)
    field = broad + protect * (narrow - broad)

    # Recenter the level set to preserve the native label volume before reduction.
    count = round(np.count_nonzero(cropped) / ratio**3)
    rank = field.size - count
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(ordered[rank - 1 : rank + 1].mean(), -0.45, 0.45))
    inside = field > level
    if ndimage.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Smoothed field must enclose one pancreas without tunnels")
    points, faces, _, _ = marching_cubes(
        field, level, spacing=(STEP_MM,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    ras = points + lower * SOURCE_MM + AFFINE[:3, 3]
    a, b, c = (ras[faces] - ras.mean(0)).transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return ras, faces


def anchor_exterior(points):
    """Fit the two measured source landmarks using smooth, 6 mm-radius patches in RAS mm."""
    # Each pair is the closest dense r01 point and the corresponding filled-label landmark.
    anchors = [
        (
            [27.230288012510396, 197.44003805225898, 340.043283772072],
            [27.388671875, 197.460948061, 340.450000763],
        ),
        (
            [-1.8494071960449219, 196.888671875, 353.20000076293945],
            [-1.111328125, 196.907056481, 353.931616157],
        ),
    ]
    delta = np.zeros_like(points)
    for origin, landmark in anchors:
        pull = np.subtract(landmark, origin)
        radial = np.linalg.norm(points - origin, axis=1)
        weight = np.clip((6.0 - radial) / 6.0, 0, 1)
        delta += (weight**2 * (3 - 2 * weight))[:, None] * pull
    return points + delta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="Fresh replay directory")
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--revision", choices=("r01", "r02"), default="r01")
    args = parser.parse_args()
    mask = volume(args.case / "segmentations/pancreas.nii.gz", MASK_SHA, "u1")
    points, faces = reconstruct(mask)
    if args.revision == "r02":
        points = anchor_exterior(points)
    args.work.mkdir(parents=True)
    surface = args.work / "smooth.npz"
    export = args.work / "pancreas.mesh"
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
    revisions = json.loads(record.read_text())["revisions"]
    pin = next(revision for revision in revisions if revision["revisionId"] == args.revision)[
        "exports"
    ][0]
    if len(payload) != pin["bytes"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
        raise ValueError(f"Replayed pancreas differs from the {args.revision} identity")
    print(f"{hashlib.sha256(payload).hexdigest()}  {len(payload)} bytes  {export}")


if __name__ == "__main__":
    main()
