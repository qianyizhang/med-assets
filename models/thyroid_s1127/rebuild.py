"""Rebuild the paired s1127 thyroid lobes and isthmus in the CT voxel frame."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_abdomen import mesh_from_mask
from build_study import volume
from build_thyroid import AFFINE, PINS, SHAPE
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
LABEL = "thyroid_gland"
STEP_MM = 0.75
SOURCE_MM = 1.5


def reconstruct(mask, revision):
    points = np.argwhere(mask)
    lower, upper = points.min(0) - 4, points.max(0) + 5
    crop = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))].astype(np.float32)
    ratio = STEP_MM / SOURCE_MM
    shape = tuple(np.rint((np.array(crop.shape) - 1) / ratio).astype(int) + 1)
    transform = np.eye(3) * ratio
    half_label = ndimage.affine_transform(crop, transform, output_shape=shape, order=1)
    broad = ndimage.gaussian_filter(crop, (0.78, 0.78, 1.04))
    smooth = ndimage.affine_transform(broad, transform, output_shape=shape, order=1)
    origin = AFFINE[:3, 3] + lower * SOURCE_MM
    xyz = [
        axis * STEP_MM + start
        for axis, start in zip(np.indices(shape, sparse=True), origin, strict=True)
    ]
    # Keep the two grazing exterior contours in the left longitudinal neighborhood.
    # Feather the fit over neighboring slices so the preserved patches do not form seams.
    protect = np.zeros(shape, dtype=np.float32)
    for landmark in ((-7.66, 164.40, 276.82), (-4.98, 150.77, 272.5), (-8.12, 170.40, 283.27)):
        distance = np.sqrt(
            sum((axis - point) ** 2 for axis, point in zip(xyz, landmark, strict=True))
        )
        blend = np.clip((10.0 - distance) / 5.5, 0, 1)
        protect = np.maximum(protect, blend * blend * (3 - 2 * blend))
    # The isthmus is the narrow region centered on the course's sagittal divider.
    bridge_weight = 0.35 if revision == "r02" else 0.10
    bridge = bridge_weight * np.exp(-(((xyz[0] - 5.65) / 6) ** 2))
    support = protect
    if revision == "r03":
        protect = 0.86 * support
    protect = np.maximum(protect, bridge)
    field = smooth + protect * (half_label - smooth) + (1 - protect) * 0.023
    if revision == "r03":
        # Small outward field compensation preserves the sampled tangent loops.
        field += 0.022 * support
    vertices, faces, _, _ = marching_cubes(
        field, 0.5, spacing=(STEP_MM,) * 3, allow_degenerate=False
    )
    points = vertices + origin
    a, b, c = points[faces].transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return points, faces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="Fresh output directory")
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--revision", choices=("r01", "r02", "r03"), default="r03")
    args = parser.parse_args()
    if args.revision in ("r02", "r03") and args.blender is None:
        parser.error("--blender is required for a shaped revision")
    mask = volume(args.case / "segmentations" / f"{LABEL}.nii.gz", PINS[LABEL], "u1", SHAPE, AFFINE)
    args.work.mkdir(parents=True)
    export = args.work / f"{LABEL}.mesh"
    if args.revision == "r01":
        export.write_bytes(mesh_from_mask(mask))
    else:
        vertices, faces = reconstruct(mask, args.revision)
        surface = args.work / "smooth.npz"
        np.savez(surface, vertices=vertices, faces=faces, affine=AFFINE)
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
    data = export.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    record = HERE / "asset.record.json"
    pin = next(
        revision
        for revision in json.loads(record.read_text())["revisions"]
        if revision["revisionId"] == args.revision
    )["exports"][0]
    if len(data) != pin["bytes"] or digest != pin["sha256"]:
        raise ValueError(f"Replayed thyroid differs from {args.revision}")
    print(f"{digest}  {len(data)} bytes  {export}")


if __name__ == "__main__":
    main()
