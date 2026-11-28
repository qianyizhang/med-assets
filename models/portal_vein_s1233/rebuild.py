"""Rebuild the combined s1233 venous surface in the original CT voxel frame."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
ORGAN = "portal_vein_and_splenic_vein"
MASK_SHA = "b1437b7058628669a6bc9e3b2e142dd019f1a2eeee88307e141f8f7d37e17e60"
SOURCE_STEP = 1.5
FINE_STEP = 0.5


def ease(value):
    t = np.clip(value, 0, 1)
    return t * t * (3 - 2 * t)


def target_field(cropped, revision):
    ratio = FINE_STEP / SOURCE_STEP
    shape = tuple(np.round((np.array(cropped.shape) - 1) / ratio).astype(int) + 1)
    fine = (
        ndimage.affine_transform(
            cropped.astype(np.float32), np.eye(3) * ratio, output_shape=shape, order=1
        )
        >= 0.5
    )
    inside = ndimage.distance_transform_edt(fine)
    outside = ndimage.distance_transform_edt(~fine)
    signed = np.where(fine, inside - 0.5, 0.5 - outside) * FINE_STEP
    broad = ndimage.gaussian_filter(signed, np.array([0.83, 0.83, 1.55]) / FINE_STEP)
    kernel = (0.6, 0.6, 0.72) if revision == "r01" else (0.68, 0.68, 1.12)
    narrow = ndimage.gaussian_filter(signed, np.array(kernel) / FINE_STEP)
    # The local radius distinguishes the gentler trunk from very thin tributaries.
    radius = ndimage.maximum_filter(inside * FINE_STEP, size=17)
    broad_weight = ease((radius - 2.8) / 2.7)
    return narrow + broad_weight * (broad - narrow)


def reconstruct(mask, revision):
    points = np.argwhere(mask)
    lower, upper = points.min(0) - 5, points.max(0) + 6
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    vertices, faces, _, _ = marching_cubes(cropped, 0.5, allow_degenerate=False)
    origin = lower * SOURCE_STEP + AFFINE[:3, 3]
    original = vertices.astype(float) * SOURCE_STEP
    xyz = original + origin
    x, y, z = xyz.T
    # Keep the raw saddle near the left posterior tip. Tighten the movement
    # at both observed junctions and keep the three outer endpoints in range.
    left_saddle = ease((x + 102.0) / 10)
    protect1, protect2 = (0.68, 0.70) if revision == "r01" else (0.36, 0.53)
    junction1 = 1 - protect1 * np.exp(-((x - 1) ** 2 + (y - 204) ** 2 + (z - 342) ** 2) / 180)
    junction2 = 1 - protect2 * np.exp(-((x - 36) ** 2 + (y - 199) ** 2 + (z - 359) ** 2) / 210)
    endpoint = np.minimum(ease((74 - x) / 7), ease((391 - z) / 7))
    weight = np.minimum.reduce((left_saddle, junction1, junction2, endpoint))

    field = target_field(cropped, revision)
    gradient = np.gradient(field, FINE_STEP)
    current = original.copy()
    # Project with bounded steps onto the volume-compensated SDF. Keeping the
    # half-label connectivity retains the source saddle which the old mesh erased.
    for _ in range(4):
        grid = (current / FINE_STEP).T
        residual = ndimage.map_coordinates(field, grid, order=1) + 0.16
        slopes = np.array([ndimage.map_coordinates(axis, grid, order=1) for axis in gradient]).T
        norm_squared = np.maximum(np.einsum("ij,ij->i", slopes, slopes), 0.25)
        current -= (np.clip(residual / norm_squared, -0.55, 0.55) * 0.7)[:, None] * slopes
    displacement = current - original
    length = np.maximum(np.linalg.norm(displacement, axis=1), 1e-8)
    xyz += displacement * (weight * np.minimum(1, 1.15 / length))[:, None]
    a, b, c = xyz[faces].transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return xyz, faces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="Fresh replay directory")
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--revision", choices=("r01", "r02"), default="r02")
    args = parser.parse_args()
    mask = volume(args.case / "segmentations" / f"{ORGAN}.nii.gz", MASK_SHA, "u1")
    vertices, faces = reconstruct(mask, args.revision)
    args.work.mkdir(parents=True)
    surface, export = args.work / "smooth.npz", args.work / f"{ORGAN}.mesh"
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
    payload = export.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    record = HERE / "asset.record.json"
    revisions = json.loads(record.read_text())["revisions"]
    pin = next(revision for revision in revisions if revision["revisionId"] == args.revision)[
        "exports"
    ][0]
    if len(payload) != pin["bytes"] or digest != pin["sha256"]:
        raise ValueError(f"Replayed export differs from the registered {args.revision} identity")
    print(f"{digest}  {len(payload)} bytes  {export}")


if __name__ == "__main__":
    main()
