"""Render the Gallery's right-arm lesson plates from the exact selected GLBs."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from arm_scene import blender_axes, set_up_scene

WIDTH = 640
HEIGHT = 480


def render(out):
    bindings = json.loads((HERE / 'arm-lesson-layers.json').read_text())
    anchors = json.loads((HERE / 'anchors.json').read_text())
    for lesson in bindings.values():
        for layer in lesson['layers']:
            glb = ROOT / layer['path']
            data = glb.read_bytes()
            if len(data) != layer['bytes'] or hashlib.sha256(data).hexdigest() != layer['sha256']:
                raise ValueError(f'Exact source GLB differs from {layer["sha256"]}: {glb}')

    projections = {}
    out.mkdir(parents=True, exist_ok=False)
    for region, lesson in bindings.items():
        for layer in lesson['layers']:
            glb = ROOT / layer['path']
            bpy.ops.wm.read_factory_settings(use_empty=True)
            if bpy.ops.import_scene.gltf(filepath=str(glb)) != {'FINISHED'}:
                raise RuntimeError(f'Could not import {glb}')
            scene = bpy.context.scene
            meshes = {obj.name: obj for obj in scene.objects if obj.type == 'MESH'}
            if not set(layer['nodes']).issubset(meshes):
                raise ValueError(f'Missing selected meshes in {glb}')
            for name, obj in meshes.items():
                obj.hide_render = name not in layer['nodes']

            camera, lights = set_up_scene(scene, WIDTH, HEIGHT)
            config = lesson['camera']
            target = blender_axes(config['target'])
            camera.data.ortho_scale = config['height'] * WIDTH / HEIGHT
            directions = {
                f'{region}-{layer["id"]}': blender_axes(config['position']) - target,
            }
            if layer['id'] == 'cuff':
                directions['shoulder-posterior'] = (0, 1, 0)
                directions['shoulder-anterior'] = (0, -1, 0)
            for name, direction in directions.items():
                camera.location = target + Vector(direction).normalized() * 1.5
                rotation = (target - camera.location).to_track_quat('-Z', 'Y')
                camera.rotation_euler = rotation.to_euler()
                for light, offset in lights:
                    light.location = target + rotation @ offset
                    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
                bpy.context.view_layer.update()
                projections[name] = {}
                for anchor, position in anchors.get(name, {}).items():
                    screen = world_to_camera_view(scene, camera, Vector(position))
                    projections[name][anchor] = [round(screen.x * WIDTH), round((1 - screen.y) * HEIGHT)]
                scene.render.filepath = str(out / f'{name}.png')
                bpy.ops.render.render(write_still=True)
    (out / 'projections.json').write_text(json.dumps(projections, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    arguments = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    render(arguments.out.resolve())
