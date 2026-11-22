"""Disposable replay of one shared shell edit through both generated GLBs."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root))
from tools.glb import decode, buffer_view_bytes

source = root / 'models/trachea/exports/open-airway-r06/build.py'
baseline = root / 'models/trachea/exports/host-conforming-cbands-r05/trachea_host_conforming_illustration.glb'
spec = importlib.util.spec_from_file_location('airway_shell', source)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
out = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
out.mkdir(exist_ok=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
recipe.build(baseline, out / 'original')
recipe.THICKNESS *= 0.95
bpy.ops.wm.read_factory_settings(use_empty=True)
recipe.build(baseline, out / 'changed')


def inspect(file):
    raw = file.read_bytes()
    document, binary = decode(raw)
    values = {}
    for mesh in document['meshes']:
        for part in mesh['primitives']:
            name = document['materials'][part['material']]['name'].removesuffix('.001')
            attr = document['accessors'][part['attributes']['POSITION']]
            data = buffer_view_bytes(binary, document['bufferViews'][attr['bufferView']])
            points = set(struct.iter_unpack('<3f', data))
            values.setdefault(name, set()).update(points)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(file))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert len(objects) == 19
    return values, {'file': file.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'meshNames': sorted(obj.name for obj in objects)}


report = {}
for variant in ('open', 'cutaway'):
    original, before = inspect(out / 'original' / f'trachea-{variant}.glb')
    changed, after = inspect(out / 'changed' / f'trachea-{variant}.glb')
    _, retained = inspect(source.parent / f'trachea-{variant}.glb')
    interior = 'Illustrative inner shell - not segmented mucosa'
    surface = 'Illustrative external display surface'
    bands = 'Retained illustrative C-bands'
    assert original.keys() == changed.keys()
    assert original[interior] != changed[interior]
    assert original[surface] == changed[surface]
    assert original[bands] == changed[bands]
    assert before['meshNames'] == after['meshNames']
    report[variant] = {'retainedDelivery': retained, 'originalReplay': before, 'disposableChange': after,
                       'uniqueInteriorPositionsChanged': len(changed[interior] - original[interior]),
                       'outerAndBandPositionsIdentical': True}
(out / 'replay.json').write_text(json.dumps({'blender': bpy.app.version_string,
   'source': str(source.relative_to(root)), 'baseline': recipe.BASELINE_SHA256, 'variants': report}, indent=2) + '\n')
print('PASS one shared shell thickness edit reached both exact selections; clean imports retained all names and outer positions.')
