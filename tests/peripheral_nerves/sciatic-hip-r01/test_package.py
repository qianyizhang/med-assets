"""Guard source identity, inspect the actual export, and replay the lesson."""
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVIEW = ROOT / 'reviews/peripheral_nerves/2026-10-30-sciatic-hip-r01'
MODEL = ROOT / 'models/peripheral_nerves/exports/sciatic-hip-r01/right-sciatic-hip.glb'
EXPECTED = '72077a97a8a935a7a4623443c1c0fd61ab48a9bf4ad895af058345b7a372abd6'

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

build, compose = load('build'), load('compose')

class RegionalStudy(unittest.TestCase):
    def test_wrong_source_creates_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'wrong.blend'
            source.write_bytes(b'unknown source')
            output = Path(temporary) / 'output'
            with self.assertRaisesRegex(ValueError, 'Exact pinned'):
                build.check_inputs(source, output)
            self.assertFalse(output.exists())

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'output'
            output.mkdir()
            keep = output / 'keep'
            keep.write_bytes(b'preserve')
            with self.assertRaises(FileExistsError):
                build.check_inputs(Path(temporary) / 'missing.blend', output)
            self.assertEqual(keep.read_bytes(), b'preserve')

    def test_actual_export_scope(self):
        data = MODEL.read_bytes()
        self.assertEqual(sha(MODEL), EXPECTED)
        self.assertEqual(len(data), 559144)
        self.assertEqual(struct.unpack_from('<4sII', data), (b'glTF', 2, len(data)))
        size, kind = struct.unpack_from('<II', data, 12)
        self.assertEqual(kind, 0x4e4f534a)
        doc = json.loads(data[20:20+size])
        self.assertEqual({n['extras']['source_object'] for n in doc['nodes']}, set(build.NAMES))
        self.assertEqual(len(doc['nodes']), 4)
        self.assertEqual(sum(doc['accessors'][p['indices']]['count']//3
                             for m in doc['meshes'] for p in m['primitives']), 24154)
        self.assertNotIn('animations', doc)
        self.assertEqual(doc['scenes'][0]['extras']['license'], 'CC BY-SA 4.0')
        self.assertIn('unresolved source nerve-piriformis overlap', doc['scenes'][0]['extras']['scope'])

    def test_bound_evidence_and_explicit_import_limit(self):
        source = json.loads((REVIEW / 'source-check.json').read_text())
        self.assertEqual(source['artifactSha256'], EXPECTED)
        self.assertEqual(source['result'], 'passed-with-explicit-import-limits')
        self.assertEqual({r['sourceObject'] for r in source['objects']}, set(build.NAMES))
        self.assertTrue(all(r['storedSurfaceTrianglesMatch'] and r['maxStoredVertexDifference'] < 1e-6
                            for r in source['objects']))
        self.assertEqual(sum(r['storedGLBTriangles'] for r in source['objects']), 24154)
        self.assertEqual(sum(r['reimportTriangles'] for r in source['objects']), 24153)
        for folder in ('preflight', 'v1'):
            bindings = json.loads((REVIEW / folder / 'bindings.json').read_text())
            for view in bindings['views']:
                self.assertEqual(sha(REVIEW / folder / view['file']), view['sha256'])
        self.assertEqual(bindings['artifactSha256'], EXPECTED)
        self.assertEqual(len(bindings['visibleLabelChecks']), 6)
        self.assertTrue(all(r['passed'] and
                            r['firstVisibleSourceObject'] == bindings['anchors'][r['anchor']]['sourceObject']
                            for r in bindings['visibleLabelChecks']))

    def test_actual_composition_replay(self):
        expected = json.loads((REVIEW / 'v2/composition.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'teaching'
            self.assertEqual(compose.compose(REVIEW / 'v1', output), expected)
            for name, identity in expected['outputs'].items():
                self.assertEqual(sha(output / name), identity)
                self.assertEqual((output / name).read_bytes(), (REVIEW / 'v2' / name).read_bytes())
            with self.assertRaises(FileExistsError):
                compose.compose(REVIEW / 'v1', output)

if __name__ == '__main__':
    unittest.main()
