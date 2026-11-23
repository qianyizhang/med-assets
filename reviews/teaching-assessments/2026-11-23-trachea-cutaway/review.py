"""Render the exact One Breath cutaway and its shading-only size trial."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.glb import decode
from med_assets.glb_repack import compact_normals

MODEL = "models/trachea/exports/open-airway-r06/trachea-cutaway.glb"
SHA256 = "42b25a9e3de950db1a083da3802d4bb982c9084c425f768824c8973dc08be283"
SHELL = "Trachea | authored cutaway teaching shell"


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def inventory(path, data):
    doc, _ = decode(data)
    return {
        "file": path.name, **identity(data),
        "triangles": sum(doc["accessors"][p["indices"]]["count"] // 3
                         for mesh in doc["meshes"] for p in mesh["primitives"]),
        "meshes": len(doc["meshes"]),
        "primitives": sum(len(mesh["primitives"]) for mesh in doc["meshes"]),
        "shellTriangles": sum(doc["accessors"][p["indices"]]["count"] // 3 for p in doc["meshes"][0]["primitives"]),
        "materials": [material["name"] for material in doc["materials"]],
    }


def gltf_to_blender(point):
    x, y, z = point
    return Vector((x, -z, y))


def render(renderer, tag, path, out, guide):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), merge_vertices=False)
    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    shell = scene.objects[SHELL]
    if len(meshes) != 19 or len(shell.material_slots) != 3:
        raise ValueError("Unexpected cutaway reimport inventory")
    for obj in meshes:
        for slot in obj.material_slots:
            principal = slot.material.node_tree.nodes.get("Principled BSDF")
            slot.material.diffuse_color = principal.inputs["Base Color"].default_value
    camera = renderer["configure"](scene)
    pictures = []
    # Lesson branch camera direction, recalibrated to frame the isolated GLB in a square plate.
    source_position = gltf_to_blender((.11, .13, .44))
    source_target = gltf_to_blender((.042, .104, -.014))
    lesson_direction = source_position - source_target
    left_detail = gltf_to_blender((.000, .091, -.024))
    views = (
        ("complete", Vector((-.006, .012, .124)), lesson_direction, .147, meshes, True),
        ("wall", Vector((-.006, .012, .124)), lesson_direction, .147, [shell], True),
        ("branch", left_detail, Vector((.4, -1, .31)), .071, [shell], False),
        ("context", Vector((-.006, .012, .124)), Vector((.95, .55, .27)), .147, meshes, True),
    )
    for view, target, direction, scale, visible, palette in views:
        camera.location = target + direction.normalized() * .62
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = scale
        picture = renderer["shot"](
            scene, camera, meshes, tuple(direction), out / f"{tag}-{view}.png", palette, visible, fixed=True,
        )
        picture["targetM"] = list(target)
        if view in ("wall", "branch"):
            from bpy_extras.object_utils import world_to_camera_view

            coords = {}
            for name, position in guide.items():
                point = world_to_camera_view(scene, camera, gltf_to_blender(position))
                coords[name] = [point.x, 1 - point.y]
            picture["projectedLessonGuides"] = coords
        pictures.append(picture)
    return pictures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("render_dir", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.artifact.resolve() != ROOT / MODEL:
        raise ValueError("Expected the exact One Breath source path")
    raw = args.artifact.read_bytes()
    if identity(raw)["sha256"] != SHA256:
        raise ValueError("Wrong or unhydrated One Breath cutaway")
    output = args.render_dir.resolve()
    output.mkdir(parents=True)
    source = inventory(args.artifact, raw)
    lesson = json.loads((ROOT / "lessons/one-breath/assets.json").read_text())
    lesson_asset, = [asset for asset in lesson["assets"] if asset["id"] == "tracheaCutaway"]
    if lesson_asset["sha256"] != SHA256 or lesson_asset["source"] != MODEL:
        raise ValueError("Current historical lesson cutaway does not match the V7 evidence")
    guides = {
        "leftMain": lesson["ports"]["left"]["position"],
        "rightMain": lesson["ports"]["right"]["position"],
        "fork": lesson["route"]["main"][-1],
    }
    if guides["leftMain"][0] <= 0 or guides["rightMain"][0] >= 0:
        raise ValueError("Lesson ports lost their left/right locations")
    packed, metrics = compact_normals(raw)
    trial = output / "cutaway-normal-trial.glb"
    trial.write_bytes(packed)
    packed_inventory = inventory(trial, packed)
    if any(packed_inventory[key] != source[key] for key in ("triangles", "meshes", "primitives", "materials")):
        raise ValueError("Encoding trial changed the teaching selection")
    renderer = runpy.run_path(str(HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"))
    results = {
        "blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(),
        "source": {"path": MODEL, **source},
        "encodingTrial": {"asset": packed_inventory, **metrics},
        "portAnchorsM": guides,
        "views": {
            "original": render(renderer, "original", args.artifact, output, guides),
            "trial": render(renderer, "trial", trial, output, guides),
        },
    }
    (output / "render.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
