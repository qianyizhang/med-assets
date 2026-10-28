#!/usr/bin/env python3
"""Verify the pinned HRA inventory and its partition; no anatomical inference."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = 'sources/datasets/hra/eye-male-right-v1.3/hra-source.glb'
INVENTORY_FILE = 'reviews/eye_anterior_segment/2026-10-27-source-coverage-r01/source-inventory.json'
RECORD_FILE = 'reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/record.json'
SOURCE_SHA256 = '1a6ecc528e98e0bddb8e2905e4ddb799eb471383f7274dbb9bdd1676b06be73b'
SOURCE_BYTES = 20697584
ABSENT_NAMES = ['optic nerve', 'extraocular muscles', 'long posterior ciliary artery']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_inventory(model, inventory, record):
    """Stdlib contract, also exercised on synthetic glTF in offline CI."""
    require(inventory['sourceFile'] == SOURCE_FILE, 'inventory sourceFile mismatch')
    require(type(inventory['sourceBytes']) is int and inventory['sourceBytes'] == SOURCE_BYTES,
            'inventory sourceBytes mismatch')
    require(inventory['sourceSha256'] == SOURCE_SHA256, 'inventory sourceSha256 mismatch')
    require(type(inventory['meshNodeCount']) is int and inventory['meshNodeCount'] == 23,
            'inventory meshNodeCount mismatch')
    meshes, materials = model['meshes'], model['materials']
    nodes = [n for n in model['nodes'] if 'mesh' in n]
    require(len(nodes) == len(meshes) == 23 and len(materials) == 21, 'source counts mismatch')
    require(all(type(n['mesh']) is int and 0 <= n['mesh'] < len(meshes) for n in nodes),
            'invalid mesh index')
    require(len({n['mesh'] for n in nodes}) == len(nodes), 'duplicate mesh references')
    names = [n['name'] for n in nodes]
    require(all(isinstance(n, str) and n for n in names) and len(set(names)) == 23,
            'missing or duplicate node names')
    rows = []
    for node in nodes:
        material_names = []
        for primitive in meshes[node['mesh']]['primitives']:
            index = primitive.get('material')
            require(index is None or type(index) is int and 0 <= index < len(materials),
                    'invalid material index')
            material_names.append(materials[index].get('name') if index is not None else None)
        rows.append({'node': node['name'], 'mesh': node['mesh'], 'materials': material_names})
    require(inventory['meshNodes'] == rows, 'mesh/node/material inventory mismatch')
    selected = record['sourceScope']['selectedNodes']
    excluded = record['sourceScope']['excludedSourceMeshes']
    require(len(selected) == len(set(selected)) == 7, 'selected list must contain 7 unique names')
    require(len(excluded) == len(set(excluded)) == 16, 'excluded list must contain 16 unique names')
    require(set(selected).isdisjoint(excluded) and set(selected) | set(excluded) == set(names),
            'selected/excluded lists must partition every source mesh node')
    require(inventory['selectedNodes'] == selected, 'selected inventory mismatch')
    require(inventory['noSeparatelyNamedNodes'] == ABSENT_NAMES, 'named-absence scope mismatch')
    require(not any(term in name.lower() for name in names
                    for term in ('optic_nerve', 'rectus', 'oblique', 'artery')),
            'unexpected separately named structure')
    require({'VH_M_optic_disc_R', 'VH_M_ciliary_muscle_R'} <= set(names),
            'expected disc/ciliary names missing')


def check(root=ROOT):
    source = (root / SOURCE_FILE).read_bytes()
    expected = json.loads((root / SOURCE_FILE).with_name('source.json').read_text())
    require(expected['bytes'] == SOURCE_BYTES and expected['sha256'] == SOURCE_SHA256,
            'source manifest no longer identifies the pinned revision')
    require(len(source) == SOURCE_BYTES and hashlib.sha256(source).hexdigest() == SOURCE_SHA256,
            'pinned source bytes missing or changed; an LFS pointer is not payload')
    require(source[:4] == b'glTF' and struct.unpack_from('<II', source, 4) == (2, len(source)),
            'invalid GLB header')
    json_size, chunk_type = struct.unpack_from('<II', source, 12)
    require(chunk_type == 0x4E4F534A and 20 + json_size <= len(source), 'invalid JSON chunk')
    model = json.loads(source[20:20 + json_size])
    validate_inventory(model, json.loads((root / INVENTORY_FILE).read_text()),
                       json.loads((root / RECORD_FILE).read_text()))


def main():
    require(not sys.flags.optimize, 'Do not use Python -O: run the documented verification command')
    check()
    print('PASS pinned inventory: 23 mesh nodes; exact 7 selected / 16 excluded partition. '
          'Provider-description discrepancy remains unresolved; no anatomy approval.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, struct.error) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
