"""Rebuild the s1233 spleen in its original voxel-index frame."""

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
MASK_SHA = "760eb489a2f6821ce25e7565e4d73709cab5a1ef0af6537d193b2ce036213573"
STEP_MM = 0.6
SOURCE_MM = 1.5


def ease(value):
    t = np.clip(value, 0, 1)
    return t**2 * (3 - 2 * t)


def reconstruct(mask):
    points = np.column_stack(np.nonzero(mask))
    lower, upper = points.min(axis=0) - 6, points.max(axis=0) + 7
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
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
    x, y, z = [axis * STEP_MM for axis in np.indices(size, sparse=True)]
    local = (points - lower) * SOURCE_MM
    bottom, top = local[:, 2].min(), local[:, 2].max()
    center = np.median(local, axis=0)
    # RAS x increases toward the medial face in this subject's spleen.
    medial = ease((x - center[0] + 2) / 14)
    hilum = (
        medial
        * (1 - ease((abs(z - center[2]) - 12) / 19))
        * (1 - ease((abs(y - center[1]) - 12) / 16))
    )
    ends = 1 - ease((np.minimum(z - bottom, top - z) - 1) / 7)
    # The scan crosses the medial notch almost tangentially. Blend in a
    # tighter physical kernel near its high, oblique shoulder.
    notch = np.array([-106.0, 104.0, 375.5]) - AFFINE[:3, 3] - lower * SOURCE_MM
    radial = np.sqrt((x - notch[0]) ** 2 + (y - notch[1]) ** 2 + (z - notch[2]) ** 2)
    notch_weight = 1 - ease((radial - 9) / 11)
    protect = np.maximum.reduce(np.broadcast_arrays(hilum, ends, notch_weight))
    broad = ndimage.gaussian_filter(signed, np.array([1.55, 1.55, 2.15]) / STEP_MM)
    narrow = ndimage.gaussian_filter(signed, np.array([0.85, 0.85, 1.05]) / STEP_MM)
    field = broad + protect * (narrow - broad)

    # Recenter the level set to preserve the native label volume before reduction.
    count = round(np.count_nonzero(cropped) / ratio**3)
    rank = field.size - count
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(ordered[rank - 1 : rank + 1].mean(), -0.45, 0.45))
    inside = field > level
    if ndimage.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Smoothed field must enclose one spleen without tunnels")
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
    mask = volume(args.case / "segmentations/spleen.nii.gz", MASK_SHA, "u1")
    points, faces = reconstruct(mask)
    args.work.mkdir(parents=True)
    surface = args.work / "smooth.npz"
    export = args.work / "spleen.mesh"
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
    pin = next(revision for revision in revisions if revision["revisionId"] == "r01")["exports"][0]
    if len(payload) != pin["bytes"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
        raise ValueError("Replayed spleen differs from the r01 identity")
    print(f"{hashlib.sha256(payload).hexdigest()}  {len(payload)} bytes  {export}")


if __name__ == "__main__":
    main()
