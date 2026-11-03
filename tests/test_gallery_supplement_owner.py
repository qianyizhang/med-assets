import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]/'gallery/supplement-owner/r01'
s=importlib.util.spec_from_file_location('routing',P/'apply.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def samples(self,t):
  raw={n:(('prefix '+m.OLD+' suffix') if n=='review.js' else n).encode() for n in m.BINDING['inputs']}
  for n,v in raw.items():(t/n).write_bytes(v)
  b={**m.BINDING,'inputs':{n:m.digest(v) for n,v in raw.items()},'output':m.digest(raw['review.js'].replace(m.OLD.encode(),m.NEW.encode()))}
  return raw,b
 def test_success_and_repeat_refusal(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);raw,b=self.samples(t)
   with patch.object(m,'BINDING',b):
    self.assertEqual(m.apply(t),{'review.js':b['output']});self.assertEqual((t/'review.js').read_bytes(),raw['review.js'].replace(m.OLD.encode(),m.NEW.encode()))
    for n in raw.keys()-{'review.js'}:self.assertEqual((t/n).read_bytes(),raw[n])
    with self.assertRaises(ValueError):m.apply(t)
 def test_wrong_input_no_write(self):
  for name in m.BINDING['inputs']:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
    t=Path(td);raw,b=self.samples(t);(t/name).write_bytes(b'wrong');before={n:(t/n).read_bytes() for n in raw}
    with patch.object(m,'BINDING',b),self.assertRaises(ValueError):m.apply(t)
    self.assertEqual(before,{n:(t/n).read_bytes() for n in raw})
 def test_wrong_output_no_write(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);raw,b=self.samples(t);b['output']='0'*64
   with patch.object(m,'BINDING',b),self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(raw,{n:(t/n).read_bytes() for n in raw})
 def test_nonunique_link_no_write(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);raw,b=self.samples(t);raw['review.js']+=m.OLD.encode();(t/'review.js').write_bytes(raw['review.js']);b['inputs']['review.js']=m.digest(raw['review.js'])
   with patch.object(m,'BINDING',b),self.assertRaises(ValueError):m.apply(t)
   self.assertEqual(raw,{n:(t/n).read_bytes() for n in raw})
if __name__=='__main__':unittest.main()
