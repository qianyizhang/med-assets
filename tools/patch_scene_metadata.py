#!/usr/bin/env python3
"""Apply a hash-pinned scene-extra patch without changing other GLB content."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct


def require(condition, message):
    if not condition:
        raise ValueError(message)


def patch_bytes(raw, patch):
    require(len(raw) == patch['sourceBytes']
            and hashlib.sha256(raw).hexdigest() == patch['sourceSha256'],
            'Source size/SHA-256 mismatch')
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    chunks = []
    offset = 12
    while offset < len(raw):
        size, kind = struct.unpack_from('<II', raw, offset)
        require(size % 4 == 0 and offset + 8 + size <= len(raw), 'Invalid GLB chunk')
        chunks.append((kind, raw[offset + 8:offset + 8 + size]))
        offset += 8 + size
    require(offset == len(raw) and chunks and chunks[0][0] == 0x4e4f534a,
            'Expected complete GLB with first JSON chunk')
    old = json.loads(chunks[0][1])
    new = copy.deepcopy(old)
    require(len(patch['jsonPointerPatch']) in (6, 7), 'Expected six or seven reviewed operations')
    for operation in patch['jsonPointerPatch']:
        path = operation['path'].split('/')
        require(path[:4] == ['', 'scenes', '0', 'extras'] and len(path) == 5,
                'Patch must stay within scene-zero extras')
        key = path[4]
        require(new['scenes'][0]['extras'][key] == operation['oldValue'], 'Old value mismatch')
        if operation['op'] == 'replace':
            new['scenes'][0]['extras'][key] = operation['value']
        elif operation['op'] == 'remove':
            del new['scenes'][0]['extras'][key]
        else:
            raise ValueError('Only replace/remove allowed')
    a, b = copy.deepcopy(old), copy.deepcopy(new)
    a['scenes'][0].pop('extras')
    b['scenes'][0].pop('extras')
    require(a == b, 'JSON outside scene extras changed')
    encoded = json.dumps(new, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    payload = b''.join(struct.pack('<II', len(data), kind) + data
                       for kind, data in [(chunks[0][0], encoded)] + chunks[1:])
    result = struct.pack('<4sII', b'glTF', 2, len(payload) + 12) + payload
    require(len(result) == patch['targetBytes']
            and hashlib.sha256(result).hexdigest() == patch['targetSha256'],
            'Target size/SHA-256 mismatch')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', type=Path, required=True)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    patch = json.loads(args.patch.read_text())
    result = patch_bytes(args.source.read_bytes(), patch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(result)
    print(json.dumps({'sha256': patch['targetSha256'], 'bytes': len(result),
                      'BINUnchanged': True, 'JSONOutsideSceneExtrasUnchanged': True,
                      'scope': 'Metadata only; no anatomy/runtime promotion'}))


if __name__ == '__main__':
    main()
