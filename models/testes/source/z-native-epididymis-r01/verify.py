"""Independently compare native evaluated source to a clean GLB import.

Blender 4.3.2; no image, clinical or browser assertions. Export float32 tolerance
2e-7 native units is far below a visible fraction of these ~0.03-unit objects.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils.kdtree import KDTree

SOURCE_SHA = "9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd"
NAMES = [f"{part}.{side}" for part in ("Testis", "Epididymis") for side in ("r", "l")]


def geometry(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = np.array([tuple(obj.matrix_world @ v.co) for v in mesh.vertices])
    vertices, inverse = np.unique(vertices, axis=0, return_inverse=True)
    faces = inverse[np.array([t.vertices[:] for t in mesh.loop_triangles])]
    return vertices, faces


def canonical(faces):
    return sorted(tuple(np.roll(t, -np.argmin(t))) for t in faces)


def topology(vertices, faces):
    edges = Counter(tuple(sorted((int(t[i]), int(t[(i + 1) % 3]))))
                    for t in faces for i in range(3))
    area = np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                   vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
    return {"triangles": len(faces), "unique_positions": len(vertices),
            "boundary_edges": sum(v == 1 for v in edges.values()),
            "nonmanifold_edges": sum(v > 2 for v in edges.values()),
            "zero_area_triangles": int(np.count_nonzero(area < 1e-16)),
            "duplicate_triangles": len(faces) - len(set(tuple(sorted(t)) for t in faces)),
            "finite_positions": bool(np.isfinite(vertices).all())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if hashlib.sha256(args.source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Source hash mismatch")
    if args.out.exists():
        raise FileExistsError("Receipt must be new")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    with bpy.data.libraries.load(str(args.source), link=False) as (_, selected):
        selected.objects = list(NAMES)
    for obj in selected.objects:
        bpy.context.collection.objects.link(obj)
        for mod in obj.modifiers:
            if mod.type == "SUBSURF":
                # Independently use the source's own render setting, not build.py.
                mod.levels = mod.render_levels
    bpy.context.view_layer.update()
    source = {}
    for obj in selected.objects:
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = bpy.data.meshes.new_from_object(evaluated)
        temporary = bpy.data.objects.new("verification", mesh)
        temporary.matrix_world = obj.matrix_world.copy()
        source[obj.name] = geometry(temporary)
        bpy.data.objects.remove(temporary)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.artifact), merge_vertices=False)
    bpy.context.view_layer.update()
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    names = [obj.get("source_object") for obj in objects]
    if sorted(names) != sorted(NAMES):
        raise ValueError("Unexpected or missing objects, including excluded deferens")
    rows = []
    for obj in objects:
        name = obj["source_object"]
        expected, expected_faces = source[name]
        actual, faces = geometry(obj)
        kd = KDTree(len(expected))
        for i, point in enumerate(expected):
            kd.insert(point, i)
        kd.balance()
        matches = [kd.find(point) for point in actual]
        indices = np.array([m[1] for m in matches])
        error = max(m[2] for m in matches)
        bijective = len(actual) == len(expected) == len(set(indices))
        oriented_faces_equal = canonical(expected_faces) == canonical(indices[faces])
        rows.append({"name": name, "max_coordinate_error_native_units": error,
                     "bijective_vertex_mapping": bijective,
                     "oriented_triangles_equal": oriented_faces_equal,
                     "source": topology(expected, expected_faces), "export": topology(actual, faces)})
    passed = all(row["max_coordinate_error_native_units"] < 2e-7
                 and row["bijective_vertex_mapping"] and row["oriented_triangles_equal"]
                 and row["export"]["finite_positions"] for row in rows)
    receipt = {"source_sha256": SOURCE_SHA,
               "artifact_sha256": hashlib.sha256(args.artifact.read_bytes()).hexdigest(),
               "source_export_pass": passed, "objects": rows,
               "scope": "Exhaustive vertex/topology comparison of four evaluated source objects; no manual geometry changes; source anatomical defects may persist",
               "tolerance_native_units": 2e-7,
               "anatomy": "reference-screened only", "runtime": "unverified"}
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    if not passed:
        raise AssertionError("Source/export mismatch; see receipt")
    print(json.dumps({"source_export_pass": passed, "objects": rows}, indent=2))


if __name__ == "__main__":
    main()
