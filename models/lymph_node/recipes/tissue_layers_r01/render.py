"""Render matched actual exports and the four named HRA tissue selections."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
SELECTION = Path(__file__).with_name('selection.json')
CAPSULE = "Yao_capsule_of_lymph_node"
FOLLICLES = "Yao_follicles"
MEDULLA = "Yao_medulla_of_lymph_node"
PARACORTEX = "Yao_paracortex"
REGIONS = (FOLLICLES, PARACORTEX, MEDULLA)
RES = 650


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def import_scene(path, expected):
    if identity(path) != {k: expected[k] for k in ("bytes", "sha256")}:
        raise ValueError(f"Wrong exact export: {path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    scene = bpy.context.scene
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    bpy.context.view_layer.update()
    for obj in meshes.values():
        obj.data.calc_loop_triangles()
    return scene, meshes


def lighting(scene, target):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.seed = 14
    scene.render.resolution_x = scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    scene.world = bpy.data.worlds.new("Soft environment")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (.2, .2, .2, 1)
    bg.inputs["Strength"].default_value = .35
    for name, position, energy, radius in (
        ("Large key", (-.018, -.024, .026), .031, .028),
        ("Fill", (.026, -.010, .006), .015, .023),
        ("Rear", (.006, .028, .018), .024, .026),
    ):
        area = bpy.data.lights.new(name, "AREA")
        area.shape = "DISK"
        area.energy = energy
        area.size = radius
        obj = bpy.data.objects.new(name, area)
        scene.collection.objects.link(obj)
        obj.location = target + Vector(position)
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera = bpy.data.objects.new("Orthographic lymph-node review", bpy.data.cameras.new("Review"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = .0001
    camera.data.clip_end = 1
    neutral = bpy.data.materials.new("Neutral review finish")
    neutral.use_nodes = True
    shader = neutral.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (.50, .44, .38, 1)
    shader.inputs["Roughness"].default_value = .66
    return camera, neutral


def render(scene, camera, neutral, meshes, pose, shown, finish, file):
    if not set(shown) <= meshes.keys():
        raise ValueError("View requests a missing named tissue")
    for name, obj in meshes.items():
        obj.hide_render = name not in shown
    camera.location = pose["cameraM"]
    target = Vector(pose["targetM"])
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = pose["orthoScaleM"]
    bpy.context.view_layer.material_override = neutral if finish == "neutral" else None
    scene.render.filepath = str(file.resolve())
    bpy.ops.render.render(write_still=True)
    return {"file": file.name, **identity(file), "visible": list(shown), "finish": finish,
            **{k: pose[k] for k in ("cameraM", "targetM", "orthoScaleM")}}


def inspection_inputs(key, names):
    common = [
        ("primary-capsule", "primary", (CAPSULE,), "source"),
        ("primary-regions", "primary", REGIONS, "source"),
        ("reverse-capsule", "reverse", (CAPSULE,), "source"),
        ("reverse-regions", "reverse", REGIONS, "source"),
    ]
    if key == "source":
        return [("primary-all", "primary", tuple(names), "source"), *common]
    return [
        *common,
        ("primary-neutral-capsule", "primary", (CAPSULE,), "neutral"),
        ("primary-neutral-regions", "primary", REGIONS, "neutral"),
        ("reverse-neutral-capsule", "reverse", (CAPSULE,), "neutral"),
        ("reverse-neutral-regions", "reverse", REGIONS, "neutral"),
        ("primary-follicles", "primary", (FOLLICLES,), "source"),
        ("primary-paracortex", "primary", (PARACORTEX,), "source"),
        ("primary-medulla", "primary", (MEDULLA,), "source"),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    build = json.loads(args.build_report.read_text())
    poses = json.loads(SELECTION.read_text())['cameras']
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(),
              "engine": "Cycles CPU, 32 samples; AgX; exact source materials or declared neutral override",
              "resolution": [RES, RES], "models": {}}
    paths = {"source": ROOT / build["source"]["path"], "candidate": args.candidate}
    for key, path in paths.items():
        scene, meshes = import_scene(path, build[key])
        expected = set(build["verifiedRetained"])
        if key == "source":
            expected |= set(build["intentionalOmissions"])
        if set(meshes) != expected:
            raise ValueError("Clean import did not preserve the expected mesh set")
        camera, neutral = lighting(scene, Vector(poses["primary"]["targetM"]))
        views = [render(scene, camera, neutral, meshes, poses[angle], shown, finish,
                        args.output / f"{key}-{file}.png")
                 for file, angle, shown, finish in inspection_inputs(key, meshes)]
        result["models"][key] = {
            **identity(path), "views": views,
            "triangles": {name: len(obj.data.loop_triangles) for name, obj in meshes.items()},
            "world_matrices": {name: [list(row) for row in obj.matrix_world] for name, obj in meshes.items()},
        }
    (args.output / "render.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
