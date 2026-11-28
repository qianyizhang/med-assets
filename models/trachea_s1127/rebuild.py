"""Replay the s1127 tracheal air-column exterior and the two governed neck crops."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_study import volume
from build_thyroid import AFFINE, SHAPE
from scipy import ndimage
from scipy.optimize import brentq
from skimage.measure import euler_number, marching_cubes

HERE = Path(__file__).resolve().parent
MASK_SHA = "f7f88b8117b623a0b8c8eb7dba46498627da5afa115002ba879a664e02a624fe"
STEP_MM = 0.5
SOURCE_MM = 1.5
TARGETS = {"trachea": 3800, "thyroid": 2900, "carotid": 2000}


def ramp(x, start, span):
    fraction = np.clip((x - start) / span, 0, 1)
    return fraction**2 * (3 - 2 * fraction)


def signed_volume(vertices, faces):
    a, b, c = (vertices[faces] - vertices.mean(0)).transpose(1, 0, 2)
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6)


def surface(field, spacing, level):
    vertices, faces, _, _ = marching_cubes(
        field, level, spacing=(spacing,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    if signed_volume(vertices, faces) < 0:
        faces = faces[:, ::-1]
    return vertices, faces


def preserve_shoulders(points):
    # The lower rim persists in slices 342–344. The oblique upper shoulder
    # ends between slices 382 and 383. Both pulls are local and subvoxel.
    anchors = [
        ([17.3534383, 119.4023438, 204.7010945], [0.34, 0, 0], 4.0),
        ([3.4023438, 141.5323284, 262.3799846], [0, -0.04472, 0.35721], 6.0),
    ]
    delta = np.zeros_like(points)
    for center, direction, radius in anchors:
        weight = 1 - ramp(np.linalg.norm(points - center, axis=1), 0, radius)
        delta += weight[:, None] * direction
    return points + delta


def reconstruct(mask):
    occupied = np.argwhere(mask)
    lower, upper = occupied.min(0) - 6, occupied.max(0) + 7
    crop = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    raw_volume = signed_volume(*surface(crop, SOURCE_MM, 0.5))
    ratio = STEP_MM / SOURCE_MM
    shape = tuple(np.ceil((np.array(crop.shape) - 1) / ratio).astype(int) + 1)
    inside = (
        ndimage.affine_transform(
            crop.astype(np.float32), np.eye(3) * ratio, output_shape=shape, order=1
        )
        >= 0.5
    )
    sdf = (
        np.where(
            inside,
            ndimage.distance_transform_edt(inside) - 0.5,
            0.5 - ndimage.distance_transform_edt(~inside),
        )
        * STEP_MM
    )
    z = (lower[2] + ratio * np.arange(shape[2]))[None, None, :]
    # The sagittal trunk spans enough slices to smooth in the axial direction.
    # Short, irregular mask ends and the inferior bifurcation retain a tighter filter.
    smooth_trunk = ramp(z, 335, 7) * (1 - ramp(z, 382, 6))
    broad = ndimage.gaussian_filter(sdf, np.array([0.72, 0.72, 1.55]) / STEP_MM)
    narrow = ndimage.gaussian_filter(sdf, np.array([0.46, 0.46, 0.62]) / STEP_MM)
    field = narrow + smooth_trunk * (broad - narrow)
    level = brentq(
        lambda x: signed_volume(*surface(field, STEP_MM, x)) - raw_volume, -0.4, 0.4, xtol=1e-5
    )
    full = field - level
    fields = {
        "trachea": full,
        "thyroid": np.minimum(full, (z - 343.5) * SOURCE_MM),
        "carotid": np.minimum(full, (z - 368.5) * SOURCE_MM),
    }
    shift = lower * SOURCE_MM + AFFINE[:3, 3]
    shapes = {}
    for name, cropped in fields.items():
        active = cropped > 0
        if ndimage.label(active)[1] != 1 or euler_number(active, connectivity=1) != 1:
            raise ValueError(f"Expected one closed {name} air-column exterior")
        points, faces = surface(cropped, STEP_MM, 0)
        shapes[name] = (preserve_shoulders(points + shift), faces)
    return shapes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--blender", required=True, type=Path)
    args = parser.parse_args()
    mask = volume(args.case / "segmentations/trachea.nii.gz", MASK_SHA, "u1", SHAPE, AFFINE)
    args.work.mkdir(parents=True)
    paths = []
    for name, (vertices, faces) in reconstruct(mask).items():
        dense = args.work / f"{name}.npz"
        packed = args.work / f"{name}.mesh"
        np.savez(dense, vertices=vertices, faces=faces, affine=AFFINE)
        paths.extend((str(dense), str(packed), str(TARGETS[name])))
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
            *paths,
        ],
        check=True,
    )
    pins = json.loads((HERE / "asset.record.json").read_text())["revisions"][0]["exports"]
    for pin in pins:
        output = args.work / f"{pin['id']}.mesh"
        payload = output.read_bytes()
        sha = hashlib.sha256(payload).hexdigest()
        if sha != pin["sha256"] or len(payload) != pin["bytes"]:
            raise ValueError(f"Replayed {output.name} differs from its r01 identity")
        print(f"{sha}  {len(payload)} bytes  {output}")


if __name__ == "__main__":
    main()
