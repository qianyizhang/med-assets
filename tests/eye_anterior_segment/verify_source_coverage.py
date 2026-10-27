#!/usr/bin/env python3
"""Check exact pinned HRA mesh-node coverage; no anatomical inference."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'sources/datasets/hra/eye-male-right-v1.3/hra-source.glb'
INVENTORY = ROOT / 'reviews/eye_anterior_segment/2026-10-27-source-coverage-r01/source-inventory.json'
RECORD = ROOT / 'reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/record.json'
source = SOURCE.read_bytes()
expected = json.loads((SOURCE.parent / 'source.json').read_text())
assert len(source) == expected['bytes']
assert hashlib.sha256(source).hexdigest() == expected['sha256']
assert source[:4] == b'glTF' and struct.unpack_from('<I', source, 8)[0] == len(source)
json_size, chunk_type = struct.unpack_from('<II', source, 12)
assert chunk_type == 0x4E4F534A
model = json.loads(source[20:20 + json_size])
mesh_nodes = [n for n in model['nodes'] if 'mesh' in n]
assert all(0 <= n['mesh'] < len(model['meshes']) for n in mesh_nodes)
assert len({n['mesh'] for n in mesh_nodes}) == len(mesh_nodes)
assert len({n['name'] for n in mesh_nodes}) == len(mesh_nodes)
rows = []
for node in mesh_nodes:
    mesh = model['meshes'][node['mesh']]
    names = []
    for prim in mesh['primitives']:
        mat = prim.get('material')
        names.append(model['materials'][mat].get('name') if mat is not None else None)
    rows.append({'node': node['name'], 'mesh': node['mesh'], 'materials': names})
record = json.loads(RECORD.read_text())
selected = record['sourceScope']['selectedNodes']
assert len(selected) == 7 and len(set(selected)) == 7
assert set(selected) <= {r['node'] for r in rows}
assert len(rows) == 23 and len(rows) - len(selected) == 16
assert len(model['meshes']) == 23 and len(model['materials']) == 21
inventory = json.loads(INVENTORY.read_text())
assert inventory['sourceSha256'] == expected['sha256']
assert inventory['meshNodes'] == rows
assert inventory['selectedNodes'] == selected
assert inventory['noSeparatelyNamedNodes'] == [
    'optic nerve', 'extraocular muscles', 'long posterior ciliary artery'
]
assert all(not any(term in r['node'].lower() for term in ('optic_nerve', 'rectus', 'oblique', 'artery')) for r in rows)
assert any(r['node'] == 'VH_M_optic_disc_R' for r in rows)
assert any(r['node'] == 'VH_M_ciliary_muscle_R' for r in rows)
print('PASS exact pinned GLB: 23 mesh nodes; 7 selected, 16 excluded; named coverage reconciled.')
