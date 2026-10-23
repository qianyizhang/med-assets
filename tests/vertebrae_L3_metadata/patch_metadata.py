#!/usr/bin/env python3
"""Exact approved scene-extra patch only; refuse unexpected input or output bytes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
options = parser.parse_args()
patch = json.loads(Path(__file__).with_name('approved-patch.json').read_text())
raw = options.source.read_bytes()
assert len(raw) == patch['sourceBytes'] and hashlib.sha256(raw).hexdigest() == patch['sourceSha256']
assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
chunks = []
offset = 12
while offset < len(raw):
    size, kind = struct.unpack_from('<II', raw, offset)
    assert size % 4 == 0 and offset + 8 + size <= len(raw)
    chunks.append((kind, raw[offset + 8:offset + 8 + size]))
    offset += 8 + size
assert offset == len(raw) and chunks[0][0] == 0x4e4f534a
old = json.loads(chunks[0][1])
new = copy.deepcopy(old)
assert len(patch['jsonPointerPatch']) == 7
for operation in patch['jsonPointerPatch']:
    path = operation['path'].split('/')
    assert path[:4] == ['', 'scenes', '0', 'extras'] and len(path) == 5
    key = path[4]
    assert new['scenes'][0]['extras'][key] == operation['oldValue']
    if operation['op'] == 'replace':
        new['scenes'][0]['extras'][key] = operation['value']
    elif operation['op'] == 'remove':
        del new['scenes'][0]['extras'][key]
    else:
        raise ValueError('Only replace/remove allowed')
a, b = copy.deepcopy(old), copy.deepcopy(new)
a['scenes'][0].pop('extras')
b['scenes'][0].pop('extras')
assert a == b
encoded = json.dumps(new, ensure_ascii=False, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
new_chunks = [(chunks[0][0], encoded)] + chunks[1:]
assert new_chunks[1:] == chunks[1:]
payload = b''.join(struct.pack('<II', len(data), kind) + data for kind, data in new_chunks)
result = struct.pack('<4sII', b'glTF', 2, len(payload) + 12) + payload
assert len(result) == patch['targetBytes'] and hashlib.sha256(result).hexdigest() == patch['targetSha256']
options.output.parent.mkdir(parents=True, exist_ok=True)
with options.output.open('xb') as stream:
    stream.write(result)
print(json.dumps({'sha256': patch['targetSha256'], 'bytes': len(result), 'BINUnchanged': True, 'JSONOutsideSceneExtrasUnchanged': True, 'scope': 'Metadata only; no anatomy/runtime promotion'}))
