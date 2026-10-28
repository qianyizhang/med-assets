"""Blender 4.3.2 clean export reimport and matched context/detail comparison."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time

import bpy
from mathutils import Vector

spec = importlib.util.spec_from_file_location('eye_build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source = args.baseline.read_bytes()
candidate = args.candidate.read_bytes()
expected, _ = build.build(source)
build.require(candidate == expected, 'Candidate differs from deterministic export')
args.output.mkdir(parents=True, exist_ok=False)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    start = time.perf_counter()
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    return objects, time.perf_counter() - start


def imported_signature(obj):
    mesh = obj.data
    raw = bytearray()
    for v in mesh.vertices:
        raw.extend(struct.pack('<3f', *v.co))
    for polygon in mesh.polygons:
        raw.extend(struct.pack('<I', len(polygon.vertices)))
        raw.extend(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
    for normal in mesh.corner_normals:
        raw.extend(struct.pack('<3f', *normal.vector))
    return {'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons),
            'geometryAndNormalsSha256': hashlib.sha256(raw).hexdigest(),
            'worldMatrix': [list(row) for row in obj.matrix_world],
            'materials': [m.name for m in mesh.materials]}


baseline_objects, baseline_seconds = load(args.baseline)
signatures = {name: imported_signature(obj) for name, obj in baseline_objects.items()}
points = [o.matrix_world @ v.co for o in baseline_objects.values() for v in o.data.vertices]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
center, extent = (lo + hi) / 2, max(hi - lo)
views = [('context', center, Vector((2, -1, .4)), extent * 1.2),
         ('detail', center + Vector((0, 0, .0048)), Vector((1, 2, .6)), .0055)]
rows, imports = [], []
for variant, path in [('baseline', args.baseline), ('candidate', args.candidate)]:
    objects, seconds = load(path)
    expected_names = build.KEEP + build.OMIT if variant == 'baseline' else build.KEEP
    build.require(set(objects) == set(expected_names), 'Unexpected imported object inventory')
    actual = {name: imported_signature(obj) for name, obj in objects.items()}
    build.require(all(actual[name] == signatures[name] for name in objects), 'Clean reimport changed retained data')
    imports.append({'variant': variant, 'seconds': seconds, 'meshes': actual})
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('ReviewWorld')
    scene.world.color = (.11, .11, .11)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 48
    scene.cycles.use_denoising, scene.cycles.seed = False, 0
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    for delta, power in [((-2, -3, 3), 420), ((3, -1, 1), 180), ((0, 3, 2), 280)]:
        bpy.ops.object.light_add(type='AREA', location=center + Vector(delta))
        light = bpy.context.object
        light.data.energy, light.data.size = power, 2
        light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    scene.camera = camera
    for name, target, direction, scale in views:
        camera.location = target + direction
        camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        path = args.output / f'{variant}-{name}.png'
        scene.render.filepath = str(path)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        rows.append({'variant': variant, 'view': name, 'file': path.name,
                     'sha256': build.sha(path.read_bytes()), 'bytes': path.stat().st_size,
                     'seconds': time.perf_counter() - started, 'visibleNodes': sorted(objects),
                     'cameraLocation': list(camera.location), 'target': list(target),
                     'orthoScaleM': camera.data.ortho_scale})
receipt = {'baselineSha256': build.sha(source), 'candidateSha256': build.sha(candidate),
           'renderer': bpy.app.version_string, 'engine': 'Cycles CPU', 'samples': 48, 'seed': 0,
           'resolution': [1000, 1000], 'viewTransform': 'AgX', 'look': 'AgX - Medium High Contrast',
           'denoising': False, 'exposure': 0, 'gamma': 1, 'imports': imports, 'views': rows,
           'scope': 'Clean native GLB imports and matched pixels; no browser, anatomical or clinical acceptance.'}
(args.output / 'reimport-render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS clean native reimports and four matched export renders; visual review still required')
