"""Extract label surfaces and measure mask proximity in the s1233 scan frame."""

import argparse
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

from refinement import refine_overviews

OWNER = Path(__file__).resolve().parent


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def transform(affine, indices):
    return sum(indices[:, axis, None] * affine[:3, axis] for axis in range(3)) + affine[:3, 3]


def read_mask(path, pin, shape, affine):
    if sha256(path) != pin:
        raise ValueError(f"Mask identity mismatch: {path.name}")
    image = nib.load(path)
    if image.shape != tuple(shape) or not np.allclose(image.affine, affine, atol=1e-6, rtol=0):
        raise ValueError(f"Mask frame mismatch: {path.name}")
    return np.asarray(image.dataobj) != 0


def component_summary(mask, shell, shell_ras, *, measure_gap):
    labels, count = ndimage.label(mask)
    sizes = np.bincount(labels[mask])
    order = np.argsort(-sizes[1:], kind="stable") + 1
    summary = {"components6": count, "componentVoxelCounts6": sizes[order].tolist()}
    if measure_gap:
        shell_labels = labels[shell]
        largest = shell_ras[shell_labels == order[0]]
        runner_up = shell_ras[shell_labels == order[1]]
        distances, indices = cKDTree(runner_up).query(largest)
        point = int(distances.argmin())
        summary["largestComponentsMinimumVoxelCentreMm"] = round(float(distances[point]), 6)
        summary["largestComponentsClosestVoxelCentresRasMm"] = [
            largest[point].tolist(), runner_up[indices[point]].tolist(),
        ]
    return summary


def surface(raw, affine, *, measure_gap=False):
    extents = ndimage.find_objects(raw.astype(np.uint8))
    if not extents:
        raise ValueError("Empty label")
    crop = extents[0]
    start = np.array([axis.start for axis in crop])
    shape = np.array(raw.shape)
    stop = np.array([axis.stop for axis in crop])
    if np.any(start == 0) or np.any(stop == shape):
        raise ValueError("Label reaches the scan boundary")
    mask = raw[crop]
    shell = mask & ~ndimage.binary_erosion(mask)
    shell_ras = transform(affine, np.argwhere(shell) + start)
    vertices, faces, _, _ = marching_cubes(
        np.pad(mask, 1), level=0.5, gradient_direction="ascent", allow_degenerate=False
    )
    # Marching-cubes saddles can emit coincident triangles, which Blender drops.
    _, first = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
    duplicate_triangles = len(faces) - len(first)
    faces = faces[np.sort(first)]
    vertices_ras = transform(affine, vertices + start - 1)
    # Voxel-to-RAS and Workshop RAS-to-Blender both preserve handedness.
    signed_volume = np.einsum(
        "ij,ij->i", vertices_ras[faces[:, 0]],
        np.cross(vertices_ras[faces[:, 1]], vertices_ras[faces[:, 2]]),
    ).sum()
    if signed_volume <= 0:
        raise ValueError("Extracted surface has unexpected winding")
    vertices_blender = (vertices_ras * [-1, -1, 1] + [0, 155, -430]) / 1000
    summary = {
        "voxels": int(mask.sum()), "triangles": len(faces),
        **component_summary(mask, shell, shell_ras, measure_gap=measure_gap),
        "duplicateTrianglesRemoved": duplicate_triangles,
        "boundsBlenderMetres": [vertices_blender.min(0).tolist(), vertices_blender.max(0).tolist()],
    }
    return vertices_blender, faces, shell_ras, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smooth-overview", action="store_true",
                        help="Keep source topology while reducing voxel steps in a separate derivative")
    args = parser.parse_args()
    config = json.loads((OWNER / "inputs.json").read_text())
    affine = np.array(config["rasMmFromVoxel"])
    pins = config["maskSha256"]
    args.output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    surfaces = {}
    meshes = {}
    for label, pin in pins.items():
        mask = read_mask(args.masks / f"{label}.nii.gz", pin, config["shape"], affine)
        vertices, faces, shell, summary = surface(mask, affine, measure_gap=label == "colon")
        meshes[label] = (vertices, faces)
        summaries[label] = summary
        surfaces[label] = shell

    updates = refine_overviews(meshes, config["assemblies"]) if args.smooth_overview else {}
    for label, (vertices, faces) in meshes.items():
        mesh_path = args.output / f"{label}.npz"
        summary = summaries[label]
        if label in updates:
            vertices, evidence = updates[label]
            summary["sourceBoundsBlenderMetres"] = summary["boundsBlenderMetres"]
            summary["boundsBlenderMetres"] = [vertices.min(0).tolist(), vertices.max(0).tolist()]
            summary["overviewRefinement"] = evidence
        np.savez(mesh_path, vertices=vertices, faces=faces)
        summary["meshSha256"] = sha256(mesh_path)

    pairs = []
    for assembly in config["assemblies"].values():
        for left, right in assembly["pairs"]:
            distances, indices = cKDTree(surfaces[right]).query(surfaces[left])
            point = int(distances.argmin())
            pairs.append({
                "labels": [left, right],
                "minimumBoundaryVoxelCentreMm": round(float(distances[point]), 6),
                "leftCentresWithinOneVoxel": int(np.count_nonzero(distances <= 1.500001)),
                "closestCentresRasMm": [surfaces[left][point].tolist(), surfaces[right][indices[point]].tolist()],
            })
    receipt = {
        "case": config["case"], "labelGridRasMm": config["rasMmFromVoxel"],
        "inputs": pins, "parts": summaries, "pairProximity": pairs,
    }
    if args.smooth_overview:
        receipt["derivative"] = "bounded-source-surface-smoothing-v1"
    (args.output / "mask-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
