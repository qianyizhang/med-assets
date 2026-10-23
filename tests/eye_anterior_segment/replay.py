#!/usr/bin/env python3
"""Replay into a NEW directory; never mutate retained source or review evidence."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'sources/datasets/hra/eye-male-right-v1.3/hra-source.glb'
EXPECTED_SOURCE = '1a6ecc528e98e0bddb8e2905e4ddb799eb471383f7274dbb9bdd1676b06be73b'
EXPECTED = {
    'source-subset.glb': '372a40daf5c032d311fd8ce813126392aa070dedd2082dfc14339ba8884354be',
    'material-only.glb': '658996d556addf07da3015ff8d59eddde291a88e5dadcf7ca9c491433b240bfc',
    'normal-material.glb': '457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750',
    'context-diagnostic.glb': '072afc7354352d293227b4524d99c92bda3861670d2380526fd324ff2e67384c',
}
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--render', action='store_true')
options = parser.parse_args()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE, 'Source missing/unresolved or wrong bytes'
out = options.output.resolve()
out.mkdir(parents=True, exist_ok=False)
for folder in ('sources', 'models', 'reviews', 'scripts'):
    (out / folder).mkdir()
shutil.copy2(SOURCE, out / 'sources/hra-source.glb')
for script in Path(__file__).with_name('recipes').glob('*.py'):
    shutil.copy2(script, out / 'scripts' / script.name)
for script in ('build_candidates.py', 'build_context.py', 'verify_export.py'):
    subprocess.run([sys.executable, str(out / 'scripts' / script)], check=True)
for name, digest in EXPECTED.items():
    assert hashlib.sha256((out / 'models' / name).read_bytes()).hexdigest() == digest, name
if options.render:
    subprocess.run(['blender', '-b', '--python', str(out / 'scripts/render.py'), '--', 'normal-material'], check=True)
print('PASS: four deterministic exports and selected source-data preservation. No anatomy/runtime certification.')
