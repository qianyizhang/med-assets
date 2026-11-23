"""Check the retained dental film package and its caption and credit records."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path('experiments/dental-video-treatments')
sys.path.insert(0, str(ROOT / 'lib'))
from med_assets.artifacts import parse_pointer, repo_file, source_path

spec = importlib.util.spec_from_file_location('dental_video_replay', ROOT / PACKAGE / 'replay.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class DentalFilmArchive(unittest.TestCase):
    def test_archive_identities(self):
        manifest = json.loads((ROOT / PACKAGE / 'results/manifest.json').read_bytes())
        seen = set()
        for artifact in manifest['artifacts']:
            name = source_path(artifact['file'])
            with self.subTest(artifact=name):
                self.assertNotIn(name, seen)
                seen.add(name)
                path = replay.asset_file(ROOT / PACKAGE, name).relative_to(ROOT)
                attr = subprocess.check_output(['git', 'check-attr', 'filter', '--', path], cwd=ROOT, text=True)
                self.assertEqual(attr.strip(), f'{path}: filter: lfs')
                pointer = subprocess.check_output(['git', 'show', f':{path}'], cwd=ROOT)
                self.assertGreater(artifact['bytes'], 0)
                self.assertEqual(parse_pointer(pointer), (artifact['sha256'], artifact['bytes']))

        self.assertEqual(seen, {
            'results/hyperframes.mp4', 'results/remotion.mp4', 'results/manimgl.mp4', 'results/comparison.mp4',
            'results/storyboard.jpg', 'audio/final-mix.wav', 'fonts/DejaVuSans.ttf', 'fonts/DejaVuSans-Bold.ttf',
        })
        records = manifest['archiveTextSha256']
        self.assertEqual(set(records), {
            str(PACKAGE / 'audio/narration.srt'), str(PACKAGE / 'README.md'),
            str(PACKAGE / 'audio/README.md'), 'sources/fonts/dejavu/LICENSE.txt',
        })
        for name, expected in records.items():
            with self.subTest(record=name):
                self.assertEqual(hashlib.sha256(repo_file(ROOT, name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
