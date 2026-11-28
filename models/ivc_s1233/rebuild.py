"""Rebuild the s1233 IVC exterior and abdominal locator in the source voxel grid."""

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
MASK_SHA = "44504ba513ec6292a4a030c097948f546054ea36fdfbca7b6896103cf1b488e0"
SOURCE_MM = 1.5
STEP_MM = 0.5
ABDOMINAL_SUPERIOR_Z = 270.5
TARGETS = {"ivc": 5800, "abdominal": 6000}


def transition(value, center, feather):
    fraction = np.clip((value - center) / feather, 0, 1)
    return fraction**2 * (3 - 2 * fraction)


def reconstruct(mask):
    occupied = np.argwhere(mask)
    lower, upper = occupied.min(axis=0) - 6, occupied.max(axis=0) + 7
    cropped = mask[tuple(slice(low, high) for low, high in zip(lower, upper, strict=True))]
    ratio = STEP_MM / SOURCE_MM
    fine_shape = tuple(np.ceil((np.array(cropped.shape) - 1) / ratio).astype(int) + 1)
    fine = (
        ndimage.affine_transform(
            cropped.astype(np.float32), np.eye(3) * ratio, output_shape=fine_shape, order=1
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
    z_voxel = (lower[2] + ratio * np.arange(fine_shape[2]))[None, None, :]
    # Use the tighter kernel at the small inferior extension, around the
    # frame-12 bulge, and in the irregular superior flare and cap.
    protect_inferior = 1 - transition(z_voxel, 144, 7)
    protect_window = transition(z_voxel, 197, 7) * (1 - transition(z_voxel, 212, 7))
    protect_superior = transition(z_voxel, 250, 9)
    protect = np.maximum.reduce([protect_inferior, protect_window, protect_superior])
    coarse = ndimage.gaussian_filter(signed, np.array([0.8, 0.8, 1.55]) / STEP_MM)
    fine = ndimage.gaussian_filter(signed, np.array([0.52, 0.52, 0.68]) / STEP_MM)
    field = coarse + protect * (fine - coarse)

    rank = field.size - round(np.count_nonzero(cropped) / ratio**3)
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = float(np.clip(ordered[rank - 1 : rank + 1].mean(), -0.45, 0.45))
    full = field - level

    # The existing sweep's lower bound equals the first occupied source slice.
    # Its upper bound cuts the full exterior between source slices 270 and 271.
    # Keep the analytical truncation planar at the half-label boundary.
    cropped_field = np.minimum(full, (ABDOMINAL_SUPERIOR_Z - z_voxel) * SOURCE_MM)
    shift = lower * SOURCE_MM + AFFINE[:3, 3]
    return {"ivc": extract(full, shift), "abdominal": extract(cropped_field, shift)}


def protect_shallow_rim(points):
    """Preserve the local peripheral shoulder represented on source slices 245 and 246."""
    anchor = np.array([28.138671875, 157.888671875, 408.907351594])
    normal = np.array([0.96645461, -0.18895174, -0.17396183])
    weight = 1 - transition(np.linalg.norm(points - anchor, axis=1), 0, 5.0)
    return points + (0.84 * weight[:, None]) * normal


def extract(field, shift):
    inside = field > 0
    if ndimage.label(inside)[1] != 1 or euler_number(inside, connectivity=1) != 1:
        raise ValueError("Expected one solid IVC exterior without tunnels or detached pieces")
    points, faces, _, _ = marching_cubes(
        field, 0.0, spacing=(STEP_MM,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    points = protect_shallow_rim(points + shift)
    a, b, c = (points[faces] - points.mean(0)).transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return points, faces


def digest(path):
    payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="Fresh replay directory")
    parser.add_argument("--blender", required=True, type=Path)
    args = parser.parse_args()
    mask = volume(args.case / "segmentations/inferior_vena_cava.nii.gz", MASK_SHA, "u1")
    surfaces = reconstruct(mask)
    args.work.mkdir(parents=True)
    outputs = []
    for scope, (vertices, faces) in surfaces.items():
        source = args.work / f"{scope}.npz"
        np.savez(source, vertices=vertices, faces=faces, affine=AFFINE)
        output = args.work / f"{scope}.mesh"
        outputs.extend((str(source), str(output), str(TARGETS[scope])))
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
            *outputs,
        ],
        check=True,
    )
    pins = json.loads((HERE / "asset.record.json").read_text())["revisions"][0]["exports"]
    for pin in pins:
        output = args.work / f"{pin['id']}.mesh"
        actual = digest(output)
        if actual != (pin["sha256"], pin["bytes"]):
            raise ValueError(f"Replayed {output.name} differs from its r01 identity")
        print(f"{actual[0]}  {actual[1]} bytes  {output}")


if __name__ == "__main__":
    main()
