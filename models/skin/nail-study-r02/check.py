"""Measure topology and sampled anatomical relationships in two clean GLB imports."""

import argparse
from importlib import import_module
import json
from pathlib import Path
import struct
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
design = import_module("build")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from render_teaching import sha256


PARTS = (
    "Distal digit tissue",
    "Germinal matrix",
    "Nail bed",
    "Nail plate with free edge",
    "Proximal nail fold",
)
TOLERANCE_MM = 0.0025


def glb_counts(path):
    with path.open("rb") as handle:
        magic, version, _, size, tag = struct.unpack("<4sIII4s", handle.read(20))
        if (magic, version, tag) != (b"glTF", 2, b"JSON"):
            raise ValueError(f"Invalid GLB v2 header in {path}")
        data = json.loads(handle.read(size))
    counts = {}
    for node in data["nodes"]:
        if node.get("name", "").startswith("Nail | ") and "mesh" in node:
            primitives = data["meshes"][node["mesh"]]["primitives"]
            if any(primitive.get("mode", 4) != 4 for primitive in primitives):
                raise ValueError(f"Expected triangle primitives in {node['name']}")
            counts[node["name"].removeprefix("Nail | ")] = {
                "primitives": len(primitives),
                "triangles": sum(data["accessors"][p["indices"]]["count"] // 3 for p in primitives),
            }
    if set(counts) != set(PARTS):
        raise ValueError(f"{path.name} does not contain the five nail mesh identities")
    return counts


def clean_import(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), disable_bone_shape=True)
    return {
        obj.name.removeprefix("Nail | "): obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.name.startswith("Nail | ")
    }


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00000001)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            vertex = pending.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    pending.append(other)
    measurements = {
        "weldedComponents": components,
        "openOrNonmanifoldEdges": sum(not edge.is_manifold for edge in bm.edges),
        "signedVolumeMm3": bm.calc_volume(signed=True) * 1e9,
    }
    bm.free()
    return measurements


def acceleration(obj):
    obj.data.calc_loop_triangles()
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    triangles = [tri.vertices[:] for tri in obj.data.loop_triangles]
    return BVHTree.FromPolygons(points, triangles, all_triangles=True)


def interface(tree, s, u, top):
    x, y, _ = design.point(s, u, 0)
    start = 0.004 if top else -0.001
    direction = (0, 0, -1 if top else 1)
    hit, *_ = tree.ray_cast(Vector((x, y, start)), Vector(direction), 0.01)
    return None if hit is None else hit.z * 1000


def check_interface(left, right, samples):
    gaps = []
    for s, u in samples:
        lower = interface(left, s, u, top=True)
        upper = interface(right, s, u, top=False)
        if lower is None or upper is None:
            raise ValueError(f"Missing interface at s={s:.3f}, u={u:.3f}")
        gaps.append(abs(upper - lower))
    max_gap = max(gaps)
    if max_gap > TOLERANCE_MM:
        raise ValueError(f"Contact gap {max_gap:.5f} mm exceeds {TOLERANCE_MM} mm")
    return {"sampleCount": len(gaps), "maxGapMm": max_gap}


def check_landmarks(objects):
    digit, matrix, bed, plate, fold = [acceleration(objects[name]) for name in PARTS]
    contacts = {
        "matrix–plate": check_interface(matrix, plate, [(s, u) for s in (0.31, 0.61, 0.92) for u in (0.23, 0.70)]),
        "bed–plate": check_interface(bed, plate, [(s, u) for s in (1.17, 1.63, 2.12, 2.68) for u in (0.23, 0.70)]),
        "proximal fold–plate": check_interface(plate, fold, [(s, u) for s in (0.32, 0.49, 0.64) for u in (0.23, 0.70)]),
    }
    clearance = interface(plate, 2.98, 0.23, top=False) - interface(digit, 2.98, 0.23, top=True)
    protrusion = design.PLATE_END - design.DIGIT_END
    near_front = 0.025
    crown = interface(plate, 1.62, near_front, top=True) - interface(plate, 1.62, 0.88, top=True)
    proximal = interface(plate, 0.50, near_front, top=True)
    distal = interface(plate, 3.13, near_front, top=True)
    longitudinal = interface(plate, 1.85, near_front, top=True) - max(proximal, distal)
    if clearance < 0.17 or protrusion < 0.10 or crown < 0.20 or longitudinal < 0.04:
        raise ValueError("Expected a projecting free edge and a longitudinal/transverse plate crown")
    return {
        "contacts": contacts,
        "contactToleranceMm": TOLERANCE_MM,
        "clearanceUnderFreeEdgeMm": clearance,
        "projectingEdgeXSpanMm": protrusion,
        "transverseCrownDropMm": crown,
        "longitudinalCrownRiseMm": longitudinal,
    }


def measure(path, updated):
    counts = glb_counts(path)
    objects = clean_import(path)
    if set(objects) != set(PARTS):
        raise ValueError("Unexpected clean-import mesh names")
    if updated and len(bpy.context.scene.objects) != len(PARTS):
        raise ValueError("Updated GLB includes unexpected scene objects")
    for name, obj in objects.items():
        counts[name].update(topology(obj))
        if updated and (
            counts[name]["weldedComponents"] != 1
            or counts[name]["openOrNonmanifoldEdges"] != 0
            or counts[name]["signedVolumeMm3"] <= 0
        ):
            raise ValueError(f"Expected a single outward-facing closed shell for {name}")
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in objects.values()
        for corner in obj.bound_box
    ]
    return {
        "file": str(path),
        "sha256": sha256(path),
        "fileBytes": path.stat().st_size,
        "boundsMm": [
            [1000 * min(p[i] for p in corners) for i in range(3)],
            [1000 * max(p[i] for p in corners) for i in range(3)],
        ],
        "parts": counts,
        "totalTriangles": sum(count["triangles"] for count in counts.values()),
        "totalPrimitives": sum(count["primitives"] for count in counts.values()),
        **({"landmarks": check_landmarks(objects)} if updated else {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("original", "updated", "receipt"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    report = {
        "blender": bpy.app.version_string,
        "original": measure(args.original, False),
        "updated": measure(args.updated, True),
    }
    with args.receipt.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
