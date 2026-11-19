"""Clean-import and compare the pinned gallery original and authored cutaway."""
import argparse
from collections import deque
import json
from pathlib import Path
import struct
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build import DEPTHS, NAMES, X, tube_point

ROOT = Path(__file__).resolve().parents[3]
from render_teaching import configure_scene, render_pair, sha256

ORIGINAL = ROOT / "lessons/one-breath/airway-r01/airway-route.glb"
ORIGINAL_SHA256 = "92fd447bad48b03489041e16d0de8750b550034ec4f158219b8352571e0e6091"
CAMERA_BOUNDS = [[.104, -.002, .121], [.149, .006, .147]]
TOLERANCE = .00000004


def inspect_glb(glb, names):
    with glb.open("rb") as stream:
        magic, version, length, size, chunk = struct.unpack("<4sIII4s", stream.read(20))
        if (magic, version, length, chunk) != (b"glTF", 2, glb.stat().st_size, b"JSON"):
            raise ValueError(f"Invalid GLB container: {glb}")
        parsed = json.loads(stream.read(size))
    result = {}
    for node in parsed["nodes"]:
        name = node.get("name")
        if name in names:
            primitives = parsed["meshes"][node["mesh"]]["primitives"]
            counts = []
            for primitive in primitives:
                if primitive.get("mode", 4) != 4:
                    raise ValueError(f"Expected triangle primitive in {name}")
                counts.append(parsed["accessors"][primitive["indices"]]["count"] // 3)
            result[name] = {"primitives": len(counts), "triangles": sum(counts)}
    if set(result) != set(names):
        raise ValueError(f"Round-trip mesh names differ in {glb}")
    return result


def weld(objects):
    mesh = bmesh.new()
    for obj in objects:
        mesh.from_mesh(obj.data)
        count = len(obj.data.vertices)
        for vertex in list(mesh.verts)[-count:]:
            vertex.co = obj.matrix_world @ vertex.co
    bmesh.ops.remove_doubles(mesh, verts=list(mesh.verts), dist=TOLERANCE)
    return mesh


def components(mesh):
    remaining = set(mesh.verts)
    count = 0
    while remaining:
        count += 1
        frontier = deque([remaining.pop()])
        while frontier:
            vertex = frontier.popleft()
            for edge in vertex.link_edges:
                neighbor = edge.other_vert(vertex)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    frontier.append(neighbor)
    return count


def ray_spans(bvh, paths):
    """All requested inlet and mouth crossings must exist in free space."""
    result = []
    for a, b in paths:
        start, end = Vector(a), Vector(b)
        delta = end - start
        loc, *_ = bvh.ray_cast(start, delta.normalized(), delta.length)
        if loc is not None:
            raise ValueError(f"Passage obstructed from {list(a)} to {list(b)}")
        result.append(round(delta.length * 1000, 3))
    return result


def study_metrics(objects, artifact_dir):
    mesh = weld(objects)
    if components(mesh) != 1 or any(not e.is_manifold for e in mesh.edges):
        raise ValueError("Airway surfaces must form one closed tissue shell after world-space welding")
    inverted = sum(not e.is_contiguous for e in mesh.edges)
    if inverted:
        raise ValueError(f"Inconsistent winding at {inverted} edges")
    tree = BVHTree.FromBMesh(mesh)
    axes = [tube_point(x, 0, 0, 0) for x in (105.3, *X, 146.8)]
    targets = json.loads((artifact_dir / "airspace-targets.json").read_text())
    expected = [
        (row, col) for row, depths in enumerate(DEPTHS)
        for col, depth in enumerate(depths) if depth
    ]
    if [(target["row"], target["col"]) for target in targets] != expected:
        raise ValueError("Missing or out-of-order authored airspace targets")
    paths = []
    for target in targets:
        floor = Vector(target["floor"])
        x = (X[target["row"]] + X[target["row"] + 1]) / 2
        center = Vector(tube_point(x, 0, 0, 0))
        # Stop just inside the pocket, before the tissue surface.
        paths.append((center, center.lerp(floor, .90)))
    result = {
        "worldWeldToleranceMetres": TOLERANCE,
        "weldedComponents": 1,
        "nonManifoldEdges": 0,
        "inconsistentlyWoundEdges": 0,
        "unobstructedAxisSegmentsDisplayMillimetres": ray_spans(tree, zip(axes, axes[1:])),
        "unobstructedLumenToRecessSegmentsDisplayMillimetres": ray_spans(tree, paths),
    }
    mesh.free()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    directory = options.artifact_dir.resolve()
    output = directory / "renders"
    if sha256(ORIGINAL) != ORIGINAL_SHA256:
        raise ValueError(f"Source identity differs for {ORIGINAL}")
    if output.exists() and not options.check_only:
        raise FileExistsError(output)
    views = []
    all_metrics = {}
    for identifier, glb in (
        ("original", ORIGINAL), ("updated", directory / "terminal-airspaces.glb"),
    ):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(glb), disable_bone_shape=True)
        scene = bpy.context.scene
        objects = [o for o in scene.objects if o.type == "MESH"]
        selected = [o for o in objects if o.name.startswith("Terminal | ")] if identifier == "original" else objects
        names = sorted(o.name for o in selected)
        expected = len(names) == 11 if identifier == "original" else set(names) == set(NAMES)
        if not expected:
            raise ValueError(f"Incorrect terminal study selection for {glb}")
        parts = inspect_glb(glb, names)
        for obj in selected:
            mesh = weld([obj])
            parts[obj.name]["components"] = components(mesh)
            mesh.free()
        result = {
            "glb": {"file": glb.name, "sha256": sha256(glb)},
            "sourceFileBytes": glb.stat().st_size,
            "parts": parts,
            "total": {key: sum(p[key] for p in parts.values()) for key in ("primitives", "triangles", "components")},
        }
        if identifier == "updated":
            result["continuity"] = study_metrics(selected, directory)
        all_metrics[identifier] = result
        if not options.check_only:
            configure_scene(scene)
            output.mkdir(exist_ok=True)
            view = render_pair(scene, objects, {
                "id": identifier, "include": names, "cameraBounds": CAMERA_BOUNDS,
            }, output)
            view["glb"] = result["glb"]
            views.append(view)

    (directory / "metrics.json").write_text(json.dumps(all_metrics, indent=2) + "\n")
    if views:
        receipt = {
            "blender": bpy.app.version_string,
            "display": {
                "cameraBoundsBlenderMetres": CAMERA_BOUNDS,
                "engine": "Cycles CPU", "samples": 12, "denoise": True,
                "viewTransform": "AgX", "exposure": 0, "background": "transparent",
                "lighting": "Same Key, Fill, Rim and world rig from tools/render_teaching.py",
                "materials": "Each GLB's own materials. Original is a fresh rerender without gallery palette overrides.",
            },
            "views": views,
        }
        (output / "renders.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
