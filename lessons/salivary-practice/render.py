"""Render salivary practice layers from the exact Gallery GLBs."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
VIEWS = Path(__file__).with_name("views.json")
EXPORTS = ROOT / "models/salivary_glands/exports"

sys.path.insert(0, str(ROOT / "tools"))
from render_teaching import area_light, configure_scene


def blender_coordinates(gltf):
    x, y, z = gltf
    return Vector((x, -z, y))


def render_layer(path, pose, layer, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    scene = bpy.context.scene
    selected = set(layer["nodes"])
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    if missing := selected - meshes.keys():
        raise ValueError(f"{path.name} is missing {sorted(missing)}")
    for name, obj in meshes.items():
        obj.hide_render = name not in selected
    configure_scene(scene)
    width, height = 960, 720
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.cycles.samples = 24
    target = blender_coordinates(pose["target"])
    scene.camera.location = blender_coordinates(pose["position"])
    scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera.data.ortho_scale = pose["height"] * width / height
    scene.camera.data.clip_start = 0.001
    scene.camera.data.clip_end = 5
    area_light(scene, target, 0.12, "Key", (2, -3, 4), 540, 3)
    area_light(scene, target, 0.12, "Fill", (-3, -2, 1), 240, 4)
    area_light(scene, target, 0.12, "Rim", (1, 3, 3), 350, 4)
    scene.render.filepath = str(output / f"{layer['id']}.png")
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--edition", choices=("z-native-shared-r01", "z-native-scoped-r02"),
                        default="z-native-shared-r01")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    args.out.mkdir(parents=True, exist_ok=False)
    for view in json.loads(VIEWS.read_text()).values():
        for layer in view["layers"]:
            render_layer(EXPORTS / args.edition / layer["file"], view["camera"], layer,
                         args.out.resolve())


if __name__ == "__main__":
    main()
