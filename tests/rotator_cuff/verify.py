"""Small package checks; run with actual payloads after building/staging."""
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
MODEL = Path('models/joints/exports/z-rotator-cuff-r01')
REVIEW = Path('reviews/joints/2026-10-30-rotator-cuff-r01')
NAMES = {'Humerus.r', 'Scapula.r', 'Supraspinatus muscle.r', 'Infraspinatus muscle.r',
         'Teres minor muscle.r', 'Subscapularis muscle.r'}
EXPECTED = {'posterior.png': {'1': 'Supraspinatus muscle.r', '2': 'Infraspinatus muscle.r',
                             '3': 'Teres minor muscle.r', 'S': 'Scapula.r'},
            'anterior.png': {'4': 'Subscapularis muscle.r'}, 'lateral.png': {},
            'overview.png': {'S': 'Scapula.r', 'H': 'Humerus.r'}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_records(root=ROOT):
    return (json.loads((root/MODEL/'inventory.json').read_text()),
            json.loads((root/REVIEW/'checks.json').read_text()))


def validate(inventory, checks):
    require(inventory['sourceSha256'] == '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd', 'Wrong native source')
    require(inventory['sourceCommit'] == 'c08bde5325e35a46404d86a6bd458c484297cc2d', 'Wrong source revision')
    require(checks['artifactSha256'] == inventory['artifact']['sha256'], 'Mismatched artifact')
    rows = inventory['objects']
    require(len(rows) == 6 and {r['name'] for r in rows} == NAMES, 'Wrong source object set')
    require(len(checks['objects']) == 6 and {r['name'] for r in checks['objects']} == NAMES, 'Incomplete geometry checks')
    require(checks['toleranceNativeUnits'] == 5e-7, 'Unexpected tolerance')
    for checked in checks['objects']:
        source = next(r for r in rows if r['name'] == checked['name'])
        error = checked['maxWorldError']
        require(math.isfinite(error) and 0 <= error <= 5e-7, 'Coordinate preservation failed')
        require(checked['triangleMultisetMatches'] is True and checked['triangles'] == source['triangles'], 'Triangle preservation failed')
    for group in ['sourceViews', 'exportViews']:
        views = checks[group]
        require(len(views) == 4 and {v['file'] for v in views} == set(EXPECTED), 'Missing or duplicate capture')
        for view in views:
            anchors = view['anchors']
            require(len(anchors) == len(EXPECTED[view['file']]), 'Missing or duplicate anchor')
            require({a['id']: a['object'] for a in anchors} == EXPECTED[view['file']], 'Wrong label target')
            for anchor in anchors:
                require(anchor['face'] >= 0 and len(anchor['world']) == 3, 'Missing surface binding')
                require(len(anchor['pixel']) == 2 and all(0 < x < 900 for x in anchor['pixel']), 'Off-image label')
    for source, exported in zip(checks['sourceViews'], checks['exportViews']):
        require(source['file'] == exported['file'], 'Pair order changed')
        for a, b in zip(source['anchors'], exported['anchors']):
            require(a['object'] == b['object'] and a['id'] == b['id'], 'Pair label mismatch')
            require(max(abs(x-y) for x, y in zip(a['world'], b['world'])) <= 5e-7, 'Pair surface point moved')


def require_hash(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Payload hash mismatch: '+path.name)
    return raw


def validate_composition(composition, artifact_sha):
    require(composition['artifactSha256'] == artifact_sha, 'Presentation has wrong artifact')
    required = {(view[:-4], key) for view, anchors in EXPECTED.items() for key in anchors}
    labels = composition.get('labelBindings', [])
    observed = {(a['view'], a['anchorId']) for a in labels}
    require(len(labels) == len(required) and observed == required,
            'Missing or duplicate presentation label')


def payloads(root=ROOT):
    inventory, checks = read_records(root)
    validate(inventory, checks)
    artifact = inventory['artifact']
    raw = require_hash(root/MODEL/artifact['file'], artifact['sha256'])
    require(len(raw) == artifact['bytes'], 'Wrong GLB size')
    magic, version, size = struct.unpack_from('<4sII', raw)
    require(magic == b'glTF' and version == 2 and size == len(raw), 'Invalid GLB')
    count, kind = struct.unpack_from('<I4s', raw, 12)
    require(kind == b'JSON', 'Missing GLB JSON')
    doc = json.loads(raw[20:20+count])
    require({n['name'] for n in doc['nodes']} == NAMES and len(doc['nodes']) == 6, 'Unexpected GLB nodes')
    require(len(doc['meshes']) == 6 and not doc.get('animations'), 'Wrong mesh or animation set')
    for node in doc['nodes']:
        require(node['extras']['source_object'] == node['name'], 'Unbound source node')
        require(node['extras']['source_sha256'] == inventory['sourceSha256'], 'Wrong node source')
    require_hash(root/inventory['license']['file'], inventory['license']['sha256'])
    for group, folder in [('sourceViews', 'source'), ('exportViews', 'export')]:
        for view in checks[group]:
            png = require_hash(root/REVIEW/folder/view['file'], view['sha256'])
            require(png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', png, 16) == (900, 900), 'Wrong raw image dimensions')
    composition = json.loads((root/REVIEW/'v2/composition.json').read_text())
    validate_composition(composition, artifact['sha256'])
    for name, digest in composition['outputs'].items():
        require_hash(root/REVIEW/'v2'/name, digest)
    require_hash(root/REVIEW/'v1/teaching.png', composition['previousTeachingSha256'])
    for label in composition['labelBindings']:
        view = next(v for v in checks['exportViews'] if v['file'] == label['view']+'.png')
        require(label['anchorId'] in {a['id'] for a in view['anchors']}, 'Presentation label lacks visible source binding')
    return artifact['sha256']


if __name__ == '__main__':
    print('PASS: six-surface payload, native identities, eight captures and seven visible labels:', payloads())
