import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'reviews/spleen/source-locator-r01'
spec = importlib.util.spec_from_file_location('spleen_source_guard', P/'source_guard.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def fixture(labels=None):
    data={'nodes':[{'mesh':i,'extras':{'label':name,'ontologyid':oid}} for i,(name,oid) in enumerate(labels or g.LABELS)]}
    raw=json.dumps(data).encode();raw+=b' '*(-len(raw)%4)
    return b'glTF'+struct.pack('<IIII',2,len(raw)+20,len(raw),0x4E4F534A)+raw

class SourceLocatorTests(unittest.TestCase):
    def test_wrong_source_refused(self):
        with self.assertRaises(ValueError): g.verify_source(b'not the approved GLB')
    def test_source_annotation_contract(self):
        b=fixture();self.assertEqual(len(g.verify_source(b,hashlib.sha256(b).hexdigest())['nodes']),5)
        b=fixture(g.LABELS[:-1]);
        with self.assertRaises(ValueError):g.verify_source(b,hashlib.sha256(b).hexdigest())
    def test_camera_exact_pin(self):
        g.verify_camera((P/'camera-source.json').read_bytes())
        with self.assertRaises(ValueError):g.verify_camera(b'{}')
    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):g.require_new_output(d)
            g.require_new_output(Path(d)/'new')
    def test_derived_view_and_visible_anchors(self):
        r=json.loads((P/'render-receipt.json').read_text());self.assertNotIn('source_evidence_sha256',r['views'][1]);self.assertIn('derivedFrom',r['views'][1])
        rows=json.loads((P/'anchors.json').read_text());self.assertEqual({x['number'] for row in rows for x in row if x['marked']},set(range(1,6)))
        for row in rows:
            for x in row:self.assertEqual(x['marked'],x['interiorRadius']>=15)
