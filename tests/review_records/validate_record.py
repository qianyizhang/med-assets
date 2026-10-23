#!/usr/bin/env python3
"""Validate local record shape and hashes; never certify visual/anatomy/runtime claims."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

STATUSES = {'unreviewed', 'unverified', 'passed', 'pass-with-limitations',
            'reference-screened', 'failed', 'needs-review', 'needs-revision',
            'not-applicable'}


def payload(root, entry):
    name = entry.get('file', '')
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Expected repository-relative POSIX file path')
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Path must stay within repository')
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Resolved path escapes repository')
    digest = entry.get('sha256', '')
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Expected lowercase SHA-256')
    data = path.read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        raise ValueError('Unresolved LFS pointer; fetch actual payload first')
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Payload SHA-256 mismatch: ' + name)
    return digest


def validate(record, root):
    root = Path(root).resolve()
    if record.get('schemaVersion') != 1:
        raise ValueError('Unsupported schemaVersion')
    for key in ('id', 'assetId', 'variantId', 'reviewedAt'):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError('Missing text field: ' + key)
    if datetime.fromisoformat(record['reviewedAt'].replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('reviewedAt requires timezone')
    digest = payload(root, record['artifact'])
    for name in ('technical', 'visual', 'anatomy', 'runtime'):
        gate = record['gates'][name]
        if gate.get('status') not in STATUSES or not isinstance(gate.get('scope'), str) or not gate['scope'].strip():
            raise ValueError('Invalid independent gate: ' + name)
    evidence = record.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('At least one bound evidence item required')
    for item in evidence:
        payload(root, item)
        if item.get('artifactSha256') != digest or not isinstance(item.get('kind'), str) or not item['kind'].strip():
            raise ValueError('Evidence kind/binding mismatch')
    for key in ('failure', 'cause', 'fix', 'retest', 'lesson'):
        if not isinstance(record.get('failureSummary', {}).get(key), str) or not record['failureSummary'][key].strip():
            raise ValueError('Missing failure-summary field: ' + key)
    limits = record.get('limitations')
    if not isinstance(limits, list) or not limits or not all(isinstance(x, str) and x.strip() for x in limits):
        raise ValueError('Explicit limitations required')
    return {'result': 'passed', 'scope': 'Local contract/hash checks only; not visual, anatomy, remote LFS or runtime certification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('record')
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(Path(args.record).read_text()), args.root), indent=2))
