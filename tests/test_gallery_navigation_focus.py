import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'gallery/navigation-focus/r01'
spec=importlib.util.spec_from_file_location('navigation_focus_apply',P/'apply.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PackageTests(unittest.TestCase):
 def test_payload_hashes(self):
  for name,expected in m.BINDING['outputs'].items():
   self.assertEqual(m.digest((P/name).read_bytes()),expected)
 def test_wrong_source_fails_without_write(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td)
   for name in m.BINDING['inputs']:(t/name).write_text('unknown source')
   before={p.name:p.read_bytes() for p in t.iterdir()}
   with self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_success_repeat_and_tampered_output(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td)
   samples={name:('fixture '+name).encode() for name in m.BINDING['inputs']}
   binding={**m.BINDING,'inputs':{name:m.digest(raw) for name,raw in samples.items()}}
   for name,raw in samples.items():(t/name).write_bytes(raw)
   with patch.object(m,'BINDING',binding):
    outputs=m.apply(t)
    self.assertEqual(outputs,binding['outputs'])
    before={p.name:p.read_bytes() for p in t.iterdir()}
    with self.assertRaises(ValueError):m.apply(t)
    self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
   (t/'navigation-focus.mjs').unlink()
   for name,raw in samples.items():(t/name).write_bytes(raw)
   bad={**binding,'outputs':{**binding['outputs'],'navigation-focus.mjs':'0'*64}}
   before={p.name:p.read_bytes() for p in t.iterdir()}
   with patch.object(m,'BINDING',bad):
    with self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_contract(self):
  source=(P/'navigation-focus.mjs').read_text()
  self.assertNotIn('localStorage',source);self.assertNotIn('sessionStorage',source)
  self.assertNotIn('fetch(',source)
  self.assertEqual(set(m.BINDING['outputs']),{'review.js','navigation-focus.mjs'})
if __name__=='__main__':unittest.main()
