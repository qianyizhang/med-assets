"""Required context-loss source/actual-module tests; no browser or unmerged code."""
from pathlib import Path
import hashlib
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = (ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js').read_bytes()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context = load(ROOT / 'gallery/candidate-context/r01/apply.py', 'context_patch')
lifecycle = load(ROOT / 'gallery/candidate-lifecycle/r01/apply.py', 'lifecycle_patch')


class ContextPatchTests(unittest.TestCase):
    def prepare(self, directory, with_lifecycle=True):
        target = Path(directory)
        (target / 'candidate.js').write_bytes(ORIGINAL)
        (target / 'review-data.json').write_bytes(b'unchanged-records\n')
        if with_lifecycle:
            lifecycle.apply(target)
        return target

    def test_exact_existing_lifecycle_and_unchanged_camera_body(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            raw = (target / 'candidate.js').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), context.LIFECYCLE_SOURCE)
            updated = context.patched(raw).decode()
            start, end = 'let direction=framing?', ';const resize=()=>'
            self.assertEqual(raw.decode().split(start)[1].split(end)[0],
                             updated.split(start)[1].split(end)[0])

    def test_apply_preserves_records_and_exact_lifecycle_module(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            prior = (target / 'viewer-lifecycle.mjs').read_bytes()
            result = context.apply(target)
            self.assertEqual(set(result), {'candidate.js', 'context-loss.mjs'})
            self.assertEqual((target / 'viewer-lifecycle.mjs').read_bytes(), prior)
            self.assertEqual((target / 'review-data.json').read_bytes(), b'unchanged-records\n')

    def assert_refused_without_writes(self, target):
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        with self.assertRaises(ValueError):
            context.apply(target)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_unpatched_canonical_requires_explicit_lifecycle_first(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_refused_without_writes(self.prepare(directory, with_lifecycle=False))

    def test_wrong_source_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            path = target / 'candidate.js'
            path.write_bytes(path.read_bytes() + b'\n')
            self.assert_refused_without_writes(target)

    def test_missing_or_changed_dependency_rejected_without_writes(self):
        for changed in (None, b'changed'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                target = self.prepare(directory)
                dependency = target / 'viewer-lifecycle.mjs'
                dependency.unlink()
                if changed is not None:
                    dependency.write_bytes(changed)
                self.assert_refused_without_writes(target)

    def test_existing_module_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            (target / 'context-loss.mjs').write_bytes(b'existing')
            self.assert_refused_without_writes(target)

    def test_deterministic_and_repeat_application_refused(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first, second = self.prepare(first), self.prepare(second)
            self.assertEqual(context.apply(first), context.apply(second))
            self.assert_refused_without_writes(first)

    def run_module(self, mode, suite, expected):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory, with_lifecycle=mode != 'canonical')
            if mode == 'updated':
                context.apply(target)
            env = os.environ.copy()
            env['CANDIDATE_LIFECYCLE_SOURCE'] = str(target / 'candidate.js')
            # Default tests must not rely on an optional, unmerged camera package.
            env.pop('CANDIDATE_CAMERA_MODULE', None)
            result = subprocess.run(
                ['node', '--experimental-vm-modules', '--test', '--test-reporter=tap',
                 str(ROOT / suite)], env=env, text=True, capture_output=True, timeout=30)
            counts = {key: int(value) for key, value in re.findall(
                r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$',
                result.stdout, re.MULTILINE)}
            total, passed, failed = expected
            self.assertEqual(counts, {'tests': total, 'pass': passed, 'fail': failed,
                                     'cancelled': 0, 'skipped': 0, 'todo': 0},
                             result.stdout + result.stderr)
            self.assertEqual(result.returncode, 1 if failed else 0, result.stdout + result.stderr)

    def test_canonical_module_exposes_context_regressions(self):
        self.run_module('canonical', 'tests/candidate_context/context.test.mjs', (14, 2, 12))

    def test_existing_lifecycle_module_exposes_context_regressions(self):
        self.run_module('lifecycle', 'tests/candidate_context/context.test.mjs', (14, 4, 10))

    def test_updated_actual_module_passes_context_suite(self):
        self.run_module('updated', 'tests/candidate_context/context.test.mjs', (14, 14, 0))

    def test_updated_actual_module_preserves_existing_lifecycle_suite(self):
        self.run_module('updated', 'tests/candidate_lifecycle/lifecycle.test.mjs', (15, 15, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
