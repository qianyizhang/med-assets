"""Run exact-vendor CPU camera checks without downloads, rendering or a browser."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def run(vendor, baseline=False):
    original = ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js'
    current = ROOT / 'tests/viewer/candidate.js'
    source_binding = json.loads((current.parent / 'source.json').read_text())
    expected_source = ('9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b'
                       if baseline else source_binding['files']['candidate.js']['sha256'])
    source_raw = (original if baseline else current).read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != expected_source:
        raise ValueError('Wrong exact candidate source')
    binding = json.loads((Path(__file__).parent / 'vendor-binding.json').read_text())
    fixture = json.loads((ROOT / binding['existingThreeFixture']).read_text())
    expected = {Path(row['path']).name: row for row in fixture['resources']
                if row['path'] in binding['threeResources']}
    expected['OrbitControls.js'] = binding['orbitControls']
    for name, row in expected.items():
        raw = (vendor / name).read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Wrong exact current vendor: ' + name)
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        staged = target / 'vendor'
        staged.mkdir()
        for name in expected:
            shutil.copyfile(vendor / name, staged / name)
        # Explicit CPU-only bare-specifier binding, not evidence of browser import-map resolution.
        (staged / 'package.json').write_text(json.dumps({
            'name': 'three', 'type': 'module', 'exports': './three.module.js'}))
        source = target / 'candidate.js'
        source.write_bytes(source_raw)
        env = os.environ.copy()
        env['CAMERA_VENDOR_STAGE'] = str(staged)
        env['CAMERA_SOURCE'] = str(source)
        return subprocess.run(['node', '--test', str(Path(__file__).with_name('cpu.test.mjs'))],
                              env=env, check=False).returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-dir', required=True, type=Path)
    parser.add_argument('--baseline', action='store_true', help='Expected failing-before run')
    args = parser.parse_args()
    raise SystemExit(run(args.vendor_dir, args.baseline))
