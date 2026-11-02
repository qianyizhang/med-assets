import hashlib, importlib.util, pathlib, tempfile, unittest, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('knee_patch',ROOT/'gallery/knee-inspection/r01/apply.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class KneePatch(unittest.TestCase):
    def test_exact_candidate_output(self):
        raw=(ROOT/'tests/knee_inspection/fixtures/candidate-v44.js').read_bytes()
        self.assertEqual(hashlib.sha256(m.patched(raw)).hexdigest(),m.BINDING['outputs']['candidate.js'])
    def test_wrong_source_refused(self):
        with self.assertRaises(ValueError):m.patched(b'wrong source')
    def test_input_refusal_before_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);(p/'candidate.js').write_bytes(b'wrong source')
            with self.assertRaises(ValueError):m.apply(p)
            self.assertEqual(list(p.iterdir()),[p/'candidate.js'])
            self.assertEqual((p/'candidate.js').read_bytes(),b'wrong source')
    def test_actual_viewer_composition(self):
        subprocess.run([sys.executable,str(ROOT/'tests/knee_inspection/run.py')],check=True,timeout=30)
    def test_module_payload_pin(self):
        self.assertEqual(hashlib.sha256((m.HERE/'knee-inspection.mjs').read_bytes()).hexdigest(),m.BINDING['outputs']['knee-inspection.mjs'])
if __name__=='__main__':unittest.main()
