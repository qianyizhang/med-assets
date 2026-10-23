"""Reconstruct accepted context bytes from the explicit atlas, not from accepted GLBs."""
import copy
import hashlib
import json
from pathlib import Path
import struct

from extract_exact_subsets import j as atlas, subset, write_glb

ROOT = Path(__file__).resolve().parents[1]
ROLES = json.loads(Path(__file__).with_name('explicit-role-data.json').read_text())


def prepare(source_id, roots, organ, only_names=None):
    subset(source_id, roots)
    source = ROOT / 'models' / source_id / (source_id + '.glb')
    raw = source.read_bytes()
    json_len = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + json_len])
    binary = raw[28 + json_len:]
    original = copy.deepcopy(gltf)
    role_rows = ROLES[organ]['rows']
    if only_names is not None:
        role_rows = [row for row in role_rows if row['source_mesh_name'] in only_names]
    mapping = {row['source_mesh_name']: row for row in role_rows}
    actual = {node['name'] for node in gltf['nodes'] if 'mesh' in node}
    assert actual == set(mapping)
    for row in role_rows:
        source_node = atlas['nodes'][row['source_atlas_node_id']]
        assert source_node['name'] == row['source_mesh_name'] and 'mesh' in source_node
    gltf['materials'] = []
    materials = {}
    for node in gltf['nodes']:
        if 'mesh' not in node:
            continue
        row = mapping[node['name']]
        role = row['illustrative_display_role']
        if role not in materials:
            materials[role] = len(gltf['materials'])
            gltf['materials'].append({
                'name': 'Illustrative_matte_' + organ + '_' + role,
                'pbrMetallicRoughness': {
                    'baseColorFactor': row['base_color_factor'],
                    'metallicFactor': 0,
                    'roughnessFactor': .78,
                },
                'emissiveFactor': [0, 0, 0],
                'doubleSided': True,
            })
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            primitive['material'] = materials[role]
    comparable = copy.deepcopy(gltf)
    for obj in [comparable, original]:
        obj.pop('materials', None)
        for mesh in obj['meshes']:
            for primitive in mesh['primitives']:
                primitive.pop('material', None)
    assert comparable == original
    output_id = source_id.replace('r01', 'r02')
    directory = ROOT / 'models' / output_id
    directory.mkdir()
    target = directory / (output_id + '.glb')
    write_glb(target, gltf, binary)
    result = target.read_bytes()
    new_len = struct.unpack_from('<I', result, 12)[0]
    assert result[28 + new_len:] == binary
    audit = {
        'id': output_id, 'parent_sha256': hashlib.sha256(raw).hexdigest(),
        'sha256': hashlib.sha256(result).hexdigest(),
        'all_binary_bytes_identical': True, 'all_non_material_json_identical': True,
        'all_selected_source_node_ids_names_roles_verified': True,
        'role_mapping': mapping,
        'scope': 'Final reviewed explicit display roles applied directly; no fuzzy matching. Colors illustrative, double-sided patches do not imply thickness.',
    }
    (directory / 'explicit-material-replay-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(output_id, audit['sha256'])


prepare('bladder_hra_female_context_r01', [
    'VH_F_urinary_bladder', 'VH_F_right_ureter', 'VH_F_left_ureter',
    'VH_F_uterus', 'VH_F_vagina', 'VH_F_rectum',
], 'bladder')
pancreas_names = {
    row['source_mesh_name'] for row in ROLES['pancreas']['rows']
    if row['illustrative_display_role'] in {'head', 'body', 'tail', 'neck', 'ucinate'}
}
prepare('pancreas_hra_female_r01', ['VH_F_pancreas'], 'pancreas', pancreas_names)
prepare('pancreas_hra_female_context_r01', [
    'VH_F_pancreas', 'VH_F_ducts_of_pancreas', 'VH_F_duodenum', 'VH_F_spleen',
], 'pancreas')
import bladder_interface_normals  # bounded dome/base update only
import pancreas_guarded_normals  # guarded standalone normals transferred by exact name
