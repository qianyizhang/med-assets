"""Shared s1127 carotid SDF construction and clean packed-export replay."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_study import volume
from scipy import ndimage
from scipy.optimize import brentq
from skimage.measure import euler_number, marching_cubes

HERE = Path(__file__).resolve().parent
STEP_MM = 0.5
SOURCE_MM = 1.5
NECK_VOXELS = (371, 407)
TARGETS = {"carotid": 1900, "neck": 1650}


def transition(x, start, span):
    t = np.clip((x - start) / span, 0, 1)
    return t**2 * (3 - 2 * t)


def extract(field, level=0):
    vertices, faces, _, _ = marching_cubes(
        field, level, spacing=(STEP_MM,) * 3, allow_degenerate=False, gradient_direction="ascent"
    )
    if signed_volume(vertices, faces) < 0:
        faces = faces[:, ::-1]
    return vertices, faces


def signed_volume(vertices, faces):
    a, b, c = (vertices[faces] - vertices.mean(0)).transpose(1, 0, 2)
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6)


def crop_label(mask, margin):
    occupied = np.argwhere(mask)
    start = occupied.min(0) - margin
    stop = occupied.max(0) + margin + 1
    low = np.maximum(start, 0)
    high = np.minimum(stop, mask.shape)
    cropped = mask[tuple(slice(a, b) for a, b in zip(low, high, strict=True))]
    return np.pad(cropped, tuple(zip(low - start, stop - high, strict=True))), start


def reconstruct(mask, affine):
    cropped, lower = crop_label(mask, margin=6)
    raw, faces, _, _ = marching_cubes(
        cropped, 0.5, spacing=(SOURCE_MM,) * 3, allow_degenerate=False
    )
    raw_volume = abs(signed_volume(raw, faces))

    # The CT label reaches the last imaged slice. Extend that final cross-section
    # only in the smoothing field and intersect it with the original half-voxel cap.
    end = mask.shape[2] - 1
    if mask[:, :, end].any():
        last = end - lower[2]
        cropped[:, :, last + 1 : last + 4] = cropped[:, :, last : last + 1]
    ratio = STEP_MM / SOURCE_MM
    shape = tuple(np.ceil((np.array(cropped.shape) - 1) / ratio).astype(int) + 1)
    inside = (
        ndimage.affine_transform(
            cropped.astype(np.float32), np.eye(3) * ratio, output_shape=shape, order=1
        )
        >= 0.5
    )
    signed = (
        np.where(
            inside,
            ndimage.distance_transform_edt(inside) - 0.5,
            0.5 - ndimage.distance_transform_edt(~inside),
        )
        * STEP_MM
    )
    z = (lower[2] + np.arange(shape[2]) * ratio)[None, None, :]
    occupied_z = np.flatnonzero(mask.any(axis=(0, 1)))
    # Protect both ends and the inferior curvature. The central tubular course
    # uses stronger smoothing along Z where the working grid shows axial steps.
    strength = transition(z, max(occupied_z[0] + 3, 371), 5) * (1 - transition(z, 401, 6))
    broad = ndimage.gaussian_filter(signed, np.array([0.54, 0.54, 1.55]) / STEP_MM)
    narrow = ndimage.gaussian_filter(signed, np.array([0.42, 0.42, 0.56]) / STEP_MM)
    field = narrow + strength * (broad - narrow)
    end_limit = (end + 0.5 - z) * SOURCE_MM

    def full_field(level):
        return np.minimum(field - level, end_limit)

    def volume_difference(level):
        return signed_volume(*extract(full_field(level))) - raw_volume

    min_shift, max_shift = -0.35, 0.35
    level = brentq(volume_difference, min_shift, max_shift, xtol=1e-5)
    full = full_field(level)
    inferior, superior = (boundary - 0.5 for boundary in NECK_VOXELS)
    fields = {
        "carotid": full,
        "neck": np.minimum(full, np.minimum(z - inferior, superior - z) * SOURCE_MM),
    }
    shift = lower * SOURCE_MM + affine[:3, 3]
    out = {}
    for scope, values in fields.items():
        positive = values > 0
        if ndimage.label(positive)[1] != 1 or euler_number(positive, connectivity=1) != 1:
            raise ValueError(f"Expected one closed {scope} exterior with no tunnels")
        vertices, faces = extract(values)
        out[scope] = (vertices + shift, faces)
    return out


def replay(owner, side, mask_sha, shape, affine):
    parser = argparse.ArgumentParser(
        description=f"Replay the s1127 {side} common carotid exteriors."
    )
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--blender", required=True, type=Path)
    args = parser.parse_args()
    mask = volume(
        args.case / f"segmentations/common_carotid_artery_{side}.nii.gz",
        mask_sha,
        "u1",
        shape,
        affine,
    )
    args.work.mkdir(parents=True)
    inputs = []
    for scope, (vertices, faces) in reconstruct(mask, affine).items():
        dense = args.work / f"{scope}.npz"
        np.savez(dense, vertices=vertices, faces=faces, affine=affine)
        inputs.extend((str(dense), str(args.work / f"{scope}.mesh"), str(TARGETS[scope])))
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
            *inputs,
        ],
        check=True,
    )
    pins = json.loads((owner / "asset.record.json").read_text())["revisions"][0]["exports"]
    for pin in pins:
        artifact = args.work / Path(pin["path"]).name
        payload = artifact.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != pin["sha256"] or len(payload) != pin["bytes"]:
            raise ValueError(f"Replayed {artifact.name} differs from its r01 identity")
        print(f"{digest}  {len(payload)} bytes  {artifact}")
