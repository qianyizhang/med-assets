"""Render display-only materials on pinned source geometry in Blender."""

import argparse
import json
from pathlib import Path
import re
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gallery_plan import GALLERY_VIEWS, REPO, render_plan

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from render_teaching import configure_scene, render_pair, sha256


def material(group):
    name = "Gallery · " + group["label"]
    stored = bpy.data.materials.get(name)
    if stored is not None:
        return stored
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    rgb = [int(group["color"][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [channel / 12.92 if channel < 0.04045 else ((channel + .055) / 1.055) ** 2.4
              for channel in rgb]
    shader = result.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear, 1)
    shader.inputs["Roughness"].default_value = 0.78
    shader.inputs["Alpha"].default_value = group["alpha"]
    return result


def import_source(source):
    path = REPO / source["path"]
    if sha256(path) != source["sha256"]:
        raise ValueError(f"Gallery source differs from pin: {path}")
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    selected = []
    assignments = {}
    for obj in bpy.context.scene.objects:
        if obj in before or obj.type != "MESH":
            continue
        if source.get("surfaceOnly") and obj.get("view_role") != "surface":
            obj.hide_render = True
            continue
        old_material = " ".join(slot.material.name for slot in obj.material_slots if slot.material)
        group = next((group for group in source["groups"]
                      if re.search(group["pattern"], f"{obj.name}\n{old_material}", re.I | re.M)), source)
        display = material(group)
        if obj.material_slots:
            for slot in obj.material_slots:
                # Per-object assignment keeps a shared mesh's other instances intact.
                slot.link = "OBJECT"
                slot.material = display
        else:
            obj.data.materials.append(display)
        selected.append(obj)
        assignments[obj.name] = {key: group[key] for key in ("label", "color", "alpha")}
    if not selected:
        raise ValueError(f"No display geometry in {path}")
    return selected, assignments


def render_scene(job, root):
    folder = root / job["id"]
    folder.mkdir(exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    meshes, assignments = [], {}
    for source in job["inputs"]:
        imported, colors = import_source(source)
        meshes.extend(imported)
        assignments.update(colors)
    configure_scene(scene)
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 680, 560
    scene.cycles.samples = 28 if any(item["alpha"] < 1 for item in assignments.values()) else 14
    views = []
    for view in job["views"]:
        result = render_pair(scene, meshes, view, folder)
        groups = {}
        for name in result["visible"]:
            group = assignments[name]
            groups[group["label"]] = group
        result["legend"] = sorted(groups.values(), key=lambda x: x["label"].casefold())
        unmatched = [name for name in result["visible"] if assignments[name]["label"] == "Other anatomy"]
        if unmatched:
            raise ValueError(f"Unclassified parts in {job['id']}/{view['id']}: {unmatched}")
        views.append(result)
    record = dict(id=job["id"], inputs=[{key: item[key] for key in ("path", "sha256")}
                                       for item in job["inputs"]],
                  blender=bpy.app.version_string, transforms="source world transforms; no display placement edits",
                  views=views)
    (folder / "renders.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=GALLERY_VIEWS)
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    plan = list(render_plan())
    if args.only:
        jobs = [job for job in plan if job["id"] in args.only]
        if len(jobs) != len(set(args.only)):
            raise ValueError("Unknown gallery scene")
    else:
        jobs = plan[args.index::args.stride]
    args.output.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        render_scene(job, args.output)


if __name__ == "__main__":
    main()
