"""Required source-bound patch and full-module lifecycle checks; no browser."""
from pathlib import Path
import hashlib
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'gallery/candidate-lifecycle/r01'
spec = importlib.util.spec_from_file_location('lifecycle_apply', PACKAGE / 'apply.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
ORIGINAL = (ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js').read_bytes()


class PatchTests(unittest.TestCase):
    def prepare(self, directory):
        target = Path(directory)
        (target / 'candidate.js').write_bytes(ORIGINAL)
        (target / 'review-data.json').write_bytes(b'unchanged-data\n')
        return target

    def test_original_identity(self):
        self.assertEqual(hashlib.sha256(ORIGINAL).hexdigest(), patch.BASE_SHA)
        self.assertEqual(hashlib.sha256(patch.patched(ORIGINAL)).hexdigest(),
                         'd11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e')
        self.assertEqual(hashlib.sha256((PACKAGE / 'viewer-lifecycle.mjs').read_bytes()).hexdigest(),
                         '2e2b67adb61140feefa64ffae50207258aa507bb555ebe8549c6b7b0989e8969')

    def test_replay_preserves_data_and_native_camera_visibility_code(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            result = patch.apply(target)
            text = (target / 'candidate.js').read_text()
            self.assertEqual(set(result), {'candidate.js', 'viewer-lifecycle.mjs'})
            self.assertEqual((target / 'review-data.json').read_bytes(), b'unchanged-data\n')
            start, end = 'const box=new THREE.Box3()', 'const resize=()=>'
            self.assertEqual(ORIGINAL.decode().split(start)[1].split(end)[0],
                             text.split(start)[1].split(end)[0])
            for needle in ('// Preserve native transforms and default pose. No mixer.',
                           'inspectGLB(bytes)', "credentials:'omit',redirect:'error'",
                           'Source SHA256 mismatch', 'Non-embedded GLB resource blocked'):
                self.assertIn(needle, text)

    def test_wrong_baseline_has_no_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            (target / 'candidate.js').write_bytes(ORIGINAL + b'\n')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaisesRegex(ValueError, 'baseline'):
                patch.apply(target)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_existing_module_has_no_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            (target / 'viewer-lifecycle.mjs').write_bytes(b'existing')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaisesRegex(ValueError, 'already exists'):
                patch.apply(target)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_deterministic_and_repeated_apply_refused(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first, second = self.prepare(first), self.prepare(second)
            self.assertEqual(patch.apply(first), patch.apply(second))
            before = {p.name: p.read_bytes() for p in first.iterdir()}
            with self.assertRaises(ValueError):
                patch.apply(first)
            self.assertEqual(before, {p.name: p.read_bytes() for p in first.iterdir()})

    def run_behavior(self, original=False):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            if not original:
                patch.apply(target)
            env = os.environ.copy()
            env['CANDIDATE_LIFECYCLE_SOURCE'] = str(target / 'candidate.js')
            result = subprocess.run(
                ['node', '--experimental-vm-modules', '--test', '--test-reporter=tap',
                 str(ROOT / 'tests/candidate_lifecycle/lifecycle.test.mjs')],
                env=env, text=True, capture_output=True, timeout=30)
            counts = {key: int(value) for key, value in re.findall(
                r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$',
                result.stdout, re.MULTILINE)}
            self.assertEqual(counts, {
                'tests': 15, 'pass': 3 if original else 15, 'fail': 12 if original else 0,
                'cancelled': 0, 'skipped': 0, 'todo': 0}, result.stdout + result.stderr)
            self.assertEqual(result.returncode, 1 if original else 0,
                             result.stdout + result.stderr)

    def test_canonical_module_exposes_lifecycle_regressions(self):
        self.run_behavior(original=True)

    def test_patched_module_passes_complete_lifecycle_suite(self):
        self.run_behavior()


if __name__ == '__main__':
    unittest.main(verbosity=2)
