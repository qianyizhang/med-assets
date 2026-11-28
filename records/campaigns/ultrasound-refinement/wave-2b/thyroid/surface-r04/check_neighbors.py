"""Check the left superior lobe in 3D and sample parallel planes withheld from fitting."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "measure.py"
SPEC = importlib.util.spec_from_file_location("thyroid_geometry", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load the pinned thyroid measurements from {SOURCE}")
thyroid = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(thyroid)


def shoulder(triangles):
    """Centroids in the superior left-lobe region, in source RAS millimetres."""
    x, _, z = triangles.mean(axis=1).T
    return triangles[(x < 0) & (z >= 272)]


def held_out_cuts(raw, candidate, planes):
    rows = []
    for name in ("left_48_1", "right_48_1"):
        spec = next(plane for plane in planes if plane["name"] == name)
        normal = np.array(spec["normal"])
        for offset in (-2.25, -0.75, 0.75, 2.25):
            origin = np.array(spec["originRasMm"]) + normal * offset
            cuts = [thyroid.geometry.cut(surface, origin, normal) for surface in (raw, candidate)]
            row = {"base": name, "offsetMm": offset}
            if all(len(cut) for cut in cuts):
                result = thyroid.compare(*cuts)
                direction = max(result, key=lambda key: result[key]["maxMm"])
                point = np.array(result[direction]["maxLocationRasMm"])
                target = candidate if direction == "referenceToMesh" else raw
                dist2 = thyroid.geometry.squared_distance(np.broadcast_to(point, (len(target), 3)), target)
                row.update(maxMm=result[direction]["maxMm"], direction=direction,
                           p95Mm=max(v["p95Mm"] for v in result.values()),
                           position=point.tolist(), nearestSurfaceMm=float(np.sqrt(dist2.min())))
            else:
                row.update(sourceSegments=len(cuts[0]), meshSegments=len(cuts[1]))
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    frozen = json.loads((HERE.parent / "reference.json").read_text())
    if thyroid.geometry.identity(args.reference) != frozen["reference"]:
        raise ValueError("Reference differs from the frozen raw half-label")
    with np.load(args.reference, allow_pickle=False) as data:
        raw = data["vertices"][data["faces"]]
    out = {}
    for revision in ("r01", "r03", "r04"):
        mesh = HERE.parents[5] / "models/thyroid_s1127/exports" / revision / "thyroid_gland.mesh"
        vertices, faces = thyroid.mesh(mesh)
        candidate = vertices[faces]
        out[revision] = {
            "meshSha256": thyroid.geometry.identity(mesh)["sha256"],
            "leftSuperiorRegional3d": {
                "rawToMesh": thyroid.geometry.compare(shoulder(raw), candidate),
                "meshToRaw": thyroid.geometry.compare(shoulder(candidate), raw),
            },
            "heldOutParallelCuts": held_out_cuts(raw, candidate, frozen["protectedPlanes"]),
        }
    args.output.write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
