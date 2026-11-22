"""Compare exact deliveries and replay one disposable edit in both pelvic locators."""

import argparse
import json
from pathlib import Path
import struct

from build import ROOT, VAGINA_FILE, build, read_inputs
from tools.glb import decode, encode
from tools.glb_selection import identity

PATCH = 'VH_F_fundus_of_urinary_bladder_dome'
RETAINED = {
    'bladder-pelvic-base.glb': ROOT / 'models/bladder/exports/pelvic-base-r01/bladder-pelvic-base.glb',
    VAGINA_FILE: ROOT / 'models/vagina_hra/exports/teaching-context-r03' / VAGINA_FILE,
}


def position_accessor(document):
    node = next(n for n in document['nodes'] if n.get('name') == PATCH)
    mesh = document['meshes'][node['mesh']]
    (primitive,) = mesh['primitives']
    index = primitive['attributes']['POSITION']
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    return accessor, view['byteOffset'] + accessor.get('byteOffset', 0)


def revised(master, spec, *, malformed=False):
    doc, binary = decode(master)
    accessor, offset = position_accessor(doc)
    binary = bytearray(binary)
    if malformed:
        accessor['count'] -= 1
    else:
        x, = struct.unpack_from('<f', binary, offset)
        struct.pack_into('<f', binary, offset, x + 0.0001)
    changed = encode(doc, binary)
    return changed, {**spec, 'sha256': identity(changed)['sha256']}


def position(raw):
    doc, binary = decode(raw)
    _, offset = position_accessor(doc)
    return struct.unpack_from('<3f', binary, offset)


def mesh_names(raw):
    doc, _ = decode(raw)
    return sorted(node['name'] for node in doc['nodes'] if 'mesh' in node)


def check():
    master, style, spec = read_inputs()
    normal = build(master, style, spec)
    changed_master, changed_spec = revised(master, spec)
    changed = build(changed_master, style, changed_spec)
    report = {}
    for file, expected in RETAINED.items():
        original = normal[file]
        updated = changed[file]
        if original != expected.read_bytes():
            raise ValueError(f'Replay differs from its reviewed delivery: {file}')
        if position(original) != position(master) or position(updated) != position(changed_master):
            raise ValueError(f'Shared atlas edit did not propagate to {file}')
        if mesh_names(original) != mesh_names(updated):
            raise ValueError(f'The edit changed the unrelated selection in {file}')
        report[file] = {'exactReplay': identity(original), 'meshes': mesh_names(original),
                        'sharedVertexBefore': position(original), 'sharedVertexAfter': position(updated)}

    malformed, malformed_spec = revised(master, spec, malformed=True)
    try:
        build(malformed, style, malformed_spec)
    except ValueError as error:
        if 'reviewed style layout' not in str(error):
            raise
    else:
        raise ValueError('Mismatched geometry and style layouts unexpectedly rebuilt')
    return {'canonical': identity(master), 'style': identity(style), 'sharedMesh': PATCH,
            'selections': report, 'rejectedIncompatibleLayout': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path, help='Fresh JSON output path')
    args = parser.parse_args()
    result = check()
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('PASS exact pelvic replays, shared vertex edit, independent selections and malformed-layout rejection.')
