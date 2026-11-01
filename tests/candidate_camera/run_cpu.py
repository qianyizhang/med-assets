"""Run exact-vendor CPU camera checks without downloads, rendering or a browser."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(vendor, baseline=False, lifecycle=False):
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
        source.write_bytes((ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js').read_bytes())
        if lifecycle:
            load(ROOT / 'gallery/candidate-lifecycle/r01/apply.py', 'lifecycle').apply(target)
        if not baseline:
            load(ROOT / 'gallery/candidate-camera/r01/apply.py', 'camera').apply(target)
        env = os.environ.copy()
        env['CAMERA_VENDOR_STAGE'] = str(staged)
        env['CAMERA_SOURCE'] = str(source)
        return subprocess.run(['node', '--test', str(Path(__file__).with_name('cpu.test.mjs'))],
                              env=env, check=False).returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-dir', required=True, type=Path)
    parser.add_argument('--baseline', action='store_true', help='Expected failing-before run')
    parser.add_argument('--lifecycle', action='store_true', help='Compose after exact lifecycle-v2 patch')
    args = parser.parse_args()
    raise SystemExit(run(args.vendor_dir, args.baseline, args.lifecycle))
