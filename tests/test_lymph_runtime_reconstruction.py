"""Offline boundary checks; no browser, network, or candidate staging."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ci'))
spec=importlib.util.spec_from_file_location('glb_runtime_probe',ROOT/'ci/glb_runtime_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
sys.path.pop(0)

class RuntimeReconstructionTests(unittest.TestCase):
 def test_generated_size_and_hash_fail_closed(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'candidate';path.write_bytes(b'abc')
   digest=hashlib.sha256(b'abc').hexdigest()
   self.assertEqual(probe.verify_generated(path,3,digest)['sha256'],digest)
   for size,sha in ((2,digest),(3,'0'*64),(16*1024*1024+1,digest)):
    with self.assertRaises(ValueError):probe.verify_generated(path,size,sha)
   path.unlink()
   with self.assertRaises(ValueError):probe.verify_generated(path,3,digest)

 def test_pins_bind_exact_recipe_and_distinct_retained_identity(self):
  fixture=json.loads((ROOT/'ci/glb-runtime-fixture.json').read_text())
  decision=json.loads((ROOT/'reviews/lymph_node/2026-10-27-editorial-window-r03/decision.json').read_text())
  candidate=fixture['lymphCandidate'];source=next(x for x in fixture['resources'] if x.get('id')=='lymph')
  self.assertEqual(source['sha256'],decision['source']['sha256'])
  self.assertEqual(candidate['intermediateSha256'],decision['candidateR03']['sha256'])
  self.assertEqual(candidate['intermediateBytes'],decision['candidateR03']['bytes'])
  self.assertEqual(candidate['sha256'],'f89e989450e6f5f64a9d939d135ad0ec17c22e86eee6d9977d46dd68ca542f83')
  self.assertEqual(candidate['retainedComparisonSha256'],'882d146ce2b04547e1f45704a414d5d0a059fef7bff980fe7b932148be24314e')
  self.assertNotEqual(candidate['sha256'],candidate['retainedComparisonSha256'])
  self.assertNotIn('url',candidate)
  self.assertEqual(probe.MAX_DOWNLOAD,10*1024*1024)
  self.assertTrue(all(0<x['bytes']<=probe.MAX_DOWNLOAD for x in fixture['resources']))

 def test_actions_gate_is_required_before_browser_or_download(self):
  with tempfile.TemporaryDirectory() as directory, mock.patch.object(probe,'OUT',Path(directory)), mock.patch.object(probe.os,'geteuid',return_value=1000), mock.patch.dict(probe.os.environ,{'GITHUB_ACTIONS':'false'}):
   with self.assertRaisesRegex(RuntimeError,'Authorized GitHub Actions job only'):probe.main()

 def test_pixel_difference_detects_normal_or_facing_changes(self):
  a=bytes([0,0,0,255]*128);b=bytes([20,0,0,255]*128)
  self.assertEqual(probe.changed(a,a),0)
  self.assertEqual(probe.changed(a,b),128)

if __name__=='__main__':unittest.main()
