import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import balanced_drive_fallback as b
class Safety(unittest.TestCase):
 def test_urls(self):
  self.assertTrue(b.allowed(b.URL))
  self.assertTrue(b.allowed('https://drive.usercontent.google.com/download?id='+b.ID+'&export=download'))
  for url in [b.URL+'&confirm=t', b.URL.replace('https:','http:'),b.URL.replace(b.ID,'other'),b.URL.replace('drive.google.com','evil.test'),b.URL+'#fragment']:
   self.assertFalse(b.allowed(url))
 def test_bad_zip(self):
  with self.assertRaises(b.lfs.Stop):b.decode(b'<html>confirm download</html>')
 def test_pr_cannot_upload(self):
  with self.assertRaises(b.lfs.Stop):b.guard(pathlib.Path('.'),{'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':b.lfs.REPOSITORY,'GITHUB_EVENT_NAME':'pull_request','GITHUB_REF':'refs/heads/main'})
 def test_missing_confirmation(self):
  with self.assertRaises(b.lfs.Stop):b.guard(pathlib.Path('.'),{'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':b.lfs.REPOSITORY,'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_REF':'refs/heads/main'})
 def test_wrong_bytes_cannot_reach_remote(self):
  with patch.object(b.lfs,'batch') as batch:
   with self.assertRaises(b.lfs.Stop):b.transfer(pathlib.Path('.'),b'wrong',pathlib.Path('.'))
   batch.assert_not_called()
 def test_bad_redirect(self):
  with self.assertRaises(b.lfs.Stop):b.FixedRedirect().redirect_request(None,None,303,'',{},'https://evil.test/')
if __name__=='__main__':unittest.main()
