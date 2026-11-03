import importlib.util,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]/'gallery/elbow-legend/r01'
s=importlib.util.spec_from_file_location('legend',P/'apply.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_payload(self):
  for n,h in m.BINDING['outputs'].items():self.assertEqual(m.digest((P/n).read_bytes()),h)
 def test_wrong_source_no_write(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td)
   for n in m.BINDING['inputs']:(t/n).write_text('unknown')
   before={p.name:p.read_bytes() for p in t.iterdir()}
   with self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_success_repeat_and_corruption(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);samples={n:('fixture '+n).encode() for n in m.BINDING['inputs']}
   b={**m.BINDING,'inputs':{n:m.digest(r) for n,r in samples.items()}}
   for n,r in samples.items():(t/n).write_bytes(r)
   with patch.object(m,'BINDING',b):
    self.assertEqual(m.apply(t),b['outputs']);before={p.name:p.read_bytes() for p in t.iterdir()}
    with self.assertRaises(ValueError):m.apply(t)
    self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
   for n,r in samples.items():(t/n).write_bytes(r)
   before={p.name:p.read_bytes() for p in t.iterdir()}
   with patch.object(m,'BINDING',{**b,'outputs':{'evidence-view.mjs':'0'*64}}):
    with self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_source_proof_binding(self):
  proof=json.loads((P/'source-proof.json').read_text())
  self.assertEqual(proof['artifactSHA256'],'cd6cd488943fe721101955322b343a8c9441f1d4ff8c5042dd4e1ca7462f7891')
  self.assertEqual(proof['contactEvidence']['imageSHA256'],'5d98b09ffac33ed679ec9087d7dc8da52bbffaf98efcbdc81d2c4a79962d227d')
  selected=[n for n in proof['nodes'] if n['materialIndices']==[1]]
  self.assertEqual(len(selected),1)
  self.assertEqual(selected[0]['extras']['source_object_name'],'Articular capsule of elbow joint.r')
  self.assertEqual(proof['materials'][1]['name'],'Capsule | illustrative transparency')
 def test_bounded_contract(self):
  self.assertEqual(set(m.BINDING['outputs']),{'evidence-view.mjs'})
  source=(P/'evidence-view.mjs').read_text()
  for identity in ['joints__z-elbow-r01__scoped-review__5','5d98b09ffac33ed679ec9087d7dc8da52bbffaf98efcbdc81d2c4a79962d227d','cd6cd488943fe721101955322b343a8c9441f1d4ff8c5042dd4e1ca7462f7891']:self.assertIn(identity,source)
  self.assertNotIn('fetch(',source)
if __name__=='__main__':unittest.main()
