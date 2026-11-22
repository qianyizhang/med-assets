"""Reimport the two pinned r01 GLBs and render matched diagnostic views."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

OVARY = ("models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb",
         "465a44b18df91ece95a236372a8cbe3e1a0de0207525955290e6b0fa519195d1", 681552)
WALL = ("models/esophagus_wall/exports/authored-cutaway-r01/esophagus-wall-cutaway-r01.glb",
        "e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5", 201328)
LIGHTS = [((-.6, -.7, .8), 14), ((.5, -.3, .1), 7), ((0, .5, .5), 10)]


def identity(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def open_export(root, export, expected_count):
    path, sha, size = export
    if identity(root / path) != {"sha256": sha, "bytes": size}:
        raise ValueError(f"Wrong export revision: {path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(root / path), merge_vertices=False)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    if len(meshes) != expected_count:
        raise ValueError(f"Wrong reimport mesh count: {path}")
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.seed = 17
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Diagnostic world")
    scene.world.color = (.1, .1, .1)
    scene.view_settings.view_transform = "AgX"

    camera_data = bpy.data.cameras.new("Review camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("Review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    neutral = bpy.data.materials.new("Matched diagnostic")
    neutral.use_nodes = True
    shader = neutral.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (.44, .39, .34, 1)
    shader.inputs["Roughness"].default_value = .8
    return scene, meshes, neutral


def crop(objects):
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    lower = Vector([min(point[i] for point in points) for i in range(3)])
    upper = Vector([max(point[i] for point in points) for i in range(3)])
    return (lower + upper) / 2, max(upper - lower)


def capture(scene, neutral, output, name, visible, target, scale, directions):
    lights = []
    factor = scale / .15
    for offset, power in LIGHTS:
        data = bpy.data.lights.new("Broad diagnostic light", "AREA")
        data.shape = "DISK"
        data.size = .4 * factor
        data.energy = power * factor ** 2
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        light.location = target + Vector(offset) * factor
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
        lights.append(light)
    for mesh in [obj for obj in scene.objects if obj.type == "MESH"]:
        mesh.hide_render = mesh not in visible
    camera = scene.camera
    camera.data.ortho_scale = scale
    rows = []
    for angle, direction, timings in directions:
        camera.location = target + Vector(direction).normalized() * .30
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        for finish in timings:
            scene.view_layers[0].material_override = neutral if finish == "neutral" else None
            file = output / f"{name}-{angle}-{finish}.png"
            scene.render.filepath = str(file)
            bpy.ops.render.render(write_still=True)
            rows.append({
                "file": file.name, **identity(file), "angle": angle, "material": finish,
                "targetM": list(target), "orthoScaleM": scale, "cameraM": list(camera.location),
                "cameraQuaternion": list(camera.rotation_euler.to_quaternion()),
                "visibleNodes": sorted(obj.name for obj in visible),
            })
    for lamp in lights:
        bpy.data.objects.remove(lamp, do_unlink=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    args.output.mkdir(parents=True, exist_ok=False)
    scene, meshes, material = open_export(args.root, OVARY, 10)
    ovary = []
    for side, word in [("L", "left"), ("R", "right")]:
        objects = [meshes[f"VH_F_{word}_ovary"], meshes[f"VH_F_fibria_of_uterine_tube_{side}"]]
        target, span = crop(objects)
        context = [obj for name, obj in meshes.items() if name.endswith(f"_{side}") or obj in objects]
        ovary.extend(capture(scene, material, args.output, f"ovary-{side}", context,
                             target, span * 1.45,
                             [("native", (0, -1, 0), ("palette", "neutral")),
                              ("alternate", (.85, -.3, .5), ("neutral",))]))
    scene, meshes, material = open_export(args.root, WALL, 5)
    wall = capture(scene, material, args.output, "wall", list(meshes.values()),
                   Vector((0, 0, .037)), .034,
                   [("wedge", (.68, -1.7, 1.16), ("palette", "neutral")),
                    ("alternate", (-.74, -1.42, 1.30), ("neutral",))])
    result = {
        "blender": bpy.app.version_string,
        "blenderBuild": bpy.app.build_hash.decode(),
        "capture": {"resolution": [960, 960], "engine": "Cycles CPU", "samples": 48,
                    "seed": 17, "denoising": False, "display": "AgX", "worldColor": [.1] * 3,
                    "lightOffsetsAndPowers": LIGHTS, "rigFactor": "orthoScaleM / 0.15",
                    "diskSizeFactor": .4, "neutralBaseColor": [.44, .39, .34, 1],
                    "neutralRoughness": .8},
        "exports": [{"path": path, "sha256": sha, "bytes": size, "views": views}
                    for (path, sha, size), views in [(OVARY, ovary), (WALL, wall)]],
    }
    (args.output / "render.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
