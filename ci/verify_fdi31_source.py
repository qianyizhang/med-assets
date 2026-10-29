#!/usr/bin/env python3
"""Download-only check for the exact retained FDI31 package; no LFS operations."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from lfs_transport import Stop, download_source, validate_manifest

MANIFEST_SHA256 = 'ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118'
MANIFEST = ROOT / 'ci/fdi31-source/manifest.json'


def verify(raw):
    manifest = validate_manifest(raw, MANIFEST_SHA256)
    rows = []
    for obj in manifest['objects']:
        data = download_source(obj)
        rows.append({'file': obj['file'], 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    return {'sourceOnly': True, 'lfsHydrated': False,
            'manifestSha256': MANIFEST_SHA256, 'objects': rows,
            'totalBytes': manifest['totalBytes']}


def main():
    try:
        receipt = verify(MANIFEST.read_bytes())
    except Stop as error:
        raise SystemExit('STOP: ' + str(error)) from None
    receipt['commit'] = os.environ.get('GITHUB_SHA')
    receipt['runId'] = os.environ.get('GITHUB_RUN_ID')
    encoded = json.dumps(receipt, sort_keys=True, indent=2)
    print(encoded)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as out:
            out.write('## FDI31 source download: passed\n\n'
                      '5 staged objects verified; no LFS upload/hydration or clinical acceptance.\n\n'
                      '```json\n' + encoded + '\n```\n')


if __name__ == '__main__':
    main()
