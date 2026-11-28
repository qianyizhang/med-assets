"""Compare bounded, exterior-only corrections to the frozen pancreatic r01."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
ROOT = REPO / "experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a"
RADIUS_MM = 6.0
CAP_MM = 1.5


def source_data(case):
    frozen = json.loads((HERE.parent / "reference.json").read_text())
    mask = volume(case / "segmentations/pancreas.nii.gz", frozen["source"]["maskSha256"], "u1")
    occupied = np.argwhere(mask)
    lo, stop = occupied.min(0) - 2, occupied.max(0) + 3
    cropped = mask[tuple(slice(a, b) for a, b in zip(lo, stop, strict=True))]
    filled = ndimage.binary_fill_holes(cropped)
    vertices, faces, _, _ = marching_cubes(filled.astype("f"), 0.5, allow_degenerate=False)
    vertices = np.einsum("ij,kj->ik", vertices + lo, AFFINE[:3, :3]) + AFFINE[:3, 3]
    return frozen, vertices[faces]


def sites():
    review = json.loads((ROOT / "measurements.json").read_bytes())
    planes = review["pancreasExteriorDiagnostic"]["delineation"]["protectedPlanes"]
    return [
        (row["offsetMm"], np.array(row["referenceToMesh"]["maxLocationRasMm"]))
        for row in planes
        if row["referenceToMesh"]["maxMm"] > 3.0
    ]


def closest_point(point, triangles):
    """Closest point on the triangles, testing open faces and all three edges."""
    a, b, c = triangles.transpose(1, 0, 2)
    normal = np.cross(b - a, c - a)

    def dot(u, v):
        return np.einsum("ij,ij->i", u, v)

    plane = point - normal * (dot(point - a, normal) / dot(normal, normal))[:, None]
    inside = np.ones(len(a), dtype=bool)
    choices = []
    for left, right in ((a, b), (b, c), (c, a)):
        edge = right - left
        inside &= dot(np.cross(edge, plane - left), normal) >= -1e-10
        t = np.clip(dot(point - left, edge) / dot(edge, edge), 0, 1)
        choices.append(left + t[:, None] * edge)
    possible = np.concatenate([plane[inside], *choices])
    return possible[np.argmin(np.linalg.norm(possible - point, axis=1))]


def prepare(case, replay, output):
    _, triangles = source_data(case)
    owner = json.loads((ROOT / "measurements.json").read_bytes())["export"]
    if sha256((replay / "pancreas.mesh").read_bytes()).hexdigest() != owner["sha256"]:
        raise ValueError("Expected the exact r01 replay")
    with np.load(replay / "smooth.npz") as original:
        points, faces, affine = (original[k] for k in ("vertices", "faces", "affine"))
    dense_digest = sha256()
    for array, dtype in ((points, "<f8"), (faces, "<u4"), (affine, "<f8")):
        dense_digest.update(array.astype(dtype).tobytes())
    if (
        dense_digest.hexdigest()
        != "a6161d9afddce1deca1cd88daacef6504f2caad1ddb7df5eb345d420871c8722"
    ):
        raise ValueError("Dense mesh or affine differs from the r01 replay")
    delta = np.zeros_like(points)
    source_delta = np.zeros_like(points)
    original_triangles = points[faces]
    summary = []
    for offset, center in sites():
        # Any surface within the displacement cap fits inside this box, including
        # triangles whose centroid is outside it. The source is the filled exterior.
        radius = RADIUS_MM + CAP_MM
        local = triangles[
            ((triangles.max(1) >= center - radius) & (triangles.min(1) <= center + radius)).all(1)
        ]
        distance = np.linalg.norm(points - center, axis=1)
        selected = np.flatnonzero(distance < RADIUS_MM)
        for i in selected:
            shift = closest_point(points[i], local) - points[i]
            weight = np.clip((RADIUS_MM - distance[i]) / (RADIUS_MM / 2), 0, 1)
            delta[i] = (
                shift
                * min(1, CAP_MM / max(np.linalg.norm(shift), 1e-12))
                * weight**2
                * (3 - 2 * weight)
            )
        # Opposite-direction control: anchor the local displacement at the nearest
        # dense surface point to this frozen source contour, with a smooth falloff.
        anchor = closest_point(center, original_triangles)
        pull = center - anchor
        radial = np.linalg.norm(points - anchor, axis=1)
        weight = np.clip((RADIUS_MM - radial) / RADIUS_MM, 0, 1)
        source_delta += (
            (weight**2 * (3 - 2 * weight))[:, None]
            * pull
            * min(1, CAP_MM / max(np.linalg.norm(pull), 1e-12))
        )
        summary.append(
            dict(
                sourceAnchorCorrectionMm=float(np.linalg.norm(pull)),
                planeMm=offset,
                centerRasMm=center.tolist(),
                vertices=len(selected),
                maxCorrectionMm=float(np.max(np.linalg.norm(delta[selected], axis=1))),
            )
        )
    output.mkdir(parents=True, exist_ok=False)
    for name, strength in (("half", 0.5), ("full", 1.0)):
        target = output / name
        target.mkdir()
        np.savez(
            target / "smooth.npz", vertices=points + delta * strength, faces=faces, affine=affine
        )
    target = output / "anchor"
    target.mkdir()
    np.savez(target / "smooth.npz", vertices=points + source_delta, faces=faces, affine=affine)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("case", "r01_replay", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    prepare(args.case, args.r01_replay, args.output)
