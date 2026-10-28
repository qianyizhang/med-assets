#!/usr/bin/env python3
"""Export the hash-pinned, three-structure eye order study; no geometry repair."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

BASELINE_SHA256 = '457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750'
BASELINE_BYTES = 10054784
KEEP = ('VH_M_cornea_R', 'VH_M_iris_R', 'VH_M_lens_R')
OMIT = ('VH_M_ciliary_body_R', 'VH_M_ciliary_muscle_R',
        'VH_M_ciliary_processes_R', 'VH_M_suspensory_ligament_of_lens_R')
SCOPE = ('Draft editorial omission study: broad cornea / iris surrounding pupil opening / lens order only. '
         'Pupil is an opening; opaque blue disk is lens. Missing support tissues are omitted, not absent anatomy. '
         'No attachment, corneal shape/thickness, optics, accommodation, normal-atlas or clinical validity.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(raw):
    require(len(raw) >= 28, 'Truncated GLB')
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    chunks, offset = [], 12
    while offset < len(raw):
        require(offset + 8 <= len(raw), 'Truncated chunk header')
        size, kind = struct.unpack_from('<II', raw, offset)
        require(size % 4 == 0 and offset + 8 + size <= len(raw), 'Invalid chunk size')
        chunks.append((kind, raw[offset + 8:offset + 8 + size]))
        offset += 8 + size
    require([c[0] for c in chunks] == [0x4e4f534a, 0x004e4942], 'Expected JSON and BIN only')
    doc = json.loads(chunks[0][1])
    require(doc['buffers'] == [{'byteLength': len(chunks[1][1])}], 'Expected one embedded buffer')
    return doc, chunks[1][1]


def pack(doc, blob):
    encoded = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    require(len(blob) % 4 == 0, 'Unaligned buffer')
    chunks = (struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
              + struct.pack('<II', len(blob), 0x004e4942) + blob)
    return struct.pack('<4sII', b'glTF', 2, 12 + len(chunks)) + chunks


def accessor(doc, blob, index):
    """Return decoded layout metadata and referenced bytes for this pinned layout."""
    a = copy.deepcopy(doc['accessors'][index])
    view = copy.deepcopy(doc['bufferViews'][a.pop('bufferView')])
    start = view.pop('byteOffset', 0)
    length = view.pop('byteLength')
    require(view.pop('buffer') == 0 and 0 <= start < start + length <= len(blob), 'Bad view range')
    return a, view, blob[start:start + length]


def node_signature(doc, blob, node):
    result = copy.deepcopy(node)
    mesh = copy.deepcopy(doc['meshes'][result.pop('mesh')])
    for primitive in mesh['primitives']:
        primitive['indices'] = accessor(doc, blob, primitive['indices'])
        primitive['attributes'] = {k: accessor(doc, blob, v) for k, v in primitive['attributes'].items()}
        primitive['material'] = doc['materials'][primitive['material']]
    return result, mesh


def validate_pair(before, after):
    old, old_blob = unpack(before)
    new, new_blob = unpack(after)
    require([n['name'] for n in new['nodes']] == list(KEEP), 'Candidate must contain exactly three ordered nodes')
    require(new['scene'] == 0 and new['scenes'] == [{'nodes': [0, 1, 2]}], 'Unexpected candidate scene hierarchy')
    require(len(new['meshes']) == len(new['materials']) == 3, 'Unexpected mesh/material count')
    used_accessors, used_views = set(), set()
    triangles = 0
    for i, node in enumerate(new['nodes']):
        require(node['mesh'] == i, 'Mesh reference mismatch')
        baseline = next(n for n in old['nodes'] if n['name'] == node['name'])
        require(node_signature(old, old_blob, baseline) == node_signature(new, new_blob, node),
                'Retained geometry, normals, material, metadata or transform changed')
        for prim in new['meshes'][i]['primitives']:
            require(prim.get('mode', 4) == 4, 'Expected triangles')
            used_accessors.update([prim['indices'], *prim['attributes'].values()])
            count = new['accessors'][prim['indices']]['count']
            require(count % 3 == 0, 'Incomplete triangle')
            triangles += count // 3
    require(used_accessors == set(range(len(new['accessors']))), 'Unreferenced accessor retained')
    for a in new['accessors']:
        used_views.add(a['bufferView'])
    require(used_views == set(range(len(new['bufferViews']))), 'Unreferenced buffer view retained')
    offset = 0
    for view in new['bufferViews']:
        require(view['byteOffset'] == offset, 'Unexpected gap/overlap in compact buffer')
        offset += view['byteLength']
    require(offset == len(new_blob), 'Unreferenced bytes retained')
    require(new['extras']['scope'] == SCOPE and new['extras']['status'] == 'draft', 'Missing draft scope')
    require(new['extras']['baselineSha256'] == sha(before), 'Wrong baseline provenance')
    require(new['extras']['baselineExtras'] == old.get('extras', {}), 'Lost baseline provenance')
    return {'nodes': 3, 'triangles': triangles, 'accessors': len(used_accessors),
            'retainedDataAndMaterialsExact': True, 'unreferencedPayloadRemoved': True}


def subset(doc, blob):
    """Internal narrow-layout operation; CLI always enforces the exact input hash."""
    require([n['name'] for n in doc['nodes']] == list(KEEP + OMIT), 'Unexpected baseline node inventory')
    require(doc['scene'] == 0 and doc['scenes'] == [{'nodes': list(range(7))}], 'Non-flat baseline hierarchy')
    require(not any(k in doc for k in ('animations', 'skins', 'images', 'textures', 'extensionsRequired')),
            'Unsupported dependencies')
    out = {'asset': copy.deepcopy(doc['asset']), 'scene': 0, 'scenes': [{'nodes': [0, 1, 2]}],
           'nodes': [], 'meshes': [], 'accessors': [], 'bufferViews': [],
           'buffers': [{'byteLength': 0}], 'materials': []}
    out['asset']['generator'] = 'med-assets bounded eye teaching subset r01; exact retained accessor bytes'
    out['extras'] = {'status': 'draft', 'scope': SCOPE, 'baselineSha256': BASELINE_SHA256,
                     'baselineExtras': copy.deepcopy(doc.get('extras', {})), 'omittedNodes': list(OMIT),
                     'decision': 'issue100 / PR113: accepted broad order; rejected attachment geometry',
                     'sourceLabelsAreNotIndependentAnatomy': True}
    payload = bytearray()
    accessors, views = {}, {}

    def copy_accessor(index):
        if index in accessors:
            return accessors[index]
        a = copy.deepcopy(doc['accessors'][index])
        require('sparse' not in a, 'Sparse accessor unsupported')
        vi = a['bufferView']
        if vi not in views:
            view = copy.deepcopy(doc['bufferViews'][vi])
            require(view['buffer'] == 0 and view['byteLength'] % 4 == 0, 'Unexpected buffer layout')
            start = view.get('byteOffset', 0)
            data = blob[start:start + view['byteLength']]
            require(len(data) == view['byteLength'], 'Truncated accessor data')
            view['byteOffset'] = len(payload)
            views[vi] = len(out['bufferViews'])
            out['bufferViews'].append(view)
            payload.extend(data)
        a['bufferView'] = views[vi]
        accessors[index] = len(out['accessors'])
        out['accessors'].append(a)
        return accessors[index]

    for node in doc['nodes'][:3]:
        node = copy.deepcopy(node)
        require('children' not in node and 'skin' not in node, 'Unexpected node dependency')
        mesh = copy.deepcopy(doc['meshes'][node['mesh']])
        node['mesh'] = len(out['meshes'])
        for prim in mesh['primitives']:
            require(set(prim) <= {'attributes', 'indices', 'material', 'mode'}, 'Unsupported primitive dependency')
            prim['indices'] = copy_accessor(prim['indices'])
            prim['attributes'] = {k: copy_accessor(v) for k, v in prim['attributes'].items()}
            material = copy.deepcopy(doc['materials'][prim['material']])
            prim['material'] = len(out['materials'])
            out['materials'].append(material)
        out['nodes'].append(node)
        out['meshes'].append(mesh)
    out['buffers'][0]['byteLength'] = len(payload)
    return out, bytes(payload)


def build(raw):
    require(len(raw) == BASELINE_BYTES and sha(raw) == BASELINE_SHA256, 'Exact diagnostic baseline size/SHA-256 required')
    doc, blob = unpack(raw)
    out, payload = subset(doc, blob)
    result = pack(out, payload)
    validation = validate_pair(raw, result)
    baseline_triangles = sum(doc['accessors'][p['indices']]['count'] // 3
                             for m in doc['meshes'] for p in m['primitives'])
    return result, {'baseline': {'sha256': sha(raw), 'bytes': len(raw), 'nodes': 7, 'triangles': baseline_triangles},
                    'candidate': {'file': 'eye-order-study.glb', 'sha256': sha(result), 'bytes': len(result), **validation},
                    'omittedNodes': list(OMIT), 'scope': SCOPE, 'sourceUnchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='NEW output directory')
    args = parser.parse_args()
    raw = args.source.read_bytes()
    result, receipt = build(raw)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'eye-order-study.glb').write_bytes(result)
    require(args.source.read_bytes() == raw, 'Source changed during build')
    (args.output / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
