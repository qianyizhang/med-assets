"""Scoped guards, real artifact bindings and deterministic teaching replay."""
import hashlib, importlib.util, json, struct, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
R=ROOT/'reviews/peripheral_nerves/2026-10-30-median-wrist-r01'
M=ROOT/'models/peripheral_nerves/exports/median-wrist-r01/right-median-wrist.glb'
EXPECTED='6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50'
def load(name):
    s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
build=load('build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class RegionalPackage(unittest.TestCase):
    def test_source_selection_boundary(self):
        self.assertEqual(len(set(build.NAMES)),33)
        self.assertEqual(len(build.NERVES),3)
        self.assertEqual(len(build.CARPALS),8)
        self.assertEqual(len(build.PHALANGES),14)
        self.assertTrue(all(n.endswith('.r') for n in build.NAMES))
        self.assertFalse(any('retinaculum' in n.lower() or 'flexor' in n.lower() or 'Palmar branch' in n for n in build.NAMES))

    def test_wrong_source_creates_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'wrong.blend';src.write_bytes(b'unknown source');out=Path(t)/'out'
            with self.assertRaisesRegex(ValueError,'Exact pinned'):build.check_inputs(src,out)
            self.assertFalse(out.exists())

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';out.mkdir();keep=out/'keep';keep.write_bytes(b'preserve')
            with self.assertRaises(FileExistsError):build.check_inputs(Path(t)/'missing.blend',out)
            self.assertEqual(keep.read_bytes(),b'preserve')

    def test_exact_retained_export_and_source_receipt(self):
        self.assertEqual(sha(M),EXPECTED)
        data=M.read_bytes();self.assertEqual(struct.unpack_from('<4sII',data),(b'glTF',2,len(data)))
        size,kind=struct.unpack_from('<II',data,12);self.assertEqual(kind,0x4e4f534a)
        doc=json.loads(data[20:20+size]);self.assertEqual({n['extras']['source_object'] for n in doc['nodes']},set(build.NAMES))
        self.assertNotIn('animations',doc)
        self.assertIn('carpal-tunnel teaching',doc['scenes'][0]['extras']['scope'])
        receipt=json.loads((R/'v1/source-reimport-check.json').read_text())
        self.assertEqual(receipt['artifactSha256'],EXPECTED)
        self.assertEqual(receipt['result'],'passed');self.assertEqual(len(receipt['objects']),33)
        self.assertEqual(sum(x['triangles'] for x in receipt['objects']),38414)
        self.assertTrue(all(x['surfaceTrianglesMatch'] and x['maxBidirectionalVertexDifference']<1e-6 for x in receipt['objects']))

    def test_capture_reuse_and_visible_targets(self):
        captures=json.loads((R/'v2-captures/bindings.json').read_text())
        self.assertEqual(captures['artifactSha256'],EXPECTED)
        for view in captures['views']:
            self.assertEqual(sha(R/'v2-captures'/view['file']),view['sha256'])
        loc=json.loads((R/'v2/locator-check.json').read_text())
        self.assertTrue(loc['passed']);self.assertEqual(len(loc['checks']),6)
        self.assertTrue(all(x['passed'] and x['boundSourceObject']==x['firstVisibleSourceObject'] for x in loc['checks']))

    def test_actual_composition_replay_and_refusal(self):
        compose=load('compose')
        expected=json.loads((R/'v2/composition-bindings.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'teaching';actual=compose.compose(R/'v2-captures',out)
            self.assertEqual(actual,expected)
            for name,h in expected['outputs'].items():
                self.assertEqual(sha(out/name),h);self.assertEqual((out/name).read_bytes(),(R/'v2'/name).read_bytes())
            with self.assertRaises(FileExistsError):compose.compose(R/'v2-captures',out)

if __name__=='__main__':unittest.main()
