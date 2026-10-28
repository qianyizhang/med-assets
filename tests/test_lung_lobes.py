"""Offline failure controls for the bounded material-only lobe derivative."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('lung_build', Path(__file__).resolve().parents[1] / 'tools/lung_lobes/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def fixture():
    doc = {'nodes': [], 'meshes': [], 'materials': [
        {'name': 'lung_mat', 'pbrMetallicRoughness': {'baseColorFactor': [.7, .4, .4, 1],
                                                  'metallicFactor': 0, 'roughnessFactor': .25}},
        {'name': 'airway', 'pbrMetallicRoughness': {'baseColorFactor': [.8, .8, .8, 1]}}],
        'accessors': [{'count': 3}], 'extras': {'preserve': 'source provenance'}}
    for _, _, name, count in build.GROUPS:
        parent = {'name': name, 'children': []}
        doc['nodes'].append(parent)
        for i in range(count):
            parent['children'].append(len(doc['nodes']))
            doc['nodes'].append({'name': name + str(i), 'mesh': len(doc['meshes'])})
            doc['meshes'].append({'primitives': [{'indices': 0, 'material': 0}]})
    doc['nodes'].append({'name': 'airway', 'mesh': len(doc['meshes']), 'translation': [1, 2, 3]})
    doc['meshes'].append({'primitives': [{'indices': 0, 'material': 1}]})
    return doc


class LobeTests(unittest.TestCase):
    def setUp(self):
        self.doc = fixture()
        self.old = build.pack(self.doc, b'1234')
        self.new = build.transform(self.doc, 'v2')

    def test_allowed_scope_and_right_left_mapping(self):
        groups = build.membership(self.doc)
        self.assertEqual([g['id'] for g in groups], ['RUL', 'RML', 'RLL', 'LUL', 'LLL'])
        self.assertEqual(len({m for g in groups for m in g['meshes']}), 25)
        self.assertEqual(self.new['nodes'], self.doc['nodes'])
        self.assertEqual(self.new['meshes'][-1], self.doc['meshes'][-1])
        self.assertEqual(self.new['materials'][:2], self.doc['materials'])
        self.assertTrue(build.validate_pair(self.old, build.pack(self.new, b'1234'), 'v2')['binExact'])

    def test_reject_wrong_lobe_material(self):
        self.new['meshes'][0]['primitives'][0]['material'] += 1
        with self.assertRaisesRegex(ValueError, 'Unexpected JSON'):
            build.validate_pair(self.old, build.pack(self.new, b'1234'), 'v2')

    def test_reject_geometry_and_transform_changes(self):
        with self.assertRaisesRegex(ValueError, 'BIN changed'):
            build.validate_pair(self.old, build.pack(self.new, b'1235'), 'v2')
        self.new['nodes'][-1]['translation'][0] += .1
        with self.assertRaisesRegex(ValueError, 'Unexpected JSON'):
            build.validate_pair(self.old, build.pack(self.new, b'1234'), 'v2')

    def test_reject_airway_material_and_missing_scope(self):
        for mutation in ('airway', 'scope'):
            out = copy.deepcopy(self.new)
            if mutation == 'airway':
                out['materials'][1]['name'] = 'unexpected'
            else:
                del out['extras']['lobeTeaching']['scope']
            with self.assertRaisesRegex(ValueError, 'Unexpected JSON'):
                build.validate_pair(self.old, build.pack(out, b'1234'), 'v2')

    def test_reject_duplicate_and_missing_membership(self):
        self.doc['nodes'][0]['children'][1] = self.doc['nodes'][0]['children'][0]
        with self.assertRaisesRegex(ValueError, 'Unexpected lobe child'):
            build.membership(self.doc)
        self.doc['nodes'][0]['children'].pop()
        with self.assertRaisesRegex(ValueError, 'Unexpected lobe membership'):
            build.membership(self.doc)

    def test_hash_gate_and_bad_chunks(self):
        with self.assertRaisesRegex(ValueError, 'Exact hydrated baseline'):
            build.build(self.old)
        with self.assertRaises(ValueError):
            build.unpack(b'version https://git-lfs.github.com/spec/v1')
        with self.assertRaises(ValueError):
            build.unpack(self.old[:-1])

    def test_v1_retained_and_v2_only_roughness_metadata(self):
        v1 = build.transform(self.doc, 'v1')
        v2 = copy.deepcopy(self.new)
        self.assertEqual(v1['meshes'], v2['meshes'])
        for m in v2['materials'][2:]:
            self.assertEqual(m['pbrMetallicRoughness']['roughnessFactor'], .65)
            m['pbrMetallicRoughness']['roughnessFactor'] = .25
        v2['extras']['lobeTeaching']['revision'] = 'v1'
        self.assertEqual(v1, v2)


if __name__ == '__main__':
    unittest.main()
