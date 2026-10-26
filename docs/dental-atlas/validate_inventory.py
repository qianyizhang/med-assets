#!/usr/bin/env python3
"""Validate research inventory semantics, not anatomy, geometry or licensing."""
import json
from pathlib import Path


def validate(data):
    assert data['status'] == 'research_spec_only'
    assert data['scope']['geometry_included'] is False
    teeth = data['teeth']
    expected = {str(q * 10 + n) for q in range(1, 9)
                for n in range(1, 6 if q > 4 else 9)}
    assert len(teeth) == 52
    assert {t['fdi'] for t in teeth} == expected
    assert len({t['id'] for t in teeth}) == 52
    assert len({t['label_en'] for t in teeth}) == 52
    assert len({t['label_zh'] for t in teeth}) == 52
    assert sum(t['dentition'] == 'permanent' for t in teeth) == 32
    assert sum(t['dentition'] == 'primary' for t in teeth) == 20
    nodes = data['scene_roots'] + data['arch_nodes'] + teeth
    by_id = {n['id']: n for n in nodes}
    assert len(by_id) == len(nodes), 'duplicate scene node'
    for node in nodes:
        seen = set()
        current = node
        while current['parent'] is not None:
            assert current['id'] not in seen, 'hierarchy cycle'
            seen.add(current['id'])
            assert current['parent'] in by_id, 'unknown parent'
            current = by_id[current['parent']]
    catalog = {c['id']: c for c in data['component_catalog']}
    assert len(catalog) == len(data['component_catalog'])
    templates = data['component_templates']
    for template in templates.values():
        assert len(template) == len(set(template))
        assert set(template) <= set(catalog)
    kinds = {'surface', 'tissue', 'space', 'space_region', 'support_tissue', 'annotation', 'landmark'}
    assert all(c['kind'] in kinds for c in catalog.values())
    names = ['central incisor', 'lateral incisor', 'canine', 'first premolar',
             'second premolar', 'first molar', 'second molar', 'third molar']
    primary_names = names[:3] + names[5:7]
    instance_ids = set()
    for tooth in teeth:
        quadrant, position = map(int, tooth['fdi'])
        dentition = 'primary' if quadrant > 4 else 'permanent'
        arch = 'maxillary' if quadrant in {1, 2, 5, 6} else 'mandibular'
        side = 'right' if quadrant in {1, 4, 5, 8} else 'left'
        assert tooth['dentition'] == dentition
        assert tooth['arch'] == arch and tooth['patient_side'] == side
        assert tooth['position_from_midline'] == position
        assert tooth['parent'] == f'{dentition}/{arch}'
        assert tooth['id'] == f"{tooth['parent']}/tooth_{tooth['fdi']}"
        assert tooth['tooth_type'] == (primary_names if dentition == 'primary' else names)[position-1]
        assert tooth['status'] == 'specified_not_built'
        assert all(tooth[k] is None for k in ('specimen_id', 'source_id', 'root_count', 'canal_count'))
        for component in templates[tooth['component_template']]:
            instance_id = f"{tooth['id']}/{component}"
            assert instance_id not in instance_ids
            instance_ids.add(instance_id)
    sources = {s['id'] for s in data['sources']}
    assert len(sources) == len(data['sources'])
    assert data['numbering']['source_id'] in sources
    for collection in ('condition_catalog', 'tool_material_catalog'):
        entries = data[collection]
        assert len({e['id'] for e in entries}) == len(entries)
        for entry in entries:
            assert entry['status'] == 'specified_not_built'
            assert set(entry['source_ids']) <= sources
    assert all(t['geometry_source'] is None and t['dimensions_mm'] is None
               for t in data['tool_material_catalog'])
    assert {'source_file_sha256', 'source_affine', 'license_identifier_and_version',
            'review_status'} <= set(data['mesh_record_requirements'])
    return len(instance_ids)


if __name__ == '__main__':
    data = json.loads(Path(__file__).with_name('inventory.json').read_text())
    instances = validate(data)
    print(f'PASS: 32 permanent + 20 primary teeth; {instances} component slots; '
          f"{len(data['condition_catalog'])} condition families; "
          f"{len(data['tool_material_catalog'])} tool/material slots.")
    print('Research structure only: no mesh, source-license, visual or anatomical pass.')
