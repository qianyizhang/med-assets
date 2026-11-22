"""Check the actual imported edition, source landmarks, and reference-frame limits."""

import json
import sys
from pathlib import Path
import runpy

import numpy as np
from mathutils.bvhtree import BVHTree

owner = runpy.run_path(str(Path(__file__).with_name("trials.py")))
root = owner["ROOT"]
load = owner["load"]
coords = owner["points"]


def signature(obj):
    obj.data.calc_loop_triangles()
    return coords(obj), np.asarray([tuple(t.vertices) for t in obj.data.loop_triangles])


def contacts(positions, faces):
    tree = BVHTree.FromPolygons(positions.tolist(), faces.tolist(), all_triangles=True)
    return sum(
        i < j and not np.intersect1d(faces[i], faces[j]).size
        for i, j in tree.overlap(tree)
    )


def main():
    out = Path(sys.argv[sys.argv.index("--") + 1])
    results = {}
    for key, (src, _, name) in owner["MODELS"].items():
        previous = {o.name: signature(o) for o in load(root / src)}
        new = {o.name: signature(o) for o in load(out / name)}
        if key == "adrenals":
            result = {}
            for gland, (positions, faces) in previous.items():
                xyz, tri = new[gland]
                diff = np.max(
                    np.abs(
                        np.stack(
                            [
                                xyz.min(0) - positions.min(0),
                                xyz.max(0) - positions.max(0),
                            ]
                        )
                    )
                )
                old_hits = contacts(positions, faces)
                new_hits = contacts(xyz, tri)
                if diff > 0.000001 or new_hits > old_hits or len(faces) != len(tri):
                    raise ValueError(
                        f"Lost gland extent or new surface contact: {gland} {diff} {old_hits} {new_hits}"
                    )
                result[gland] = {
                    "boundsDeltaMm": diff * 1000,
                    "sourceContacts": int(old_hits),
                    "editionContacts": int(new_hits),
                }
        elif key == "pancreas":
            outer = "Pancreatic gross envelope (interpreted)"
            result = {}
            for n, (xyz, tri) in new.items():
                if n == outer:
                    hits = contacts(xyz, tri)
                    result[n] = {"nonadjacentContacts": int(hits)}
                    if hits:
                        raise ValueError(
                            f"Gross envelope has {hits} nonadjacent contacts"
                        )
                else:
                    source_points, source_faces = previous[n]
                    # Export triangulation can split shading vertices; compare unique anatomical positions.
                    source_points = np.unique(source_points.round(7), axis=0)
                    new_points = np.unique(xyz.round(7), axis=0)
                    if (
                        source_points.shape != new_points.shape
                        or not np.allclose(source_points, new_points, atol=0.000001)
                        or len(source_faces) != len(tri)
                    ):
                        raise ValueError(f"Changed reference context: {n}")
                    result[n] = {
                        "triangles": len(tri),
                        "uniquePositions": len(new_points),
                    }
        else:
            source = next(
                xyz for n, (xyz, _) in previous.items() if n.startswith("Thoracic")
            )
            sections = np.split(source[np.argsort(source[:, 2])], 5)
            result = {}
            for idx, label in [
                (0, "Lower source limit (symbol)"),
                (-1, "Upper source limit (symbol)"),
            ]:
                xyz, _ = new[label]
                unique = np.unique(xyz.round(7), axis=0)
                centroid = (unique.min(0) + unique.max(0)) / 2
                err = np.linalg.norm(centroid - sections[idx].mean(0)) * 1000
                if err > 0.0002:
                    raise ValueError(f"Shifted source limit: {label} {err}")
                result[label] = {"sourceCapCenterErrorMm": err}
        results[key] = result
    print(json.dumps(results, indent=2))
    (out / "clean-import-check.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
