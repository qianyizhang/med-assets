"""Stage exact model selections and the lesson's pinned Three.js modules."""

import argparse
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'lib'))

from airway_companion import build_companion
from med_assets.glb_selection import identity


def checked(raw, byte_count, sha256, message):
    if identity(raw) != {'bytes': byte_count, 'sha256': sha256}:
        raise ValueError(message)
    return raw


def model_bytes(item, asset_root):
    raw = (asset_root / item['source']).read_bytes()
    message = 'Wrong or unresolved local asset: ' + item['id']
    if 'sourceSha256' in item:
        checked(raw, item['sourceBytes'], item['sourceSha256'], message)
        raw = build_companion(raw, item)
    return checked(raw, item['bytes'], item['sha256'], message)


def stage(asset_root, out, vendor_dir=None):
    if out.exists():
        raise FileExistsError('Use a new local staging directory')
    manifest = json.loads((ROOT / 'assets.json').read_text())
    sources = [(item, model_bytes(item, asset_root)) for item in manifest['assets']]
    fixture = json.loads((REPO / 'tests/runtime/glb-runtime-fixture.json').read_text())
    vendors = []
    for item in fixture['resources']:
        path = item['path']
        if not path.startswith('vendor/'):
            continue
        if vendor_dir is None:
            with urllib.request.urlopen(item['url'], timeout=45) as response:
                raw = response.read()
        else:
            raw = (vendor_dir / path.removeprefix('vendor/')).read_bytes()
        vendors.append((path, checked(raw, item['bytes'], item['sha256'], 'Dependency identity mismatch')))

    # A failed model or dependency check leaves the destination available for retry.
    out.mkdir(parents=True)
    for item, raw in sources:
        (out / item['file']).write_bytes(raw)
    for path, raw in vendors:
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (out / 'vendor/package.json').write_text('{"name":"three","type":"module","exports":"./build/three.module.js"}\n')
    receipt = {'assets': manifest['assets'], 'threeVersion': fixture['threeVersion'],
               'source': 'Exact hydrated inputs and selections with fixture-pinned dependencies'}
    (out / 'staging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path, default=REPO, help='Hydrated repository checkout')
    parser.add_argument('--out', type=Path, default=ROOT / '.local', help='Fresh staging directory')
    parser.add_argument('--vendor-dir', type=Path, help='Reuse an earlier staged vendor directory after checking its hashes')
    args = parser.parse_args()
    stage(args.asset_root, args.out, args.vendor_dir)
    print('Prepared local models and pinned Three.js')


if __name__ == '__main__':
    main()
