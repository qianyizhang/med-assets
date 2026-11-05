#!/usr/bin/env python3
"""Verify retained source-package identities; no fetch, rebuild or quality approval."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PACKAGES = ('muscle', 'breasts_hra')
ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(root, package):
    require(package in PACKAGES, 'Unknown source package: ' + package)
    review = root / 'reviews' / package / '2026-10-24-bounded-migration'
    checks = json.loads((review / 'FILE-HASHES.json').read_text())
    for name, expected in checks.items():
        path = root / name
        require(path.is_file(), 'Missing package file: ' + name)
        raw = path.read_bytes()
        require(len(raw) == expected['bytes'] and digest(raw) == expected['sha256'],
                'Package file identity mismatch: ' + name)

    manifest = json.loads((review / 'transport-manifest.json').read_text())
    record = json.loads((root / manifest['reviewRecord']).read_text())
    source = json.loads((root / manifest['sourceMap']).read_text())
    model = (root / manifest['canonicalPath']).read_bytes()
    transport = manifest['transport']
    require(len(model) == transport['decodedBytes'] and
            digest(model) == transport['decodedSha256'], 'Model identity mismatch')
    json_size, = struct.unpack('<I', model[12:16])
    document = json.loads(model[20:20 + json_size])
    require(record['evidence'] == manifest['evidence'], 'Review evidence mismatch')
    require(record['sourceDependencies'] == manifest['sourceMap'], 'Source dependency mismatch')
    for node in record['nodeIdentityMap']:
        actual = document['nodes'][node['index']]
        require(actual['name'] == node['name'], 'Node name mismatch')
        if node['sourceObjectName'] is not None:
            require(actual.get('extras', {}).get('source_object_name') == node['sourceObjectName'],
                    'Node source identity mismatch')
    selected = {item['sourceObjectName'] for item in source['selection']}
    field = 'sourceObjectName' if 'sourceCollection' in source else 'name'
    require({node[field] for node in record['nodeIdentityMap']} == selected,
            'Source selection mismatch')

    seen = {digest(model): len(model)}
    for evidence in manifest['evidence']:
        raw = (root / evidence['path']).read_bytes()
        require(digest(raw) == evidence['sha256'] and len(raw) == evidence['bytes'],
                'Evidence identity mismatch: ' + evidence['path'])
        require(raw[:4] == b'RIFF' and raw[8:12] == b'WEBP', 'Expected WebP evidence')
        require(evidence['originalPNG']['bundled'] is False and
                evidence['originalPNG']['sha256'] != evidence['sha256'],
                'Original PNG and display evidence must stay distinct')
        seen[evidence['sha256']] = evidence['bytes']
        if evidence['selectionRole'] == 'candidate':
            require(evidence['assetBinding'] == transport['decodedSha256'],
                    'Candidate evidence binding mismatch')
    for reference in (source['externalHistoricalRecords'] + source['recipeDependencies'] +
                      source['licenseReceipts']):
        require(reference['bundled'] is False and len(reference['sha256']) == 64,
                'External source/license reference mismatch')
    require(sum(seen.values()) == manifest['uniqueMediaBytes'] and
            len(seen) == manifest['uniqueMediaOids'], 'Media accounting mismatch')
    return {'identityChecks': 'passed', 'scope': 'Local retained bytes only; no source rebuild or runtime approval',
            'mediaBytes': sum(seen.values()), 'status': manifest['status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', choices=PACKAGES)
    args = parser.parse_args()
    print(json.dumps(verify(ROOT, args.package)))


if __name__ == '__main__':
    main()
