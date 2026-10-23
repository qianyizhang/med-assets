#!/usr/bin/env python3
"""No network, no installation; write only into a new output directory."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def checked(path, expected_hash, expected_size=None):
    if expected_size is not None and path.stat().st_size != expected_size:
        raise ValueError('Dependency byte-size mismatch: ' + str(path))
    if sha(path) != expected_hash:
        raise ValueError('Dependency SHA-256 mismatch: ' + str(path))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, type=Path, help='Existing official HRA united-female v1.10 GLB, never fetched/copied')
parser.add_argument('--shared-recipes', required=True, type=Path, help='Existing tests/liver_spleen/recipes directory; two files are hash-pinned')
parser.add_argument('--output', required=True, type=Path, help='New, nonexistent local output directory')
options = parser.parse_args()
if sys.flags.optimize:
    raise RuntimeError('Run without -O: source-preservation assertions must remain enabled.')
import numpy as np
manifest = json.loads((HERE / 'dependency-map.json').read_text())
roles = json.loads((HERE / 'recipes/explicit-role-data.json').read_text())
source = options.source.resolve()
source_meta = manifest['external_source']
checked(source, source_meta['sha256'], source_meta['bytes'])
recipe_paths = []
for dependency in manifest['external_recipe_files']:
    path = options.shared_recipes.resolve() / Path(dependency['repo_relative_path']).name
    checked(path, dependency['sha256'], dependency['bytes'])
    recipe_paths.append(path)
# Internal files must be an exact self-described staging payload; do not execute unchecked additions.
for dependency in manifest['local_recipe_files']:
    path = HERE / dependency['path']
    checked(path, dependency['sha256'], dependency['bytes'])
output = options.output.resolve()
output.mkdir(parents=True, exist_ok=False)
(output / 'sources').mkdir()
(output / 'sources/shared-united-female.glb').symlink_to(source)
(output / 'scripts').mkdir()
for path in recipe_paths:
    shutil.copy2(path, output / 'scripts' / path.name)
for dependency in manifest['local_recipe_files']:
    path = HERE / dependency['path']
    shutil.copy2(path, output / 'scripts' / path.name)
subprocess.run([sys.executable, '-B', str(output / 'scripts/build_pair.py')], check=True)
results = []
for organ, data in roles.items():
    candidate_id = data['candidate_id']
    path = output / 'models' / candidate_id / (candidate_id + '.glb')
    checked(path, data['expected_sha256'])
    raw = path.read_bytes()
    json_len = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + json_len])
    mesh_nodes = [node for node in gltf['nodes'] if 'mesh' in node]
    mapping = {row['source_mesh_name']: row for row in data['rows']}
    assert {node['name'] for node in mesh_nodes} == set(mapping)
    for node in mesh_nodes:
        row = mapping[node['name']]
        expected = 'Illustrative_matte_' + organ + '_' + row['illustrative_display_role']
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            material = gltf['materials'][primitive['material']]
            assert material['name'] == expected
            assert material['pbrMetallicRoughness']['baseColorFactor'] == row['base_color_factor']
    results.append({'id': candidate_id, 'sha256': sha(path), 'bytes': path.stat().st_size,
                    'exact_accepted_hash_match': True, 'all_roles_checked': len(mesh_nodes)})
bladder_audit = json.loads((output / 'models/bladder_hra_female_context_r03/normal-only-derivation-audit.json').read_text())
pancreas_audit = json.loads((output / 'models/pancreas_hra_female_normals35_guarded_r04/normal-only-derivation-audit.json').read_text())
assert bladder_audit['changed_normal_vectors'] == 486
assert bladder_audit['all_non_normal_binary_bytes_identical']
expected_guards = {
    'normal_vectors_updated': 26124, 'illconditioned_source_triangles_preserved': 101,
    'protected_sliver_normal_indices': 222, 'source_zero_normals_preserved': 20,
    'nonmanifold_virtual_edges_not_smoothed': 8, 'degenerate_faces': 8,
    'original_indices_skipped_for_multiple_smoothing_fans': 2,
    'unchanged_geometric_crease_edges_above_threshold': 47,
    'source_zero_normals_replaced_expected_zero': 0,
}
for key, expected in expected_guards.items():
    assert pancreas_audit[key] == expected, key
assert pancreas_audit['all_json_identical'] and pancreas_audit['all_non_normal_binary_bytes_identical']
# Source recheck catches unintended changes; accepted exports never enter the replay.
checked(source, source_meta['sha256'], source_meta['bytes'])
report = {
    'result': 'PASS exact reconstruction of two previously accepted exports',
    'source': {'sha256': source_meta['sha256'], 'bytes': source_meta['bytes'], 'read_only_external_symlink': True, 'checked_before_and_after': True},
    'dependency_map_sha256': sha(HERE / 'dependency-map.json'),
    'runtime': {'python': platform.python_version(), 'numpy': np.__version__},
    'outputs': results, 'bladder_updated_normals': 486, 'pancreas_guard_counts': expected_guards,
    'pancreas_max_normal_change_degrees': pancreas_audit['max_angular_change_degrees'],
    'source_boundary': 'Only external original atlas + listed text recipes/data are build inputs; accepted GLBs, archived normals, large history and image renders are not inputs.',
    'validation_boundary': 'Byte reproduction, explicit-role checks and bounded normal/source guards only. No new anatomy, clinical, normality, closed-volume, flow, clean-format, visual or runtime approval.',
}
(output / 'replay-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
