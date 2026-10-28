#!/usr/bin/env python3
"""Local, CPU-only exact-GLB/Three raycast regression. No network or browser launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ci'))
from esophagus import probe


def run(vendor_root, source):
    if not shutil.which('node'):
        raise RuntimeError('Preinstalled Node is required; no installation attempted')
    fixture = json.loads((ROOT / 'ci/glb-runtime-fixture.json').read_text())
    libraries = [item for item in fixture['resources'] if item['path'].startswith('vendor/')]
    if len(libraries) != 5:
        raise ValueError('Expected the five reviewed Three resources, including LICENSE')
    # Validate every dependency before importing JavaScript. Do not use an npm
    # version range or substitute another Three build with the same revision.
    verified = []
    for item in libraries:
        relative = Path(item['path']).relative_to('vendor')
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Library path outside vendor root')
        path = vendor_root / relative
        if not path.is_file() or path.stat().st_size != item['bytes']:
            raise ValueError('Pinned library size mismatch: ' + str(relative))
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Pinned library SHA-256 mismatch: ' + str(relative))
        verified.append((relative, data))
    probe.exact(source, probe.FIXTURE['baseline'])
    with tempfile.TemporaryDirectory(prefix='esophagus-anchor-regression-') as temporary:
        work = Path(temporary)
        for relative, data in verified:
            path = work / 'vendor' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        # Package resolution metadata only; reviewed upstream bytes stay intact.
        (work / 'vendor/package.json').write_text(json.dumps({
            'name': 'three', 'type': 'module', 'exports': './build/three.module.js'}))
        (work / 'node_modules').mkdir()
        (work / 'node_modules/three').symlink_to('../vendor', target_is_directory=True)
        output = work / 'replay'
        receipt = probe.prepare(source, output)
        env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
        env.update(ESOPHAGUS_VENDOR_ROOT=str(work / 'vendor'),
                   ESOPHAGUS_BASELINE=str(output / 'baseline/esophagus-wall-cutaway-r01.glb'),
                   ESOPHAGUS_CANDIDATE=str(output / 'candidate/esophagus-wall-palette-r01.glb'))
        subprocess.run(['node', '--test', str(ROOT / 'tests/runtime_receipts/test_esophagus_anchors.mjs')],
                       env=env, check=True, timeout=30)
        print(json.dumps({**receipt, 'threeCommit': fixture['threeCommit'],
                          'loadedRaycastRegression': 'passed', 'browserExecuted': False,
                          'displayVerified': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-root', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    run(args.vendor_root.resolve(), args.input.resolve())
