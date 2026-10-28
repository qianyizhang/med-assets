"""Lean structural/failure checks; actual payload and native import are local gates."""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest

PATH = Path(__file__).resolve().parents[1] / 'tools/eye_teaching/build.py'
spec = importlib.util.spec_from_file_location('eye_teaching_build', PATH)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def fixture():
    doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': list(range(7))}],
           'nodes': [], 'meshes': [], 'materials': [], 'accessors': [], 'bufferViews': [],
           'buffers': [{'byteLength': 84}], 'extras': {'source': 'synthetic'}}
    blob = bytearray()
    for i, name in enumerate(build.KEEP + build.OMIT):
        doc['nodes'].append({'name': name, 'mesh': i, 'translation': [i, 0, 0]})
        doc['meshes'].append({'primitives': [{'indices': i, 'attributes': {'POSITION': i}, 'material': i}]})
        doc['materials'].append({'name': name, 'doubleSided': True})
        doc['accessors'].append({'bufferView': i, 'componentType': 5125, 'count': 3, 'type': 'SCALAR'})
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': 12})
        blob.extend(struct.pack('<III', i, i + 1, i + 2))
    raw = build.pack(doc, bytes(blob))
    out, payload = build.subset(doc, bytes(blob))
    out['extras']['baselineSha256'] = build.sha(raw)
    return raw, out, payload


class EyeTeachingDerivativeTests(unittest.TestCase):
    def test_removes_nodes_and_unused_payload_preserves_selected_data(self):
        raw, out, payload = fixture()
        result = build.validate_pair(raw, build.pack(out, payload))
        self.assertEqual((result['nodes'], len(payload)), (3, 36))
        self.assertEqual([n['name'] for n in out['nodes']], list(build.KEEP))

    def test_changed_position_material_and_transform_rejected(self):
        raw, out, payload = fixture()
        for change in ('payload', 'material', 'transform'):
            altered = copy.deepcopy(out)
            changed_payload = payload
            if change == 'payload':
                changed_payload = bytes([payload[0] ^ 1]) + payload[1:]
            elif change == 'material':
                altered['materials'][0]['doubleSided'] = False
            else:
                altered['nodes'][0]['translation'][0] += 1
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'Retained geometry'):
                build.validate_pair(raw, build.pack(altered, changed_payload))

    def test_hidden_payload_and_extra_node_rejected(self):
        raw, out, payload = fixture()
        altered = copy.deepcopy(out)
        altered['buffers'][0]['byteLength'] += 4
        with self.assertRaisesRegex(ValueError, 'Unreferenced bytes'):
            build.validate_pair(raw, build.pack(altered, payload + b'\0' * 4))
        out['nodes'].append({'name': build.OMIT[0], 'mesh': 0})
        with self.assertRaisesRegex(ValueError, 'exactly three'):
            build.validate_pair(raw, build.pack(out, payload))

    def test_hierarchy_and_unhandled_dependencies_rejected(self):
        raw, _, _ = fixture()
        doc, blob = build.unpack(raw)
        doc['nodes'][0]['children'] = [3]
        with self.assertRaisesRegex(ValueError, 'node dependency'):
            build.subset(doc, blob)
        del doc['nodes'][0]['children']
        doc['animations'] = []
        with self.assertRaisesRegex(ValueError, 'Unsupported dependencies'):
            build.subset(doc, blob)

    def test_wrong_source_and_malformed_glb_rejected(self):
        raw, _, _ = fixture()
        for bad in (b'version https://git-lfs.github.com/spec/v1\n', raw, raw[:-1]):
            with self.assertRaisesRegex(ValueError, 'Exact diagnostic baseline'):
                build.build(bad)
        for bad in (raw[:-1], raw + b'xxxx', b'glTF'):
            with self.assertRaises(ValueError):
                build.unpack(bad)

    def test_missing_scope_and_provenance_rejected(self):
        raw, out, payload = fixture()
        for key in ('scope', 'baselineSha256', 'baselineExtras'):
            altered = copy.deepcopy(out)
            altered['extras'][key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                build.validate_pair(raw, build.pack(altered, payload))


if __name__ == '__main__':
    unittest.main()
