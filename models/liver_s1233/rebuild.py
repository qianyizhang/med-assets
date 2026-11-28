"""Replay either pinned liver surface in its original s1233 voxel-index grid."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LFS_HEADER = b"version https://git-lfs.github.com/spec/v1\n"
SOURCE_MM = 1.5
STEP_MM = 0.75
MASK_SHA = "0e37697cde4bf2f6042fa89d338cfbe71d85b4b44e42801840be5612c4785980"


def _is_matching_lfs_pointer(data: bytes, digest: str, size: int) -> bool:
    if not data.startswith(LFS_HEADER):
        return False
    fields: dict[str, str] = {}
    for line in data.decode("utf-8", errors="ignore").splitlines():
        if " " in line:
            key, value = line.split(" ", 1)
            fields[key.strip()] = value.strip()
    return fields.get("oid") == f"sha256:{digest}" and fields.get("size") == str(size)


def place_verified_output(candidate: Path, destination: Path, raw: bytes, digest: str) -> None:
    """Install verified bytes at destination, replacing only a matching LFS pointer."""
    try:
        os.link(candidate, destination)
    except FileExistsError:
        existing = destination.read_bytes()
        if existing == raw:
            return
        if _is_matching_lfs_pointer(existing, digest, len(raw)):
            os.replace(candidate, destination)
            return
        raise ValueError(
            f"Existing output differs: {destination}. Choose --output in a fresh directory."
        ) from None


def reconstruct(mask, affine):
    """Smooth in physical 3D, preserving the documented inferior cleft."""
    import numpy as np
    from scipy import ndimage
    from skimage.measure import euler_number, marching_cubes

    occupied = np.argwhere(mask)
    lower, upper = occupied.min(axis=0) - 6, occupied.max(axis=0) + 7
    cropped = mask[tuple(slice(lo, hi) for lo, hi in zip(lower, upper, strict=True))]
    size = tuple(2 * (np.array(cropped.shape) - 1) + 1)
    fine = (
        ndimage.affine_transform(
            cropped.astype(np.float32), np.eye(3) * 0.5, output_shape=size, order=1
        )
        >= 0.5
    )
    signed = (
        np.where(
            fine,
            ndimage.distance_transform_edt(fine) - 0.5,
            0.5 - ndimage.distance_transform_edt(~fine),
        ).astype(np.float32)
        * STEP_MM
    )

    def ease(value):
        t = np.clip(value, 0, 1)
        return t**2 * (3 - 2 * t)

    def protected(coord, lo, hi, margin):
        return ease((coord - lo + margin) / margin) * ease((hi + margin - coord) / margin)

    grid = [
        axis * STEP_MM / SOURCE_MM + lo
        for axis, lo in zip(np.indices(size, sparse=True), lower, strict=True)
    ]
    x, y, z = grid

    def box(x_band, y_band, z_band):
        return protected(x, *x_band) * protected(y, *y_band) * protected(z, *z_band)

    cleft = protected(x, 166, 182, 7) * protected(y, 170, 197, 7) * protected(z, 206, 208, 8)
    broad = ndimage.gaussian_filter(signed, np.array([1.45, 1.45, 1.85]) / STEP_MM)
    dome = ndimage.gaussian_filter(signed, np.array([1.65, 1.65, 2.4]) / STEP_MM)
    narrow = ndimage.gaussian_filter(signed, np.array([0.8, 0.8, 1.05]) / STEP_MM)
    field = broad + ease((z - 237) / 17) * (dome - broad)
    field += cleft * (narrow - field)
    # Account for the slight expansion from half-label resampling on the working grid.
    field -= 0.3
    # Retain narrow channels and folds that the wider field shortens. A centered,
    # interpolated native occupancy field preserves their section geometry.
    guide = (
        ndimage.affine_transform(
            ndimage.gaussian_filter(cropped.astype(np.float32), 0.85),
            np.eye(3) * 0.5,
            output_shape=size,
            order=1,
        )
        - 0.5
    ) * 3.2
    deep_channel = box((148, 162, 3), (144, 158, 3), (227, 245, 4))
    retained = np.maximum.reduce(
        [
            deep_channel,
            box((169, 177, 2), (171, 191, 3), (213, 223, 3)),
            box((147, 157, 3), (119, 129, 2), (231, 247, 3)),
            box((159, 168, 2), (174, 187, 3), (256, 266, 2)),
            box((113, 120, 2), (149, 158, 3), (252, 259, 3)),
        ]
    )
    retained = np.maximum(retained, box((187, 193, 2), (135, 143, 2), (210, 216, 2)))
    field += retained * (guide - field) - deep_channel * 0.12

    # Bridge the narrowest resolved part of the inferior passage while retaining
    # both adjoining recesses. The support radius is one native source voxel.
    radius_vox = 1
    center_vox = (171, 178.5, 219.5)
    radius_fraction2 = sum(
        ((coord - center) / radius_vox) ** 2 for coord, center in zip(grid, center_vox, strict=True)
    )
    field += 0.7 * np.square(np.maximum(0, 1 - radius_fraction2))

    inside = field > 0
    if (
        ndimage.label(inside)[1] != 1
        or euler_number(inside, connectivity=1) != 1
        or euler_number(inside, connectivity=3) != 1
    ):
        raise ValueError("Refined liver must enclose one solid component without tunnels")
    vertices, faces, _, _ = marching_cubes(
        field, 0, spacing=(STEP_MM,) * 3, gradient_direction="ascent", allow_degenerate=False
    )
    ras = vertices.astype(float) + lower * SOURCE_MM + affine[:3, 3]
    a, b, c = (ras[faces] - ras.mean(axis=0)).transpose(1, 0, 2)
    if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
        faces = faces[:, ::-1]
    return ras, faces


def rebuild_refined(case: Path, blender: Path, candidate: Path) -> Path:
    import numpy as np
    from build_study import AFFINE, volume

    mask = volume(case / "segmentations/liver.nii.gz", MASK_SHA, "u1")
    vertices, faces = reconstruct(mask, AFFINE)
    dense = candidate.with_name("smooth.npz")
    np.savez(dense, vertices=vertices, faces=faces, affine=AFFINE)
    subprocess.run(
        [
            str(blender),
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--python-exit-code",
            "1",
            "--python",
            str(Path(__file__).with_name("retopology.py")),
            "--",
            str(dense),
            str(candidate),
        ],
        check=True,
    )
    return dense


def main() -> None:
    owner = Path(__file__).resolve().parent
    repo = owner.parents[1]
    record = json.loads((owner / "asset.record.json").read_text())
    builder = repo / "experiments/ultrasound-sweep/build_abdomen.py"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=os.environ.get("S1233_CASE"))
    parser.add_argument("--revision", choices=("r01", "r02"), default="r01")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--blender", type=Path, help="Pinned Blender executable for r02")
    parser.add_argument("--dense-output", type=Path, help="Fresh pre-decimation NPZ path for r02")
    args = parser.parse_args()
    if args.case is None:
        parser.error("Supply --case or set S1233_CASE to the pinned case directory")
    if args.revision == "r02" and args.blender is None:
        parser.error("Supply --blender for r02")
    if args.revision == "r01" and (args.blender or args.dense_output):
        parser.error("--blender and --dense-output apply to r02")
    if args.dense_output and args.dense_output.exists():
        parser.error("--dense-output requires a fresh path")
    revision = next(row for row in record["revisions"] if row["revisionId"] == args.revision)
    export = next(row for row in revision["exports"] if row["id"] == "liver")
    output = args.output or repo / export["path"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        candidate = Path(temp) / "liver.mesh"
        if args.revision == "r01":
            subprocess.run(
                [sys.executable, str(builder), str(args.case), "--export-liver", str(candidate)],
                check=True,
            )
            dense = None
        else:
            dense = rebuild_refined(args.case, args.blender, candidate)
        raw = candidate.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) != export["bytes"] or digest != export["sha256"]:
            parser.exit(
                1, f"Liver replay differs from {args.revision}: {digest}, {len(raw)} bytes\n"
            )
        try:
            place_verified_output(candidate, output, raw, digest)
            if dense and args.dense_output:
                os.link(dense, args.dense_output)
        except ValueError as exc:
            parser.exit(1, f"{exc}\n")
    print(f"Verified {args.revision} liver surface: {digest}, {len(raw)} bytes")


if __name__ == "__main__":
    main()
