"""Screen retained endocrine labels and prepare bounded s1233 surface derivatives."""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
WORKSHOP = HERE.parents[1] / "workshop-s1233"
sys.path.insert(0, str(WORKSHOP))
from prepare import read_mask, sha256, surface
from refinement import refine_overviews


def prepare(masks, output):
    frame = json.loads((WORKSHOP / "inputs.json").read_text())
    config = json.loads((HERE / "inputs.json").read_text())
    affine = np.array(frame["rasMmFromVoxel"])
    pins = config["maskSha256"]
    if pins["pancreas"] != frame["maskSha256"]["pancreas"]:
        raise ValueError("Endocrine pancreas pin differs from the same-case Workshop input")
    parts, meshes, shells = {}, {}, {}
    for label, pin in pins.items():
        mask = read_mask(masks / f"{label}.nii.gz", pin, frame["shape"], affine)
        vertices, faces, shell, part = surface(mask, affine)
        occupied = np.argwhere(mask)
        lo = occupied.min(axis=0)
        hi = occupied.max(axis=0)
        part["edgeMarginsInVoxels"] = [lo.tolist(), (np.array(mask.shape) - 1 - hi).tolist()]
        meshes[label] = (vertices, faces)
        parts[label] = part
        shells[label] = shell
    updated = refine_overviews(meshes, config["assemblies"])
    output.mkdir(parents=True, exist_ok=False)
    for label, (vertices, evidence) in updated.items():
        mesh = output / f"{label}.npz"
        np.savez(mesh, vertices=vertices, faces=meshes[label][1])
        parts[label]["sourceBoundsBlenderMetres"] = parts[label]["boundsBlenderMetres"]
        parts[label]["boundsBlenderMetres"] = [vertices.min(0).tolist(), vertices.max(0).tolist()]
        parts[label]["overviewRefinement"] = evidence
        parts[label]["meshSha256"] = sha256(mesh)
    pairs = []
    for assembly in config["assemblies"].values():
        for a, b in assembly["pairs"]:
            distances, _ = cKDTree(shells[a]).query(shells[b])
            pairs.append({
                "labels": [a, b],
                "minimumBoundaryVoxelCentreMm": round(float(distances.min()), 6),
            })
    (output / "mask-audit.json").write_text(json.dumps({
        "case": frame["case"],
        "shape": frame["shape"],
        "labelGridRasMm": frame["rasMmFromVoxel"],
        "inputs": pins,
        "parts": parts,
        "pairProximity": pairs,
        "derivative": "bounded-source-surface-smoothing-v1",
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.masks, args.output)
