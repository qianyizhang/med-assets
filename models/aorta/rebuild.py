"""Rebuild the s1233 aortic exterior and its two ultrasound views."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from scipy import ndimage as nd
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
MASK_SHA = "c2751ba8bb12ed2091db7e0446f3f333acf47db5d35e8f75c96fab4c6564ab2e"
STEP_MM = 0.6
SOURCE_MM = 1.5
CROPS = {"aorta": None, "aorta-abdomen": (140, 271), "aorta-screening": (117, 237)}


def ease(value):
    t = np.clip(value, 0, 1)
    return t**2 * (3 - 2 * t)


def aortic_field(mask):
    """Build one physical signed-distance field with a tighter endpoint kernel."""
    active = np.column_stack(np.nonzero(mask))
    lower, upper = active.min(0) - 5, active.max(0) + 6
    region = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    ratio = STEP_MM / SOURCE_MM
    shape = tuple(np.ceil((np.asarray(region.shape) - 1) / ratio).astype(int) + 1)
    samples = nd.affine_transform(
        region.astype(np.float32), np.eye(3) * ratio, output_shape=shape, order=1
    )
    inside = samples >= 0.5
    signed = STEP_MM * np.where(
        inside, nd.distance_transform_edt(inside) - 0.5, 0.5 - nd.distance_transform_edt(~inside)
    )
    axial = lower[2] + np.arange(shape[2]) * ratio
    # Preserve the source termination at the iliac level and the curved upper thoracic label.
    protect = np.maximum(1 - ease((axial - 148) / 7), ease((axial - 326) / 10))
    trunk = nd.gaussian_filter(signed, np.array([0.65, 0.65, 1.8]) / STEP_MM)
    ends = nd.gaussian_filter(signed, np.array([0.45, 0.45, 0.65]) / STEP_MM)
    field = trunk + protect * (ends - trunk)
    count = round(len(active) / ratio**3)
    rank = field.size - count
    ordered = np.partition(field.ravel(), (rank - 1, rank))
    level = (ordered[rank - 1] + ordered[rank]) / 2
    return field - level, axial, lower * SOURCE_MM + AFFINE[:3, 3]


def surface(field, axial, origin, crop):
    if crop is not None:
        low, high = (bound - 0.5 for bound in crop)
        # The cuts lie at the half-label crop caps in the original voxel grid.
        cap = SOURCE_MM * np.minimum(axial - low, high - axial)
        field = np.minimum(field, cap + 1e-5)
    vertices, faces, _, _ = marching_cubes(
        field, level=0, spacing=(STEP_MM,) * 3, allow_degenerate=False
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
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--trial", action="store_true", help="Build without an accepted digest")
    args = parser.parse_args()
    mask = volume(args.case / "segmentations/aorta.nii.gz", MASK_SHA, "u1")
    field, axial, origin = aortic_field(mask)
    args.work.mkdir(parents=True)
    for name, crop in CROPS.items():
        vertices, faces = surface(field, axial, origin, crop)
        np.savez(args.work / f"{name}-dense.npz", vertices=vertices, faces=faces, affine=AFFINE)

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
            str(args.work),
            *CROPS,
        ],
        check=True,
    )
    expected = {}
    if not args.trial:
        revisions = json.loads((HERE / "asset.record.json").read_text())["revisions"]
        revision = next(row for row in revisions if row["revisionId"] == "ultrasound-r01")
        expected = {row["id"]: (row["sha256"], row["bytes"]) for row in revision["exports"]}
    for name in CROPS:
        export = args.work / f"{name}.mesh"
        payload = export.read_bytes()
        actual = hashlib.sha256(payload).hexdigest(), len(payload)
        if not args.trial and actual != expected[name]:
            raise ValueError(f"Replayed {name} differs from its pinned identity")
        print(f"{actual[0]}  {actual[1]} bytes  {export}")


if __name__ == "__main__":
    main()
