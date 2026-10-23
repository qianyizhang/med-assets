#!/usr/bin/env python3
"""Read-only durable receipt/hash checks. Does not run or certify a browser."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('bundle', type=Path)
a = p.parse_args()
root = a.bundle.resolve()
manifest = json.loads((root / 'MANIFEST.json').read_text())
assert len(manifest['files']) == manifest['fileCount']
seen = set()
total = 0
for entry in manifest['files']:
    path = (root / entry['file']).resolve()
    assert path.is_relative_to(root) and entry['file'] not in seen
    seen.add(entry['file'])
    data = path.read_bytes()
    assert len(data) == entry['bytes']
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
    if path.suffix == '.png':
        assert data.startswith(b'\x89PNG\r\n\x1a\n')
    total += len(data)
assert total == manifest['totalBytes']
record = json.loads((root / 'record.json').read_text())
expected = {
    '7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd': 7413900,
    '17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a': 8180452,
}
assert {x['sha256']: x['bytes'] for x in record['assets']} == expected
for key in ['nativeUIInteractionQA', 'wholeSiteQA', 'hardwarePerformanceQA', 'anatomyApproval']:
    assert record['scope'][key] is False
print(json.dumps({'result': 'passed', 'files': len(seen), 'bytes': total,
                  'scope': 'Durable receipt/file integrity only. No new browser run, clinical approval or general runtime certification.'}))
