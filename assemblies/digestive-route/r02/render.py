"""Render the pinned original and clean-import teaching section with one camera fit."""

import argparse
from fnmatch import fnmatchcase
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from render_teaching import configure_scene, render_pair, sha256

ORIGINAL = HERE.parent / "r01" / "digestive-route.glb"
ORIGINAL_SHA256 = "f91ee8cb160b182d932b991a1dff61d465213431b87cff535cf907fa8822834a"
ORIGINAL_PARTS = ("Food 04*", "Food 05*", "Accessory Bile*", "Accessory Pancreatic*", "Accessory Common*")
ENTRY_PARTS = ("Duodenum wall", "Duodenum mucosa", "Duodenum cut faces",
               "Major duodenal papilla", "Pyloric opening rim", "Common bile duct",
               "Main pancreatic duct", "Common channel")


def imported_meshes(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def bounds(meshes, patterns):
    return [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        if any(fnmatchcase(obj.name, pattern) for pattern in patterns)
        for corner in obj.bound_box
    ]


def render(output, model):
    if sha256(ORIGINAL) != ORIGINAL_SHA256:
        raise ValueError("Restore the original r01 digestive route GLB before replaying the comparison")
    candidate_sha256 = sha256(model)
    geometry = json.loads(model.with_name("geometry.json").read_text())
    if candidate_sha256 != geometry["glb"]["sha256"]:
        raise ValueError("The revised GLB differs from its clean-reimport receipt")
    points = [*bounds(imported_meshes(ORIGINAL), ORIGINAL_PARTS), *bounds(imported_meshes(model), ("*",))]
    camera_bounds = [[fn(point[axis] for point in points) for axis in range(3)] for fn in (min, max)]

    output.mkdir(parents=True, exist_ok=False)
    views = []
    for label, path, include, digest in (
        ("original", ORIGINAL, ORIGINAL_PARTS, ORIGINAL_SHA256),
        ("updated", model, ("*",), candidate_sha256),
    ):
        meshes = imported_meshes(path)
        scene = bpy.context.scene
        configure_scene(scene)
        scene.cycles.samples = 22
        view = render_pair(scene, meshes, {"id": label, "include": include, "cameraBounds": camera_bounds}, output)
        view["glb"] = {"file": path.name, "sha256": digest}
        views.append(view)
    entry = render_pair(
        scene,
        meshes,
        {"id": "duct-entry", "include": ENTRY_PARTS, "front": (-0.40, -1, 0.14)},
        output,
    )
    entry["glb"] = {"file": model.name, "sha256": candidate_sha256}
    views.append(entry)
    if (
        views[0]["orthographicScale"] != views[1]["orthographicScale"]
        or any(left["camera"] != right["camera"] for left, right in zip(views[0]["images"], views[1]["images"]))
    ):
        raise ValueError("The original and updated comparison must share camera positions and scale")
    (output / "renders.json").write_text(json.dumps({
        "blender": bpy.app.version_string,
        "cameraBounds": camera_bounds,
        "materials": "Each clean reimport uses its authored matte materials",
        "frame": "r01 digestive schematic, +X left / -Y anterior / +Z superior in Blender metres",
        "views": views,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    render(args.output.resolve(), args.glb.resolve())
