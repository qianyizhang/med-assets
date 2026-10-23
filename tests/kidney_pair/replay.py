#!/usr/bin/env python3
"""Replay metadata/material-only derivatives in a new directory, never retained assets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--render', action='store_true')
options = parser.parse_args()
expected = {
 'left': ('58f0227d45b14d7bcfd2ed05a7bcd76000051ea08d52f844feebd70d612f8084', '8e55b5ae48821f067f41bd23ffdd668f68c7ff705cf49e9a40287042fee469fc'),
 'right': ('d80ee5a109a5cd5c90ca0770d1087e28786e2c545747cbae15a5ea22b4b0af86', '977d0a283de7071a2e8aaeb8900c5a6dc8d0ba770eb458e996dc66cc249c0b56'),
}
# Read exact source identities from retained immutable provider receipts.
for side in expected:
    prov = json.loads((ROOT / f'sources/datasets/hra/kidney-female-{side}-v1.3/provenance.json').read_text())
    assert prov['files'][0]['sha256'] == expected[side][0]
out = options.output.resolve()
out.mkdir(parents=True, exist_ok=False)
work = out / 'candidate'
work.mkdir()
for side, short in [('left', 'l'), ('right', 'r')]:
    src = ROOT / f'sources/datasets/hra/kidney-female-{side}-v1.3'
    assert hashlib.sha256((src / f'3d-vh-f-kidney-{short}.glb').read_bytes()).hexdigest() == expected[side][0]
    dest = out / f'kidney-reference-source-screen/source/hra/kidney-female-{side}'
    shutil.copytree(src, dest)
for recipe in Path(__file__).with_name('recipes').glob('*.py'):
    shutil.copy2(recipe, work / recipe.name)
subprocess.run([sys.executable, str(work / 'build_candidates.py')], check=True)
for side, (_, digest) in expected.items():
    assert hashlib.sha256((work / f'models/kidney_{side}/kidney_{side}_hra_female_r02.glb').read_bytes()).hexdigest() == digest
source = ROOT / 'sources/datasets/hra/kidney-female-left-v1.3/3d-vh-f-kidney-l.glb'
candidate = work / 'models/kidney_left/kidney_left_hra_female_r02.glb'
result = subprocess.check_output([sys.executable, str(Path(__file__).with_name('exact_index_audit.py')), str(source), str(candidate)], text=True)
report = json.loads(result)
assert report['source']['collapsedTriangleCount'] == report['candidate']['collapsedTriangleCount'] == 2
(out / 'left-exact-index-audit.json').write_text(result)
if options.render:
    subprocess.run(['blender', '-b', '--python', str(work / 'render_exact.py')], check=True)
print('PASS exact pair rebuild, unchanged BIN/JSON recovery and inherited left index identities. No anatomy/runtime certification.')
