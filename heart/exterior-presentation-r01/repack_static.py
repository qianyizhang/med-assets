"""Repack the exact static r01 heart GLB by removing unused scene data."""

import argparse
import os
from pathlib import Path
import tempfile

from build import read_glb, sha, write_glb

BASELINE_SHA256 = '595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f'
MIN_SAVINGS = 5_000_000


def read_baseline(path):
    data = path.read_bytes()
    if sha(data) != BASELINE_SHA256:
        raise ValueError('Static r01 baseline SHA-256 mismatch (requires the hydrated GLB)')
    return data


def repack(data):
    doc, binary = read_glb(data)
    # This pinned scene has 124 mesh roots and no other nodes, images, or
    # animation. The only references to these tables are the ones below.
    meshes = sorted({node['mesh'] for node in doc['nodes']})
    primitives = [p for i in meshes for p in doc['meshes'][i]['primitives']]
    materials = sorted({p['material'] for p in primitives})
    accessors = sorted({i for p in primitives for i in (p['indices'], *p['attributes'].values())})
    views = sorted({doc['accessors'][i]['bufferView'] for i in accessors})

    mesh_ids, material_ids, accessor_ids, view_ids = (
        {old: new for new, old in enumerate(indices)}
        for indices in (meshes, materials, accessors, views)
    )
    for node in doc['nodes']:
        node['mesh'] = mesh_ids[node['mesh']]
    for primitive in primitives:
        primitive['material'] = material_ids[primitive['material']]
        primitive['indices'] = accessor_ids[primitive['indices']]
        primitive['attributes'] = {
            name: accessor_ids[i] for name, i in primitive['attributes'].items()
        }
    for i in accessors:
        accessor = doc['accessors'][i]
        accessor['bufferView'] = view_ids[accessor['bufferView']]

    packed = bytearray()
    for i in views:
        view = doc['bufferViews'][i]
        start = view['byteOffset']
        view['byteOffset'] = len(packed)
        packed.extend(binary[start:start + view['byteLength']])
        packed.extend(b'\0' * (-len(packed) % 4))
    for table, indices in (
        ('meshes', meshes), ('materials', materials), ('accessors', accessors), ('bufferViews', views)
    ):
        doc[table] = [doc[table][i] for i in indices]
    doc['buffers'][0]['byteLength'] = len(packed)
    return write_glb(doc, packed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New GLB path in an existing directory')
    args = parser.parse_args()
    try:
        baseline = read_baseline(args.source)
        result = repack(baseline)
        savings = len(baseline) - len(result)
        if savings < MIN_SAVINGS:
            raise ValueError(f'Repack saved only {savings:,} bytes')
        # Place the complete file atomically. A competing writer or existing
        # symlink at the destination makes link fail without replacing it.
        with tempfile.TemporaryDirectory(dir=args.output.parent) as temp:
            staged = Path(temp) / 'candidate.glb'
            staged.write_bytes(result)
            os.link(staged, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Repack failed: {error}\n')
    print(f'{args.output.name}: {len(result):,} bytes, SHA-256 {sha(result)}, saved {savings:,} bytes')


if __name__ == '__main__':
    main()
