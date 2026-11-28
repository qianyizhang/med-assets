"""Rebuild the s1233 gallbladder in its original voxel-index frame."""

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
MASK_SHA = "c5dd1e8886ed87d29dac8225acbac49dfc308c0ead9116690c818e49b1addcc7"
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
    interior = ndimage.distance_transform_edt(fine)
    signed = (
        np.where(
            fine,
            interior - 0.5,
            0.5 - ndimage.distance_transform_edt(~fine),
        )
        * STEP_MM
    )
    # The thin terminal regions of the label need a narrower filter.
    reach = ndimage.maximum_filter(interior, size=11) * STEP_MM
    protect = 1 - ease((reach - 3.0) / 3.5)
    body = ndimage.gaussian_filter(signed, np.array([1.58, 1.58, 2.30]) / STEP_MM)
    thin = ndimage.gaussian_filter(signed, np.array([0.88, 0.88, 1.55]) / STEP_MM)
    field = body + protect * (thin - body)

    # Enclose the cleaned native label volume on the finer grid.
    count = round(np.count_nonzero(clean) * (SOURCE_MM / STEP_MM) ** 3)
    rank = field.size - count
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(ordered[rank - 1 : rank + 1].mean(), -0.45, 0.45))
    inside = field > level
    if ndimage.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Smoothed field must enclose one gallbladder without tunnels")
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
    mask = volume(args.case / "segmentations/gallbladder.nii.gz", MASK_SHA, "u1")
    points, faces = reconstruct(mask)
    args.work.mkdir(parents=True)
    surface = args.work / "smooth.npz"
    export = args.work / "gallbladder.mesh"
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
        raise ValueError("Replayed gallbladder differs from the r01 identity")
    print(f"{hashlib.sha256(payload).hexdigest()}  {len(payload)} bytes  {export}")


if __name__ == "__main__":
    main()
