#!/usr/bin/env python3
"""Verify retained source-package identities; no fetch, rebuild or quality approval."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from glb import decode

PACKAGES = ('muscle', 'breasts_hra')
ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local_bytes(root, name):
    relative = PurePosixPath(name)
    path = root / relative
    require(not relative.is_absolute() and '..' not in relative.parts and
            not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            'Package path escapes checkout or is a symlink: ' + name)
    require(path.is_file(), 'Missing package file: ' + name)
    return path.read_bytes()


class PackageFiles:
    """One invocation's expected identities. Reads always recheck captured bytes.

    No verified-path cache: changing a file between reads cannot inherit a pass.
    Each caller owns this instance and its manifest; no mutable module state.
    """
    def __init__(self, root, manifest):
        self.root = root
        self.checks = json.loads(local_bytes(root, manifest))
        require(manifest not in self.checks, 'Package manifest must not hash itself')
        for name in self.checks:
            self.read(name)

    def read(self, name, expected=None):
        require(name in self.checks, 'Undeclared package dependency: ' + name)
        raw = local_bytes(self.root, name)
        actual = {'bytes': len(raw), 'sha256': digest(raw)}
        for identity in (self.checks[name], expected):
            if identity is not None:
                require(all(actual[key] == identity[key] for key in actual),
                        'Package file identity mismatch: ' + name)
        return raw

    def json(self, name):
        return json.loads(self.read(name))


def verify_studies(root, review, check_study=None):
    """Common retained-media checks; source/evidence meaning stays with callers."""
    files = PackageFiles(root, review + '/FILE-HASHES.json')
    manifest = files.json(review + '/transport-manifest.json')
    seen, images = {}, set()
    for study in manifest['studies']:
        transport = study['transport']
        raw = files.read(study['canonicalPath'], {
            'sha256': transport['decodedSha256'], 'bytes': transport['decodedBytes']})
        document, _ = decode(raw)
        seen[transport['decodedSha256']] = len(raw)
        if check_study:
            check_study(files, study, document)
        for evidence in study['evidence']:
            raw = files.read(evidence['path'], evidence)
            kind = evidence.get('format', Path(evidence['path']).suffix[1:].upper())
            require((kind == 'WEBP' and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP') or
                    (kind == 'PNG' and raw[:8] == b'\x89PNG\r\n\x1a\n'), 'Unsupported or invalid evidence format')
            seen[evidence['sha256']] = len(raw)
            images.add(evidence['sha256'])
    require(len(seen) == manifest['uniqueMediaOids'] and
            sum(seen.values()) == manifest['uniqueMediaBytes'], 'Media accounting mismatch')
    if 'uniqueSelectedEvidence' in manifest:
        require(len(images) == manifest['uniqueSelectedEvidence'], 'Evidence accounting mismatch')
    return {'identityChecks': 'passed', 'files': len(files.checks),
            'uniqueMediaOids': len(seen), 'uniqueMediaBytes': sum(seen.values()),
            **({'status': manifest['status']} if 'status' in manifest else {}),
            'scope': 'Local retained bytes only; no rebuild, remote, anatomy or runtime approval'}


def verify(root, package):
    require(package in PACKAGES, 'Unknown source package: ' + package)
    review = root / 'reviews' / package / '2026-10-24-bounded-migration'
    files = PackageFiles(root, str(review.relative_to(root)) + '/FILE-HASHES.json')
    manifest = files.json(str(review.relative_to(root)) + '/transport-manifest.json')
    record = files.json(manifest['reviewRecord'])
    source = files.json(manifest['sourceMap'])
    transport = manifest['transport']
    model = files.read(manifest['canonicalPath'], {
        'sha256': transport['decodedSha256'], 'bytes': transport['decodedBytes']})
    document, _ = decode(model)
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

    seen = {transport['decodedSha256']: len(model)}
    for evidence in manifest['evidence']:
        raw = files.read(evidence['path'], evidence)
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
