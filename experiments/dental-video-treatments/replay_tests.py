"""Explicit checks for the dental film production and replay sources."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import replay

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]

class DentalVideoTreatments(unittest.TestCase):
    def test_source_identity_and_caption_timing(self):
        replay.check_sources()

    def test_repeat_html_build_matches_retained_hash(self):
        target=replay.manifest()['originalSourceHashes']['hyperframes/index.html']
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);shutil.copy2(PACKAGE/'hyperframes/build_story.py',p/'build_story.py')
                subprocess.run(['python3',str(p/'build_story.py')],check=True,capture_output=True)
                self.assertEqual(replay.digest(p/'index.html'),target)

    def test_dependency_versions(self):
        for engine,key,value in [('hyperframes','hyperframes','0.9.8'),('hyperframes','gsap','3.14.2'),('remotion','remotion','4.0.540'),('remotion','react','19.1.0')]:
            data=json.loads((PACKAGE/engine/'package.json').read_text())
            lock=json.loads((PACKAGE/engine/'package-lock.json').read_text())
            self.assertEqual(data['dependencies'][key],value)
            self.assertEqual(lock['packages']['node_modules/'+key]['version'],value)
        self.assertIn('manimgl==1.7.2',(PACKAGE/'manimgl/requirements.lock.txt').read_text())

    def test_scope_and_reproducibility_not_overclaimed(self):
        data=replay.manifest()
        self.assertEqual(data['reproducibility']['mp4BitwiseReplay'],'not-proven')
        self.assertEqual(data['gates']['clinical']['status'],'unverified')
        self.assertEqual(data['gates']['listening']['status'],'unverified')
        self.assertIn('Not the actual-asset treatment-procedure',data['scope'])
        self.assertEqual(len([r for r in data['artifacts'] if r['file'].endswith('.mp4')]),4)

    def test_prepare_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'never overwritten'):replay.prepare('remotion',Path(tmp))

    def test_prepare_rejects_nested_source_destination(self):
        with self.assertRaisesRegex(ValueError, 'canonical engine source'):
            replay.prepare('hyperframes',PACKAGE/'hyperframes'/'uncreated-new-output')

    def test_prepare_rejects_unknown_engine(self):
        with self.assertRaisesRegex(ValueError,'Unknown renderer'):replay.prepare('not-an-engine',Path('unused'))

    def test_bad_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'results').mkdir();(p/'hyperframes').mkdir()
            (p/'results/manifest.json').write_text(json.dumps({'originalSourceHashes':{'hyperframes/build_story.py':'0'*64}}))
            (p/'hyperframes/build_story.py').write_text('wrong')
            with self.assertRaisesRegex(ValueError,'Source identity mismatch'):replay.check_sources(p)

    def test_no_duplicate_html_or_audio_copies_tracked(self):
        paths=subprocess.check_output(['git','ls-files','--cached','--','experiments/dental-video-treatments'],cwd=ROOT,text=True).splitlines()
        self.assertTrue(paths)
        self.assertEqual([p for p in paths if p.endswith('.wav')],['experiments/dental-video-treatments/audio/final-mix.wav'])
        self.assertFalse(any('/.work/' in p or '/node_modules/' in p or p.endswith('/index.html') for p in paths))

    def test_local_document_links_exist(self):
        for doc in ('README.md','REPLAY.md','SHARED-SCRIPT.md','COMPARISON.md'):
            text=(PACKAGE/doc).read_text()
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if '://' in target or target.startswith('#'):continue
                self.assertTrue((PACKAGE/target.split('#')[0]).exists(),(doc,target))

if __name__=='__main__':unittest.main()
