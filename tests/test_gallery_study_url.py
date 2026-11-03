import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'gallery/study-url/r01'
spec=importlib.util.spec_from_file_location('study_url_apply',P/'apply.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PackageTests(unittest.TestCase):
 def test_payload_and_exact_delta(self):
  for name,expected in m.BINDING['combinedPayload'].items():self.assertEqual(m.digest((m.COMBINED/name).read_bytes()),expected)
  raw=(m.COMBINED/'review.js').read_text()
  self.assertEqual(raw.count(m.OLD),1)
  self.assertEqual(m.digest(raw.replace(m.OLD,m.NEW).encode()),m.BINDING['outputs']['review.js'])
 def test_wrong_source_no_write(self):
  for mode in ('combined','v45'):
   with tempfile.TemporaryDirectory() as td:
    t=Path(td)
    for name in m.BINDING['inputs'][mode]:(t/name).write_text('unknown')
    before={p.name:p.read_bytes() for p in t.iterdir()}
    with self.assertRaises(ValueError):m.apply(t,mode)
    self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_both_modes_and_repeat(self):
  for mode in ('combined','v45'):
   with tempfile.TemporaryDirectory() as td:
    t=Path(td);samples={n:('fixture '+n).encode() for n in m.BINDING['inputs'][mode]}
    binding={**m.BINDING,'inputs':{**m.BINDING['inputs'],mode:{n:m.digest(raw) for n,raw in samples.items()}}}
    for n,raw in samples.items():(t/n).write_bytes(raw)
    with patch.object(m,'BINDING',binding):
     output=m.apply(t,mode)
     self.assertEqual(set(output),{'review.js'} if mode=='combined' else set(binding['outputs']))
     before={p.name:p.read_bytes() for p in t.iterdir()}
     with self.assertRaises(ValueError):m.apply(t,mode)
     self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_bad_output_no_write(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);mode='combined';samples={n:('fixture '+n).encode() for n in m.BINDING['inputs'][mode]}
   binding={**m.BINDING,'inputs':{mode:{n:m.digest(r) for n,r in samples.items()}},'outputs':{**m.BINDING['outputs'],'review.js':'0'*64}}
   for n,raw in samples.items():(t/n).write_bytes(raw)
   before={p.name:p.read_bytes() for p in t.iterdir()}
   with patch.object(m,'BINDING',binding):
    with self.assertRaises(ValueError):m.apply(t,mode)
   self.assertEqual(before,{p.name:p.read_bytes() for p in t.iterdir()})
 def test_no_network_or_content_delta(self):
  self.assertNotIn('fetch(',m.NEW);self.assertNotIn('pushState',m.NEW)
  self.assertLess(m.NEW.index('some('),m.NEW.index('replaceState'))
  self.assertEqual(set(m.BINDING['outputs']),{'review.js','comparison-state.mjs','navigation-focus.mjs'})
if __name__=='__main__':unittest.main()
