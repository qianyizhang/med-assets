"""Render both revisions in the same original world-space camera frame."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from fnmatch import fnmatchcase
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review import ROOT, EXPORTS, identity

sys.path.insert(0, str(ROOT / "tools"))
from render_teaching import configure_scene, render_pair

VIEWS = {
    "parotid": ("parotid-pair", (0, -1, 0), ("*",)),
    "duct-course": ("glands-ducts", (0.65, -1, 0.08), ("*",)),
    "jaw-context": ("context", (0.95, -0.35, -0.42), ("*",)),
    "oral-floor": (
        "context", (0, -0.04, 1),
        ("Mandible source display", "Submandibular gland.*", "Sublingual gland.*"),
    ),
}


def world_points(meshes, include):
    return {
        obj.name: [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        for obj in meshes if any(fnmatchcase(obj.name, pattern) for pattern in include)
    }


def projection_box(points, direction):
    rotation = (-Vector(direction)).to_track_quat("-Z", "Y").inverted()
    positions = [rotation @ point for point in points]
    return [stat(point[axis] for point in positions) for stat in (min, max) for axis in (0, 1)]


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for role, (export_role, front, include) in VIEWS.items():
        old, new, _ = EXPORTS[export_role]
        comparison = {"view": role, "export_role": export_role, "included_objects": include}
        for revision, relpath in (("original", old), ("updated", new)):
            path = ROOT / relpath
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
            scene = bpy.context.scene
            meshes = [obj for obj in scene.objects if obj.type == "MESH"]
            configure_scene(scene)
            scene.render.resolution_x, scene.render.resolution_y = 720, 576
            scene.cycles.samples = 16
            points = world_points(meshes, include)
            if revision == "original":
                reference = points
                all_points = [point for group in points.values() for point in group]
                bounds = [[stat(point[axis] for point in all_points) for axis in range(3)] for stat in (min, max)]
                comparison["camera_bounds"] = bounds
            view = {"id": f"{role}-{revision}", "front": front, "include": include, "cameraBounds": bounds}
            rendered = render_pair(scene, meshes, view, output)
            comparison[revision] = {"path": relpath, **identity(path), **rendered}
        baseline = comparison["original"]
        candidate = comparison["updated"]
        assert baseline["orthographicScale"] == candidate["orthographicScale"]
        assert reference.keys() == points.keys()
        max_delta = 0.0
        for old_view, new_view in zip(baseline["images"], candidate["images"], strict=True):
            assert old_view["camera"] == new_view["camera"] and old_view["direction"] == new_view["direction"]
            for name in points:
                old_box = projection_box(reference[name], old_view["direction"])
                new_box = projection_box(points[name], new_view["direction"])
                for a, b in zip(old_box, new_box, strict=True):
                    delta = abs(a - b) * scene.render.resolution_x / baseline["orthographicScale"]
                    max_delta = max(max_delta, delta)
        assert max_delta < 0.05, (role, max_delta)
        comparison["maximum_projected_outline_shift_px"] = max_delta
        rows.append(comparison)
    (output / "renders.json").write_text(json.dumps({"blender": bpy.app.version_string, "views": rows}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args.out)
