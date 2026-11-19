"""Render display-only materials on pinned source geometry in Blender."""

import argparse
import json
from pathlib import Path
import re
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gallery_plan import (
    GALLERY_VIEWS, REPO, WORKSHOP_ASSEMBLIES, core_scenes, load, render_plan, workshop_scenes,
)

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
    offset = job.get("offset")
    if offset:
        obj, = [mesh for mesh in meshes if mesh.name == offset["part"]]
        matrix = obj.matrix_world.copy()
        matrix.translation += Vector(offset["metres"])
        obj.matrix_world = matrix
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
    if offset:
        record["transforms"] = {"illustrativeDisplayOffset": offset}
    (folder / "renders.json").write_text(json.dumps(record, indent=2) + "\n")


def workshop_comparisons(folder):
    original, updated = (
        {scene["id"]: scene for scene in workshop_scenes(path)}
        for path in (WORKSHOP_ASSEMBLIES, folder)
    )
    for key, after in updated.items():
        before = original[key]
        receipt = json.loads((GALLERY_VIEWS / key / "renders.json").read_text())
        if receipt["inputs"] != [{k: s[k] for k in ("path", "sha256")} for s in before["inputs"]]:
            raise ValueError(f"Baseline render poses are stale for {key}")
        if key == "digestive-s1233":
            liver = next(group for group in after["inputs"][0]["groups"] if group["label"] == "Liver")
            liver["alpha"] = 0.18
        camera_bounds = {view["id"]: view["bounds"] for view in receipt["views"]}
        for name, job in (("original", before), ("updated", after)):
            yield {
                **job,
                "id": f"{key}-{name}",
                "views": [
                    {**view, "cameraBounds": camera_bounds[view["id"]]} for view in job["views"]
                ],
            }


def regional_comparisons():
    base = {scene["id"]: scene for scene in core_scenes()}
    refinements = {item["id"]: item for item in load("regional-views.json")}
    for item in refinements.values():
        job = base[item["scene"]]
        receipt = json.loads((GALLERY_VIEWS / job["id"] / "renders.json").read_text())
        names = [view["id"] for view in job["views"]]
        original = job["views"][names.index(item["view"])]
        captures = {view["id"]: view for view in receipt["views"]}
        captured = captures[item["view"]]
        frames = [captures[other["view"]]["bounds"] for other in refinements.values()
                  if other.get("style", other["id"]) == item.get("style", item["id"])]
        camera_bounds = [[limit(frame[side][axis] for frame in frames) for axis in range(3)]
                         for side, limit in enumerate((min, max))]
        offset = item.get("offset")
        if offset:
            for axis, delta in enumerate(offset["metres"]):
                camera_bounds[0][axis] += min(delta, 0)
                camera_bounds[1][axis] += max(delta, 0)
        view = {**original, "cameraBounds": camera_bounds}
        groups = refinements[item.get("style", item["id"])]["groups"]
        visible = captured["visible"]
        hidden = item.get("hide")
        if hidden:
            removed = {name for name in visible if re.search(hidden, name, re.I)}
            if not removed:
                raise ValueError(f"No parts matched hidden selection for {item['id']}")
            visible = [name for name in visible if name not in removed]
        for group in groups:
            if not any(re.search(group["pattern"], name, re.I) for name in visible):
                raise ValueError(f"No parts match {group['label']} in {item['id']}")
        yield {**job, "id": item["id"] + "-original", "views": [view]}
        yield {
            "id": item["id"] + "-updated",
            "offset": offset,
            "inputs": [
                {**source, "groups": groups + list(source["groups"])} for source in job["inputs"]
            ],
            "views": [{**view, "include": visible}],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=GALLERY_VIEWS)
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    comparison = parser.add_mutually_exclusive_group()
    comparison.add_argument("--compare-workshop", type=Path, metavar="ASSEMBLY_FOLDER")
    comparison.add_argument("--compare-regions", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if (args.compare_workshop or args.compare_regions) and args.output == GALLERY_VIEWS:
        parser.error("Comparisons require a separate --output")
    if args.compare_workshop:
        jobs = workshop_comparisons(args.compare_workshop.resolve())
    elif args.compare_regions:
        jobs = regional_comparisons()
    else:
        jobs = render_plan()
    plan = list(jobs)
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
