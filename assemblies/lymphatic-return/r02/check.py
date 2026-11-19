"""Evaluate the exported section joints, directional mark and image identities."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree

INLETS = tuple(f"Afferent lymphatic {i}" for i in range(1, 4))
OUTLET = "Efferent lymphatic at hilum"
ARROW = "Intranodal transit arrow"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def surface(obj):
    data = obj.data
    data.calc_loop_triangles()
    require(all(triangle.area > 1e-12 for triangle in data.loop_triangles),
            f"Degenerate triangle in {obj.name}")
    points = [obj.matrix_world @ vertex.co for vertex in data.vertices]
    return BVHTree.FromPolygons(points, [triangle.vertices[:] for triangle in data.loop_triangles],
                                all_triangles=True), points


def verify_arrow(obj):
    # Compare shared positions rather than glTF vertices split for normal/UV seams.
    obj.data.calc_loop_triangles()
    keys = [tuple(round(a, 7) for a in v.co) for v in obj.data.vertices]
    edges = Counter()
    for face in obj.data.loop_triangles:
        a, b, c = (keys[i] for i in face.vertices)
        for edge in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted(edge))] += 1
    require(max(edges.values()) == 2, "Flow arrow has overlapping or open triangle patches")
    boundary = [edge for edge, count in edges.items() if count == 1]
    neighbors = {}
    for a, b in boundary:
        neighbors.setdefault(a, set()).add(b)
        neighbors.setdefault(b, set()).add(a)
    require(all(len(adjoining) == 2 for adjoining in neighbors.values()),
            "Flow-arrow seam is open")
    frontier = [next(iter(neighbors))]
    visited = set()
    while frontier:
        point = frontier.pop()
        if point not in visited:
            visited.add(point)
            frontier.extend(neighbors[point] - visited)
    require(visited == neighbors.keys(), "Flow arrow has disconnected silhouettes or a hole")


def verify_assets(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), disable_bone_shape=True)
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    expected = {"Lymphoid section face", "Nodal capsule", "Subcapsular sinus band", ARROW, OUTLET,
                *INLETS, *(f"Cortical follicle cue {i}" for i in range(1, 9))}
    require(objects.keys() == expected, "Missing, renamed or duplicate nodal part")
    require(all(obj.get("derivation") and obj.get("view_role") and obj.get("anatomy_id")
                for obj in objects.values()), "Missing anatomy identity or derivation")
    require(all(obj.data.materials and obj.data.materials[0] for obj in objects.values()),
            "Missing matte surface assignment")
    surfaces = {name: surface(obj) for name, obj in objects.items()}
    capsule, _ = surfaces["Nodal capsule"]
    for name in (*INLETS, OUTLET):
        require(capsule.overlap(surfaces[name][0]), f"{name} misses the capsule")
    arrow = objects[ARROW]
    verify_arrow(arrow)
    _, arrow_points = surfaces[ARROW]
    inlet_x = min(p.x for name in INLETS for p in surfaces[name][1])
    outlet_x = max(p.x for p in surfaces[OUTLET][1])
    start, finish = min(p.x for p in arrow_points), max(p.x for p in arrow_points)
    require(inlet_x < start < 0 < finish < outlet_x, "Transit arrow does not point toward efferent side")
    return len(objects)


def verify_renders(asset, output):
    document = json.loads((output / "renders.json").read_text())
    require(document["sha256"] == digest(asset) and document["glb"] == asset.name,
            "Render receipt points to different geometry")
    require(document["viewsSha256"] == digest(Path(__file__).with_name("views.json")),
            "View selection does not match the recipe")
    require([view["id"] for view in document["views"]] == ["node-section", "node-passage"],
            "Missing expected clean-import view")
    for view in document["views"]:
        images = view["images"]
        require([item["file"] for item in images] == [f"{view['id']}-iso.png", f"{view['id']}-ortho.png"],
                "Invalid image pair")
        for item in images:
            require(digest(output / item["file"]) == item["sha256"], f"Image identity mismatch: {item['file']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--renders", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    count = verify_assets(args.glb)
    if args.renders:
        verify_renders(args.glb, args.renders)
    print(f"{count} named parts, four structural contacts, connected arrow silhouette and required identities passed")
