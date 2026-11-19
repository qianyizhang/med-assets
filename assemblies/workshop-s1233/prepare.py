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


def surface(raw, affine):
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
    components = ndimage.label(mask)[1]
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
        "voxels": int(mask.sum()), "components6": components, "triangles": len(faces),
        "duplicateTrianglesRemoved": duplicate_triangles,
        "boundsBlenderMetres": [vertices_blender.min(0).tolist(), vertices_blender.max(0).tolist()],
    }
    return vertices_blender, faces, shell_ras, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((OWNER / "inputs.json").read_text())
    affine = np.array(config["rasMmFromVoxel"])
    pins = config["maskSha256"]
    args.output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    surfaces = {}
    for label, pin in pins.items():
        mask = read_mask(args.masks / f"{label}.nii.gz", pin, config["shape"], affine)
        vertices, faces, shell, summary = surface(mask, affine)
        mesh_path = args.output / f"{label}.npz"
        np.savez(mesh_path, vertices=vertices, faces=faces)
        summary["meshSha256"] = sha256(mesh_path)
        summaries[label] = summary
        surfaces[label] = shell

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
    (args.output / "mask-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
