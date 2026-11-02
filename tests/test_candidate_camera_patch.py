"""Source-guard/composition checks; actual-vendor CPU scope is run separately."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = (ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js').read_bytes()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


camera = load(ROOT / 'gallery/candidate-camera/r01/apply.py', 'camera_patch')
lifecycle = load(ROOT / 'gallery/candidate-lifecycle/r01/apply.py', 'lifecycle_patch')


class CameraPatchTests(unittest.TestCase):
    def prepare(self, directory):
        target = Path(directory)
        (target / 'candidate.js').write_bytes(ORIGINAL)
        (target / 'review-data.json').write_bytes(b'unchanged-records\n')
        return target

    def test_exact_canonical_identity_and_only_two_pose_anchors(self):
        self.assertIn(hashlib.sha256(ORIGINAL).hexdigest(), camera.SOURCE_HASHES)
        updated = camera.patched(ORIGINAL).decode()
        prefix = "import {clearPendingOrbit} from './camera-reset.mjs';\n"
        restored = updated.removeprefix(prefix).replace('clearPendingOrbit(controls);', '')
        self.assertEqual(updated.count('clearPendingOrbit(controls);'), 2)
        self.assertEqual(restored.encode(), ORIGINAL)

    def test_apply_retains_records_and_deterministic_output(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a, b = self.prepare(first), self.prepare(second)
            self.assertEqual(camera.apply(a), camera.apply(b))
            self.assertEqual((a / 'review-data.json').read_bytes(), b'unchanged-records\n')
            self.assertEqual(set(p.name for p in a.iterdir()),
                             {'candidate.js', 'camera-reset.mjs', 'review-data.json'})

    def test_lifecycle_composition_preserves_exact_existing_module(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            lifecycle.apply(target)
            original_module = (target / 'viewer-lifecycle.mjs').read_bytes()
            original_source = (target / 'candidate.js').read_bytes()
            camera.apply(target)
            self.assertEqual((target / 'viewer-lifecycle.mjs').read_bytes(), original_module)
            text = (target / 'candidate.js').read_text()
            text = text.removeprefix("import {clearPendingOrbit} from './camera-reset.mjs';\n")
            self.assertEqual(text.replace('clearPendingOrbit(controls);', '').encode(), original_source)

    def test_wrong_source_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            (target / 'candidate.js').write_bytes(ORIGINAL + b'\n')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaises(ValueError):
                camera.apply(target)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_existing_reset_module_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            (target / 'camera-reset.mjs').write_bytes(b'existing')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaises(ValueError):
                camera.apply(target)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_missing_or_changed_lifecycle_module_rejected_without_writes(self):
        for changed in (None, b'changed'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                target = self.prepare(directory)
                lifecycle.apply(target)
                dependency = target / 'viewer-lifecycle.mjs'
                dependency.unlink()
                if changed is not None:
                    dependency.write_bytes(changed)
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                with self.assertRaisesRegex(ValueError, 'Exact lifecycle'):
                    camera.apply(target)
                self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_repeated_application_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.prepare(directory)
            camera.apply(target)
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaises(ValueError):
                camera.apply(target)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})


if __name__ == '__main__':
    unittest.main(verbosity=2)
