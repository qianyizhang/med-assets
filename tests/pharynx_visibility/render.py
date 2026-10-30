"""Offline render of exact GLB and controller-selected visibility; not browser pixels."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector
from mathutils import Matrix

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--states', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--fit-comparison', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = Path(__file__).resolve().parents[2]
glb = root / 'models/pharynx_larynx/exports/r03/pharynx_larynx.glb'
states = json.loads(args.states.read_text())
sha = lambda value: hashlib.sha256(value).hexdigest()
assert sha(glb.read_bytes()) == states['sourceSha256']
args.output.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(glb))
parts = {obj['source_file_id']: obj for obj in bpy.context.scene.objects if obj.type == 'MESH'}
assert len(parts) == 33 and set(parts) == set(states['states']['baseline'])


def signature(obj):
    raw = bytearray()
    for vertex in obj.data.vertices:
        raw.extend(struct.pack('<3f', *vertex.co))
    for face in obj.data.polygons:
        raw.extend(struct.pack('<' + 'I' * len(face.vertices), *face.vertices))
    for normal in obj.data.corner_normals:
        raw.extend(struct.pack('<3f', *normal.vector))
    return {'meshNormalsSha256': sha(raw), 'worldMatrix': [list(row) for row in obj.matrix_world],
            'name': obj.name, 'materials': [mat.name for mat in obj.data.materials]}


before = {id: signature(obj) for id, obj in parts.items()}


def bounds(ids):
    points = [parts[id].matrix_world @ Vector(corner) for id in ids for corner in parts[id].bound_box]
    lo = Vector([min(point[i] for point in points) for i in range(3)])
    hi = Vector([max(point[i] for point in points) for i in range(3)])
    return (lo + hi) / 2, max(hi - lo)


center, extent = bounds(parts)
detail, detail_extent = bounds(states['states']['cartilage'])
views = [
    ('front', center, Vector((0, -1, 0)), extent * 1.17),
    ('posterior-oblique', center, Vector((.6, 1, .25)), extent * 1.17),
    ('cartilage-detail', detail, Vector((.35, 1, .5)), detail_extent * 1.3),
]
scene = bpy.context.scene
scene.world = bpy.data.worlds.new('ReviewWorld')
scene.world.color = (.11, .11, .11)
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 32
scene.cycles.use_denoising, scene.cycles.seed = False, 0
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
for delta, energy in [((-2, -3, 3), 420), ((3, -1, 1), 180), ((0, 3, 2), 280)]:
    bpy.ops.object.light_add(type='AREA', location=center + Vector(delta))
    light = bpy.context.object
    light.data.energy, light.data.size = energy, 2
    light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = 'ORTHO'
scene.camera = camera
rows = []
if args.fit_comparison:
    def blender_vector(value):
        return Vector((value[0], -value[2], value[1]))
    views = [(row['label'], blender_vector(row['targetThree']),
              blender_vector(row['positionThree']) - blender_vector(row['targetThree']), None)
             for row in states['cameras']]
for view, target, direction, span in views:
    camera.location = target + direction
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    if args.fit_comparison:
        current = next(row for row in states['cameras'] if row['label'] == view)
        forward = -direction.normalized()
        up = blender_vector(current['upThree'])
        right = forward.cross(up).normalized()
        up = right.cross(forward).normalized()
        camera.rotation_euler = Matrix((right, up, -forward)).transposed().to_euler()
        camera.data.type = 'PERSP'
        camera.data.sensor_fit = 'VERTICAL'
        camera.data.sensor_height = 32
        camera.data.lens = 32 / (2 * math.tan(math.radians(current['fovVerticalDegrees']) / 2))
        camera.data.clip_start, camera.data.clip_end = current['near'], current['far']
        active_states = {current['state']: states['states'][current['state']]}
    else:
        camera.data.ortho_scale = span
        active_states = states['states']
    for state, ids in active_states.items():
        if state in ('reset', 'muscles') and view == 'cartilage-detail':
            continue
        for id, obj in parts.items():
            obj.hide_render = id not in ids
        path = args.output / f'{state}-{view}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rows.append({'view': view, 'state': state, 'visibleSourceIds': ids, 'file': path.name,
                     'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
                     'cameraPositionBlender': list(camera.location), 'targetBlender': list(target),
                     'orthoVerticalSpan': span, 'cameraType': camera.data.type,
                     'controllerCamera': current if args.fit_comparison else None})
assert before == {id: signature(obj) for id, obj in parts.items()}
receipt = {'sourceSha256': states['sourceSha256'], 'controllerSha256': states['controllerSha256'],
           'renderer': bpy.app.version_string, 'engine': 'Cycles CPU', 'samples': 32, 'seed': 0,
           'resolution': [900, 900], 'viewTransform': 'AgX', 'look': scene.view_settings.look,
           'denoising': False, 'exposure': 0, 'gamma': 1, 'geometryTransformsMaterialsUnchanged': True,
           'meshIdentities': before, 'views': rows,
           'scope': ('Offline perspective fit illustrations from a clean import of the unchanged exact GLB. '
                     'The before/after fit comparison changes camera target and distance while retaining the same five parts, '
                     'viewing direction, source positions and materials. Full/reset fitted views show all 33 parts. Not WebGL or UI screenshots.'
                     if args.fit_comparison else
                     'Offline visibility illustrations from a clean import of the unchanged exact GLB. Native scene positions; only visibility differs between panels. Not WebGL or UI screenshots.')}
(args.output / 'render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS unchanged geometry/transforms/materials; actual offline render files and source bindings recorded')
