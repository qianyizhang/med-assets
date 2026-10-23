#!/usr/bin/env python3
"""Explicit external-source reconstruction; never fetch remotely or edit source bytes."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, type=Path, help='Existing official united-female v1.10 atlas; 374,505,632 bytes')
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--render', action='store_true')
options = parser.parse_args()
source = options.source.resolve()
assert source.stat().st_size == 374505632
h = hashlib.sha256()
with source.open('rb') as stream:
    for block in iter(lambda: stream.read(1048576), b''):
        h.update(block)
assert h.hexdigest() == '95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422'
out = options.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out / 'sources').mkdir()
(out / 'sources/shared-united-female.glb').symlink_to(source)
(out / 'scripts').mkdir()
for recipe in Path(__file__).with_name('recipes').glob('*.py'):
    shutil.copy2(recipe, out / 'scripts' / recipe.name)
subprocess.run([sys.executable, str(out / 'scripts/build_pair.py')], check=True)
expected = {
 'liver_hra_female_exterior_r02': 'e9abb0c2503a3fa9d725988451e630283ec2c902c182b812219f2d73f3ab1038',
 'spleen_hra_female_r03': '4e2637cf6c844aef85ab77c2c1049d4e7647348a13c34d784795b98825f7c8c7',
}
for name, digest in expected.items():
    model = out / 'models' / name / (name + '.glb')
    assert hashlib.sha256(model.read_bytes()).hexdigest() == digest
    if options.render:
        subprocess.run(['blender', '-b', '--python', str(ROOT / 'tests/blender/audit_exact_tuple_topology.py'), '--', str(model), str(out / (name + '-topology.json'))], check=True)
if options.render:
    subprocess.run(['blender', '-b', '--python', str(out / 'scripts/render_candidates.py'), '--', *expected], check=True)
print('PASS exact source-bound pair reconstruction; no anatomy/runtime certification or automatic source download.')
