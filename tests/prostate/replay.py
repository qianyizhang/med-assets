#!/usr/bin/env python3
"""Rebuild review context in a fresh directory; unchanged source is the deliverable."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
options = parser.parse_args()
paths = {
    'VH_M_Prostate.glb': ('models/prostate/exports/hra-v1.1/VH_M_Prostate.glb', 'ec1023e0a1b81f71865872bb720404abc7bb6378a54ac71fa9f24579b097f48a'),
    'VH_M_Urinary_Bladder.glb': ('sources/datasets/hra/prostate-v1.1/context/VH_M_Urinary_Bladder.glb', '43b7f17e3f498d5e494a7757ce86c183ae458f83724ceaf922f6bdd6a35ff339'),
}
for relative, digest in paths.values():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
out = options.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out / 'source/hra').mkdir(parents=True)
(out / 'scripts').mkdir()
for name, (relative, _) in paths.items():
    shutil.copy2(ROOT / relative, out / 'source/hra' / name)
for recipe in Path(__file__).with_name('recipes').glob('*.py'):
    shutil.copy2(recipe, out / 'scripts' / recipe.name)
for recipe in ('render_source.py', 'render_context.py'):
    subprocess.run(['blender', '-b', '--python', str(out / 'scripts' / recipe)], check=True)
produced = out / 'models/prostate_hra/exports/source-candidate-01/prostate_hra_native_frame.glb'
assert hashlib.sha256(produced.read_bytes()).hexdigest() == paths['VH_M_Prostate.glb'][1]
subprocess.run(['blender', '-b', '--python', str(ROOT / 'tests/blender/audit_exact_tuple_topology.py'), '--', str(produced), str(out / 'exact-tuple-topology.json')], check=True)
print('PASS source identity, offline rendering execution and explicit edge audit. No anatomy/runtime certification.')
