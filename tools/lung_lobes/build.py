#!/usr/bin/env python3
"""Hash-pinned five-lobe teaching materials; source geometry stays byte-exact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

BASELINE_SHA256 = '966a4c225be028e616f6f813e8d4232582995a82b8121a42257c1be53087cb19'
BASELINE_BYTES = 23253972
GROUPS = (
    ('RUL', 'Right upper lobe', 'VH_F_R_lung_upper_lobe', 4),
    ('RML', 'Right middle lobe', 'VH_F_R_lung_middle_lobe', 3),
    ('RLL', 'Right lower lobe', 'VH_F_R_lung_lower_lobe', 6),
    ('LUL', 'Left upper lobe', 'VH_F_L_lung_upper_lobe', 6),
    ('LLL', 'Left lower lobe', 'VH_F_L_lung_lower_lobe', 6),
)
COLORS = ('#dda64a', '#e59783', '#985d73', '#66b8aa', '#697fa9')
SCOPE = ('Draft source-labeled lobe identification only. False colors are illustrative, '
         'not natural tissue or physiology. Source annotation boundaries remain; '
         'no segment, airway completeness, breathing, clinical or runtime approval.')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack(raw):
    require(len(raw) >= 28, 'Truncated GLB or unresolved LFS pointer')
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a and size % 4 == 0 and 28 + size <= len(raw), 'Invalid JSON chunk')
    bsize, bkind = struct.unpack_from('<II', raw, 20 + size)
    require(bkind == 0x004e4942 and bsize % 4 == 0 and 28 + size + bsize == len(raw), 'Invalid BIN chunk')
    return json.loads(raw[20:20+size]), raw[28+size:]


def pack(doc, blob):
    j = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    j += b' ' * (-len(j) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(j) + len(blob))
            + struct.pack('<II', len(j), 0x4e4f534a) + j
            + struct.pack('<II', len(blob), 0x004e4942) + blob)


def linear(hex_color):
    rgb = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb] + [1.0]


def membership(doc):
    result, used = [], set()
    for number, (key, label, parent_name, count) in enumerate(GROUPS, 1):
        parents = [n for n in doc['nodes'] if n.get('name') == parent_name]
        require(len(parents) == 1, 'Missing or duplicate lobe parent')
        indices = parents[0]['children']
        require(len(indices) == count, 'Unexpected lobe membership')
        names, meshes = [], []
        for i in indices:
            n = doc['nodes'][i]
            require('mesh' in n and 'children' not in n and n['mesh'] not in used, 'Unexpected lobe child')
            used.add(n['mesh'])
            meshes.append(n['mesh'])
            names.append(n['name'])
        result.append({'number': number, 'id': key, 'label': label, 'parent': parent_name,
                       'meshes': meshes, 'nodes': names, 'srgb': COLORS[number-1]})
    require(len(used) == 25, 'Expected exactly 25 lobe child meshes')
    return result


def transform(doc, revision):
    require(revision in ('v1', 'v2'), 'Unknown revision')
    out = copy.deepcopy(doc)
    groups = membership(doc)
    for group in groups:
        material = copy.deepcopy(doc['materials'][0])
        material['name'] = 'Teaching_' + group['id']
        material['pbrMetallicRoughness']['baseColorFactor'] = linear(group['srgb'])
        if revision == 'v2':
            material['pbrMetallicRoughness']['roughnessFactor'] = .65
        mid = len(out['materials'])
        out['materials'].append(material)
        for mi in group['meshes']:
            for primitive in out['meshes'][mi]['primitives']:
                require(primitive['material'] == 0, 'Lobe child has unexpected source material')
                primitive['material'] = mid
    out.setdefault('extras', {})['lobeTeaching'] = {
        'status': 'draft', 'revision': revision, 'scope': SCOPE,
        'baselineSha256': BASELINE_SHA256, 'groups': groups,
        'labelsArePresentationOnly': True,
    }
    return out


def validate_pair(before, after, revision):
    old, old_bin = unpack(before)
    new, new_bin = unpack(after)
    require(old_bin == new_bin, 'Geometry/normal BIN changed')
    require(new == transform(old, revision), 'Unexpected JSON, transform, material or label change')
    # Recover all source fields, allowing only the declared material edits and scoped metadata.
    restored = copy.deepcopy(new)
    restored['materials'] = old['materials']
    restored['meshes'] = old['meshes']
    if 'extras' in old:
        restored['extras'] = old['extras']
    else:
        restored.pop('extras', None)
    require(restored == old, 'Source fields changed')
    return {'binSha256': sha(old_bin), 'binExact': True, 'sourceFieldsRecovered': True,
            'meshCount': len(new['meshes']), 'changedMaterialAssignments': 25,
            'triangles': sum(new['accessors'][p['indices']]['count']//3
                             for m in new['meshes'] for p in m['primitives'])}


def build(raw, revision='v2'):
    require(len(raw) == BASELINE_BYTES and sha(raw) == BASELINE_SHA256,
            'Exact hydrated baseline size/SHA-256 required')
    doc, blob = unpack(raw)
    result = pack(transform(doc, revision), blob)
    checks = validate_pair(raw, result, revision)
    return result, {'baselineSha256': sha(raw), 'baselineBytes': len(raw),
                    'revision': revision, 'candidateSha256': sha(result), 'candidateBytes': len(result),
                    'scope': SCOPE, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', choices=('v1', 'v2'), default='v2')
    args = parser.parse_args()
    candidate, record = build(args.source.read_bytes(), args.revision)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'lung-lobes.glb').write_bytes(candidate)
    (args.output / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
