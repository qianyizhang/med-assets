"""Keep the streaming migration's Node boundary tests in the required offline gate."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UploadBoundaryTests(unittest.TestCase):
    def test_actual_uploader_boundaries(self):
        result = subprocess.run(['node', '--test', '--test-reporter=tap',
                                 str(ROOT/'tests/r2_upload.test.mjs')],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('# tests 6', result.stdout)
        self.assertIn('# fail 0', result.stdout)
