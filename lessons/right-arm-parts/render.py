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
REPLAY = ROOT / 'reviews/teaching-assessments/2026-11-23-z-right-arm-replay'
GALLERY = ROOT / 'sites/anatomy-gallery/app/src/content/gallery'
sys.path.insert(0, str(REPLAY))
from render import blender_axes, set_up_scene

CUFF_REVIEW = ROOT / 'reviews/joints/2026-10-30-rotator-cuff-r01/checks.json'
NERVE_REVIEW = ROOT / 'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v2/raw-128/bindings.json'
WIDTH = 640
HEIGHT = 480


def anchors():
    nerve_views = json.loads(NERVE_REVIEW.read_text())['views']
    elbow = next(row for row in nerve_views if row['file'] == 'elbow-posteromedial.png')
    elbow_keys = {'nerve', 'medial_epicondyle', 'olecranon'}
    cuff = json.loads(CUFF_REVIEW.read_text())['exportViews']
    return {
        'elbow-nerve': {a['key']: a['world'] for a in elbow['anchors'] if a['key'] in elbow_keys},
        **{
            'shoulder-' + Path(row['file']).stem: {a['id']: a['world'] for a in row['anchors']}
            for row in cuff if row['file'] in ('anterior.png', 'posterior.png')
        },
    }


def render(out):
    bindings = json.loads((GALLERY / 'arm-lesson-layers.json').read_text())
    review_anchors = anchors()
    projections = {}
    out.mkdir(parents=True, exist_ok=False)
    for region, lesson in bindings.items():
        for layer in lesson['layers']:
            glb = ROOT / layer['path']
            if hashlib.sha256(glb.read_bytes()).hexdigest() != layer['sha256']:
                raise ValueError(f'Exact source GLB differs from {layer["sha256"]}: {glb}')
            bpy.ops.wm.read_factory_settings(use_empty=True)
            if bpy.ops.import_scene.gltf(filepath=str(glb)) != {'FINISHED'}:
                raise RuntimeError(f'Could not import {glb}')
            scene = bpy.context.scene
            meshes = {obj.name: obj for obj in scene.objects if obj.type == 'MESH'}
            if not set(layer['nodes']).issubset(meshes):
                raise ValueError(f'Missing selected meshes in {glb}')
            for name, obj in meshes.items():
                obj.hide_render = name not in layer['nodes']

            camera, lights = set_up_scene(scene)
            scene.render.resolution_x = WIDTH
            scene.render.resolution_y = HEIGHT
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
                for anchor, position in review_anchors.get(name, {}).items():
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
