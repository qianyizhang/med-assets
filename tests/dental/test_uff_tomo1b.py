import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('uff',ROOT/'tools/dental/uff_tomo1b.py');uff=importlib.util.module_from_spec(spec);spec.loader.exec_module(uff)

class TestUFF(unittest.TestCase):
 def test_wrong_source_rejected_before_ingestion(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.zip';f.write_bytes(b'not source')
   with self.assertRaises(ValueError):uff.ingest(f,Path(d))
 def test_singleton_distance_uses_naive_fallback(self):
  m=trimesh.Trimesh([[0,0,0],[1,0,0],[0,1,0]],[[0,1,2]],process=False)
  with patch.object(uff,'covering_points',return_value=(np.array([[.25,.25,1.]]),0.0)),patch.object(uff.pcu,'closest_points_on_mesh',side_effect=AssertionError('unsafe singleton call')):
   self.assertAlmostEqual(uff.deviation(m,m,.01)['sampled_max_mm'],1.0)
 def test_face_component_split_retains_topology(self):
  m=trimesh.util.concatenate([trimesh.creation.box(),trimesh.creation.box().apply_translation([3,0,0])]);parts=uff.split_compact(m)
  self.assertEqual(len(parts),2);self.assertTrue(all(uff.topology(p)['watertight'] for p in parts))
 def test_existing_output_refused_without_changes(self):
  with tempfile.TemporaryDirectory() as d:
   work=Path(d)/'existing';work.mkdir();sentinel=work/'keep.txt';sentinel.write_text('keep')
   with patch.object(uff.sys,'argv',['uff','verify','--model','unused','--work-dir',str(work)]):
    with self.assertRaises(SystemExit):uff.main()
   self.assertEqual(sentinel.read_text(),'keep');self.assertEqual(list(work.iterdir()),[sentinel])
 def test_bad_source_creates_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.zip';f.write_bytes(b'wrong');work=Path(d)/'new'
   with patch.object(uff.sys,'argv',['uff','all','--source-zip',str(f),'--work-dir',str(work)]):
    with self.assertRaises(ValueError):uff.main()
   self.assertFalse(work.exists())
 def test_bad_model_creates_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.glb';f.write_bytes(b'wrong');work=Path(d)/'new'
   with patch.object(uff.sys,'argv',['uff','verify','--model',str(f),'--work-dir',str(work)]):
    with self.assertRaises(ValueError):uff.main()
   self.assertFalse(work.exists())
 def test_pinned_candidate_hash(self):
  f=ROOT/'models/dental_specimens/uff_tomo1b/exports/r01/uff-tomo1b-display.glb'
  self.assertEqual(uff.file_hash(f),uff.DISPLAY_SHA256)

if __name__=='__main__':unittest.main()
