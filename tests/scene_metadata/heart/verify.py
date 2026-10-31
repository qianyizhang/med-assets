#!/usr/bin/env python3
"""Check the exact hydrated source-heart correction; no rendering or network."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from patch_scene_metadata import patch_bytes, require

SOURCE = ROOT / 'body/breathing/heart_breathing.glb'
TARGET = ROOT / 'models/heart/exports/metadata-cleanup-r01/heart.glb'
PATCH = Path(__file__).with_name('approved-patch.json')


def decode(raw):
    require(len(raw) >= 20 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)),
            'Expected hydrated GLB 2')
    chunks, offset = [], 12
    while offset < len(raw):
        size, kind = struct.unpack_from('<II', raw, offset)
        require(size % 4 == 0 and offset+8+size <= len(raw), 'Invalid chunk extent')
        chunks.append((kind, raw[offset+8:offset+8+size]))
        offset += 8+size
    require(offset == len(raw) and [kind for kind, _ in chunks] == [0x4e4f534a, 0x004e4942],
            'Expected the retained JSON and BIN chunks')
    return json.loads(chunks[0][1]), chunks


def clip_arrays(document, binary):
    require(len(document['animations']) == 1, 'Expected one clip')
    clip = document['animations'][0]
    require(clip['name'] == 'Illustrative breathing · 4 seconds'
            and clip['channels'] == [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}}]
            and len(clip['samplers']) == 1, 'Unexpected clip/channel')
    sampler = clip['samplers'][0]
    require(sampler['interpolation'] == 'LINEAR', 'Unexpected interpolation')
    arrays = []
    for key, kind, width in [('input', 'SCALAR', 1), ('output', 'VEC3', 3)]:
        accessor = document['accessors'][sampler[key]]
        view = document['bufferViews'][accessor['bufferView']]
        require(accessor['componentType'] == 5126 and accessor['type'] == kind
                and accessor['count'] == 81 and 'sparse' not in accessor
                and view['buffer'] == 0 and view.get('byteStride', width*4) == width*4,
                'Unexpected clip accessor')
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        arrays.append(struct.unpack_from('<'+'f'*(81*width), binary, start))
    times, translations = arrays
    require(times[0] == 0 and times[-1] == 4 and all(a < b for a, b in zip(times, times[1:])),
            'Unexpected clip times')
    return times, translations


def verify():
    patch = json.loads(PATCH.read_text())
    source, target = SOURCE.read_bytes(), TARGET.read_bytes()
    require(patch_bytes(source, patch) == target, 'Retained output differs from exact replay')
    old, before = decode(source)
    new, after = decode(target)
    require(before[1:] == after[1:], 'Non-JSON chunks changed')
    expected = copy.deepcopy(old)
    extras = expected['scenes'][0]['extras']
    for op in patch['jsonPointerPatch']:
        key = op['path'].removeprefix('/scenes/0/extras/')
        if op['op'] == 'remove':
            del extras[key]
        else:
            extras[key] = op['value']
    require(expected == new, 'JSON differs beyond reviewed fields')
    a, b = copy.deepcopy(old), copy.deepcopy(new)
    del a['scenes'][0]['extras'], b['scenes'][0]['extras']
    require(a == b, 'Render, animation or other JSON changed')
    require(clip_arrays(old, before[1][1]) == clip_arrays(new, after[1][1]),
            'Decoded animation samples changed')
    require(len(new['nodes']) == len(new['meshes']) == len(new['materials']) == 1
            and len(new['meshes'][0]['primitives']) == 1
            and not new['meshes'][0]['primitives'][0].get('targets'), 'Unexpected surface inventory')
    # Retained body consumer contract: roles are node extras, controls/identity are manifest data.
    manifest = json.loads((ROOT / 'body/breathing/animation-manifest.json').read_text())
    heart = next(row for row in manifest['assets'] if row['id'] == 'heart')
    node = new['nodes'][0]
    roles = {key: node['extras'][key] for key in ('anatomy_id', 'view_role', 'derivation')}
    require(heart['nodes'] == [dict(name=node['name'], **roles)] and not heart['cutawaySupport'],
            'Retained body node/cutaway contract differs')
    require(node['extras']['source_case'] == heart['sourceCase'] == 's1233'
            and node['extras']['source_file'] == 'heart.json'
            and node['extras']['source_revision'] == '75ec4e6530abe4d434b07958e90bdc9dec062bef',
            'Source provenance differs')
    require((heart['bytes'], heart['sha256']) == (len(source), hashlib.sha256(source).hexdigest()),
            'Historical manifest no longer binds original')
    rejected = []
    cases = [('changed source', source[:-1]+bytes([source[-1] ^ 1]), patch)]
    for label, key, value in [('wrong old field', 'oldValue', 'different'),
                               ('outside extras', 'path', '/nodes/0/name'),
                               ('unsupported operation', 'op', 'add')]:
        changed = copy.deepcopy(patch)
        changed['jsonPointerPatch'][0][key] = value
        cases.append((label, source, changed))
    changed = copy.deepcopy(patch)
    changed['jsonPointerPatch'][0]['value'] += ' Unreviewed claim.'
    cases.append(('wrong target field', source, changed))
    for label, raw, plan in cases:
        try:
            patch_bytes(raw, plan)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('Accepted '+label)
    return {
        'scope': 'Source-heart metadata correctness; no geometry or approval change',
        'source': {'file': SOURCE.relative_to(ROOT).as_posix(), 'bytes': len(source),
                   'sha256': hashlib.sha256(source).hexdigest()},
        'target': {'file': TARGET.relative_to(ROOT).as_posix(), 'bytes': len(target),
                   'sha256': hashlib.sha256(target).hexdigest()},
        'nonJSONChunksUnchanged': True, 'JSONOutsideAllowedFieldsUnchanged': True,
        'binBytes': len(before[1][1]), 'binSha256': hashlib.sha256(before[1][1]).hexdigest(),
        'clip': {'name': new['animations'][0]['name'], 'channels': 1, 'path': 'translation',
                 'keys': 81, 'timeRangeSeconds': [0, 4], 'decodedArraysExact': True},
        'retainedNodeAndManifestContractUnchanged': True, 'rejectedCases': rejected,
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, ensure_ascii=False))
