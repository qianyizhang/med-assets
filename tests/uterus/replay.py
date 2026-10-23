#!/usr/bin/env python3
"""Fresh-directory deterministic exterior reconstruction; never modify evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'sources/datasets/hra/uterus-v1.1/VH_F_Uterus.glb'
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
options = parser.parse_args()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'a484956788ecc2ab05ca7720d9b33d265677e238f144cc28481aad2f7a0c9a95'
out = options.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out / 'source/hra').mkdir(parents=True)
(out / 'scripts').mkdir()
shutil.copy2(SOURCE, out / 'source/hra/VH_F_Uterus.glb')
for recipe in Path(__file__).with_name('recipes').glob('*.py'):
    shutil.copy2(recipe, out / 'scripts' / recipe.name)
for recipe in ('rebuild_and_render.py', 'verify_coordinates.py'):
    subprocess.run(['blender', '-b', '--python', str(out / 'scripts' / recipe)], check=True)
produced = out / 'models/uterus_hra/exports/source-candidate-02/uterus_hra_native_frame.glb'
assert hashlib.sha256(produced.read_bytes()).hexdigest() == '627f169a5e02f95102af994f7346cd0f85e454651231867c6829618ef1b0c356'
report = json.loads((out / 'reviews/uterus_hra/source-candidate-02/full-coordinate-tests.json').read_text())
assert set(report['excluded_source_nodes']) == {'VH_F_anterior_wall_of_uterus', 'VH_F_posterior_wall_of_uterus'}
assert all(v['all_vertex_coordinates_match_to_0_1_micrometre'] and v['triangle_count_match'] for v in report['checks'].values())
subprocess.run(['blender', '-b', '--python', str(ROOT / 'tests/blender/audit_exact_tuple_topology.py'), '--', str(produced), str(out / 'exact-tuple-topology.json')], check=True)
print('PASS deterministic export, rounded coordinate sets and triangle counts. No anatomy/runtime certification.')
