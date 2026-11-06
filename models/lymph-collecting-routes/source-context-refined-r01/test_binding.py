import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Guards(unittest.TestCase):
 def test_no_optimized_assertions(self):
  r=subprocess.run([sys.executable,'-O',str(ROOT/'check_binding.py')],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertIn(b'optimized Python',r.stderr)
 def test_reject_changed_accepted_plate(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);shutil.copytree(ROOT,p,dirs_exist_ok=True);f=p/'projection-binding.json';b=json.loads(f.read_text());b['input_plate_sha256']['en']='0'*64;f.write_text(json.dumps(b));r=subprocess.run([sys.executable,str(p/'check_binding.py')],capture_output=True);self.assertNotEqual(r.returncode,0)
 def test_reject_changed_projection(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);shutil.copytree(ROOT,p,dirs_exist_ok=True);f=p/'projection.json';b=json.loads(f.read_text());b['views']['overview']['objects']['Thoracic duct — left venous angle']['vertices'][0][0]+=.001;f.write_text(json.dumps(b));r=subprocess.run([sys.executable,str(p/'check_binding.py')],capture_output=True);self.assertNotEqual(r.returncode,0)
 def test_reject_changed_standalone_plate(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);shutil.copytree(ROOT,p,dirs_exist_ok=True);f=p/'comparison-en.png';f.write_bytes(f.read_bytes()+b'x');r=subprocess.run([sys.executable,str(p/'check_binding.py')],capture_output=True);self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
