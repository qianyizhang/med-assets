"""Blender 4.3.2: matched exact-export diagnostic renders into a NEW directory.

blender -b --python tests/eye_anterior_segment/detail_review.py -- --output /tmp/eye-detail-NEW
No geometry/material edits or exports. Layer hiding is an editorial inspection aid.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = 'models/eye_anterior_segment/exports/hra-v1.3-r01/anterior_segment.glb'
SHA256 = '457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
if hashlib.sha256((ROOT / ARTIFACT).read_bytes()).hexdigest() != SHA256:
    raise ValueError('Exact reviewed export required')
args.output.mkdir(parents=True, exist_ok=False)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT / ARTIFACT))
objects = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
if len(objects) != 7:
    raise ValueError('Expected seven imported mesh nodes')
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.cycles.use_denoising = False
scene.cycles.seed = 0
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.11, .11, .11)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
points = [o.matrix_world @ v.co for o in objects.values() for v in o.data.vertices]
lo = Vector([min(v[i] for v in points) for i in range(3)])
hi = Vector([max(v[i] for v in points) for i in range(3)])
center = (lo + hi) / 2
extent = max(hi - lo)
for delta, power in [((-2, -3, 3), 420), ((3, -1, 1), 180), ((0, 3, 2), 280)]:
    bpy.ops.object.light_add(type='AREA', location=center + Vector(delta))
    light = bpy.context.object
    light.data.energy, light.data.size = power, 2
    light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = 'ORTHO'
scene.camera = camera
ciliary = ['VH_M_ciliary_body_R', 'VH_M_ciliary_muscle_R', 'VH_M_ciliary_processes_R',
           'VH_M_suspensory_ligament_of_lens_R']
isolation = ['VH_M_cornea_R', 'VH_M_iris_R', 'VH_M_ciliary_body_R', 'VH_M_ciliary_muscle_R']
# Detail targets use the same imported native frame. Paired full/hidden views have
# IDENTICAL camera, projection, lighting and exposure; only visibility differs.
# A 5.5-mm patch straddles lens margin and ciliary rim on the superior side.
zonule_target = center + Vector((0, 0, .0048))
views = [
    ('posterior-context', center, (0, 2, .2), extent * 1.2, []),
    ('posterior-detail-full', zonule_target, (0, 2, .2), .0055, []),
    ('posterior-detail-isolated', zonule_target, (0, 2, .2), .0055, isolation),
    ('oblique-detail-full', zonule_target, (1, 2, .6), .0055, []),
    ('oblique-detail-isolated', zonule_target, (1, 2, .6), .0055, isolation),
    ('anterior-order-full', center, (2, -1, .4), extent * 1.2, []),
    ('anterior-order-three-structures', center, (2, -1, .4), extent * 1.2, ciliary),
    ('corneal-profile-full', center, (2, 0, 0), extent * 1.05, []),
    ('corneal-profile-three-structures', center, (2, 0, 0), extent * 1.05, ciliary),
]
rows = []
for name, target, delta, scale, hidden in views:
    for node, obj in objects.items():
        obj.hide_render = node in hidden
    camera.location = target + Vector(delta)
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    image = args.output / (name + '.png')
    scene.render.filepath = str(image)
    bpy.ops.render.render(write_still=True)
    rows.append({'view': name, 'file': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                 'bytes': image.stat().st_size, 'cameraLocation': list(camera.location),
                 'target': list(target), 'orthoScaleM': camera.data.ortho_scale,
                 'visibleNodes': sorted(set(objects) - set(hidden)), 'hiddenNodes': sorted(hidden)})
receipt = {'artifact': {'file': ARTIFACT, 'sha256': SHA256}, 'renderer': bpy.app.version_string,
           'engine': 'Cycles CPU', 'samples': 48, 'seed': 0, 'denoising': False,
           'resolution': [1000, 1000], 'viewTransform': 'AgX', 'look': scene.view_settings.look,
           'exposure': 0, 'gamma': 1, 'geometryAndMaterialsEdited': False,
           'scope': 'Exact-export diagnostic pixels. Visibility changes are not physical sections or anatomical validation.',
           'views': rows}
(args.output / 'render-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS nine matched local diagnostic views; inspect pixels before any visual/anatomy decision.')
