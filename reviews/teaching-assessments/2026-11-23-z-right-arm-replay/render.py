"""Cleanly import the three assessed right-arm GLBs and render their six plate views."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SIZE = 560
sys.path.insert(0, str(ROOT / 'tools'))
from render_teaching import sha256

sys.path.insert(0, str(ROOT / 'lessons/right-arm-parts'))
from arm_scene import blender_axes, set_up_scene


def views():
    joint_source = ROOT / 'sources/datasets/z-anatomy/joint-regional-studies/camera-contract.json'
    joint_regions = json.loads(joint_source.read_text())['regions']
    result = {}
    for study in ('elbow', 'shoulder'):
        region = joint_regions[study]
        result[study] = [
            (
                Path(row['file']).stem,
                blender_axes(row['target_three']),
                blender_axes(row['position_three']) - blender_axes(row['target_three']),
                region['ortho_vertical_span'],
                row['hidden_for_inspection_only'],
            )
            for row in region['views']
            if row['file'] in ('anterior.png', 'deep-oblique.png')
        ]

    ulnar_source = ROOT / 'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v2/raw-128/bindings.json'
    ulnar_views = {
        row['file']: row for row in json.loads(ulnar_source.read_text())['views']
    }
    result['ulnar'] = []
    for name, direction in (('posteromedial', (1, 1, 0)), ('medial', (1, 0, 0))):
        row = ulnar_views[f'elbow-{name}.png']
        result['ulnar'].append((name, Vector(row['target']), Vector(direction), row['ortho_scale'], ()))
    return result


def render(out):
    assessed = json.loads((HERE / 'campaign-assessments.json').read_text())['assessments']
    inputs = {
        Path(row['teachingView']).stem.removesuffix('-teaching'): row['export']
        for row in assessed
    }
    cameras = views()
    if inputs.keys() != cameras.keys():
        raise ValueError('The assessed selections differ from the plate camera sets')
    for item in inputs.values():
        if sha256(ROOT / item['path']) != item['sha256']:
            raise ValueError(f"Assessed GLB identity mismatch: {item['path']}")
    out.mkdir(parents=True, exist_ok=False)

    for study, item in inputs.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        imported = bpy.ops.import_scene.gltf(filepath=str(ROOT / item['path']))
        if imported != {'FINISHED'}:
            raise RuntimeError(f"Could not import {item['path']}")
        bpy.context.view_layer.update()
        scene = bpy.context.scene
        meshes = {
            obj.name.removesuffix(' candidate'): obj
            for obj in scene.objects if obj.type == 'MESH'
        }
        camera, lights = set_up_scene(scene, SIZE, SIZE)
        for name, target, direction, scale, hide in cameras[study]:
            if not set(hide).issubset(meshes):
                raise ValueError(f'Unknown hidden mesh for {study}/{name}')
            for label, obj in meshes.items():
                obj.hide_render = label in hide
            camera.location = target + direction.normalized() * 1.5
            rotation = (target - camera.location).to_track_quat('-Z', 'Y')
            camera.rotation_euler = rotation.to_euler()
            camera.data.ortho_scale = scale
            for light, offset in lights:
                light.location = target + rotation @ offset
                light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(out / f'{study}-{name}.png')
            bpy.context.view_layer.update()
            bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    render(args.out.resolve())
