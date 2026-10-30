"""Restore the native opaque-exterior presentation in separate GLB derivatives.

Mesh/material/accessor data and the BIN chunk are preserved. This changes which
source nodes participate in the exterior scene, not the RV inlet geometry.
"""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_SHA256 = '09783d389fec56375a7ebef6796cb63f6c062a69887eeec4081b1223c5e1700e'
SOURCES = {
    'static': ('body/anatomy-workshop-r1/meshes/heart_detailed.glb',
               '83dd48731d0cc67e8aa61abbd7b03163fb01bcba78f501e9d2c939927aaecf6e', 389),
    'animated-source': ('heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb',
                        '6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263', 248),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_glb(data):
    if len(data) < 28 or struct.unpack_from('<III', data) != (0x46546c67, 2, len(data)):
        raise ValueError('Expected a complete GLB2 payload')
    chunks = []
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if length % 4 or offset + length > len(data):
            raise ValueError('Invalid GLB chunk')
        chunks.append((kind, data[offset:offset + length]))
        offset += length
    if offset != len(data) or [c[0] for c in chunks] != [0x4e4f534a, 0x004e4942]:
        raise ValueError('Expected exactly JSON and BIN chunks')
    return json.loads(chunks[0][1]), chunks[1][1]

def write_glb(doc, binary):
    data = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    data += b' ' * (-len(data) % 4)
    body = struct.pack('<II', len(data), 0x4e4f534a) + data
    body += struct.pack('<II', len(binary), 0x004e4942) + binary
    return struct.pack('<III', 0x46546c67, 2, len(body) + 12) + body

def build(repo, kind, output):
    if output.exists():
        raise ValueError('Refusing an existing output directory')
    rel, expected, expected_nodes = SOURCES[kind]
    source = (repo / rel).read_bytes()
    if sha(source) != expected:
        raise ValueError('Source identity mismatch; pointers and substitute variants are not inputs')
    spec_bytes = (HERE / 'visibility-spec.json').read_bytes()
    if sha(spec_bytes) != SPEC_SHA256:
        raise ValueError('Native visibility specification identity mismatch')
    spec = json.loads(spec_bytes)
    hidden = set(spec['opaque_exterior_hidden_names'])
    if len(hidden) != 123 or len(spec['opaque_exterior_hidden_names']) != 123:
        raise ValueError('Expected the 123 independently inspected native internal nodes')
    original, binary = read_glb(source)
    if len(original['nodes']) != expected_nodes or len(original['scenes']) != 1 or original.get('skins'):
        raise ValueError('Unexpected source graph')
    names = [n.get('name') for n in original['nodes']]
    if len(set(names)) != len(names) or not hidden.issubset(names):
        raise ValueError('Native node membership does not exactly match this source')
    remove = {i for i, n in enumerate(original['nodes']) if n['name'] in hidden or
              (kind == 'static' and n.get('extras', {}).get('view_role') == 'cutaway')}
    kept = [i for i in range(len(names)) if i not in remove]
    mapping = {old: new for new, old in enumerate(kept)}
    doc = copy.deepcopy(original)
    doc['nodes'] = [copy.deepcopy(original['nodes'][i]) for i in kept]
    for node in doc['nodes']:
        if 'children' in node:
            node['children'] = [mapping[i] for i in node['children'] if i in mapping]
    for scene in doc['scenes']:
        scene['nodes'] = [mapping[i] for i in scene['nodes'] if i in mapping]
        scene['name'] += ' | source-defined opaque exterior'
        scene.setdefault('extras', {})['README'] = (
            'Opaque clinical-color exterior presentation only. Native collections 02/03 '
            'are absent from this scene, as in the original opaque exterior controls. '
            'Use the retained original full/cutaway/native assets for internal views. '
            'Geometry and visible morph data are unchanged; this does not repair '
            'the source RV inlet/apparatus relationship or establish lumen continuity.')
        scene['extras']['material_set_names'] = 'Fixed clinical teaching colors; no material/cutaway selector in this derivative'
        scene['extras']['pericardial_layers'] = (
            'Complete chamber wall surfaces remain. The removable parietal '
            'pericardial envelope and internal valve/support nodes are absent '
            'from this exterior scene; use the unchanged native source for those views.')
        if kind == 'static':
            scene['extras']['animation_model'] = 'Static end-diastolic exterior snapshot; this derivative has no animation clip'
            scene['extras']['animation_delivery'] = 'Static presentation derivative, not the editable native source'
        else:
            scene['extras']['animation_model'] = (
                'Unchanged authored exterior morphs: chamber contraction and '
                'surface structures only. No valve/chord motion participates '
                'in this scene. No biomechanical or flow simulation.')
            scene['extras']['animation_delivery'] = (
                'Portable exterior-only 0.8-second source morph clip; '
                'not the editable original. Internal animated structures remain '
                'available in the unchanged original full/cutaway/native assets.')
    removed_channels = []
    for animation in doc.get('animations', []):
        channels = []
        for channel in animation['channels']:
            target = channel['target']['node']
            if target in remove:
                removed_channels.append(names[target])
                continue
            channel['target']['node'] = mapping[target]
            channels.append(channel)
        animation['channels'] = channels
    doc.setdefault('asset', {}).setdefault('extras', {})['presentation_derivative'] = {
        'id': 'source-opaque-exterior-r01', 'source_sha256': expected,
        'visibility_spec_sha256': sha(spec_bytes),
        'geometry_changed': False,
        'scope': 'Native opaque-exterior visibility only; internal geometry remains unresolved',
    }
    rendered_meshes = sum('mesh' in n for n in doc['nodes'])
    if rendered_meshes != 124:
        raise ValueError('Exterior membership must leave exactly 124 source mesh nodes')
    result = write_glb(doc, binary)
    record = {
        'kind': 'source-visibility-presentation-derivative', 'source': rel,
        'source_sha256': expected, 'candidate_sha256': sha(result),
        'candidate_file': f'{kind}-opaque-exterior.glb', 'candidate_bytes': len(result),
        'visibility_spec_sha256': sha(spec_bytes), 'unchanged_bin_sha256': sha(binary),
        'source_mesh_nodes': sum('mesh' in n for n in original['nodes']),
        'candidate_mesh_nodes': rendered_meshes,
        'source_node_count': len(names), 'candidate_node_count': len(kept),
        'removed_nodes': [names[i] for i in sorted(remove)],
        'removed_internal_animation_channels': removed_channels,
        'retained_animation_channels': sum(len(x['channels']) for x in doc.get('animations', [])),
        'original_to_candidate_node_index': mapping,
        'scope': 'Only source-defined exterior participation; no geometry correction, performance, anatomy or runtime claim',
        'retention': 'Original full/cutaway/native artifacts unchanged; unused original mesh/accessor payload retained in candidate',
    }
    output.mkdir(parents=True)
    (output / record['candidate_file']).write_bytes(result)
    (output / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--kind', choices=SOURCES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    record = build(args.repo, args.kind, args.output)
    print(json.dumps({k: record[k] for k in ['candidate_file', 'candidate_sha256',
        'candidate_mesh_nodes', 'retained_animation_channels']}, indent=2))
