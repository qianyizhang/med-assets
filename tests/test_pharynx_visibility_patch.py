"""Offline checks for applying the viewer-only patch; no rendering/media download."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'gallery/pharynx_larynx/visibility-r01/apply.py'
spec = importlib.util.spec_from_file_location('pharynx_visibility_patch', TOOL)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
BASELINE = ROOT / 'tests/pharynx_visibility/fixtures/candidate-v40.js'


class PharynxVisibilityPatchTests(unittest.TestCase):
    def fixture(self, directory):
        target = Path(directory)
        (target / 'candidate.js').write_bytes(BASELINE.read_bytes())
        (target / 'review-data.json').write_bytes(b'canonical-data-sentinel\n')
        return target

    def test_baseline_identity(self):
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), patch.BASE_SHA)

    def test_exact_source_patch_preserves_data_and_original_camera_path(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.fixture(directory)
            result = patch.apply(target)
            self.assertEqual(set(result), {'candidate.js', *patch.MODULES})
            text = (target / 'candidate.js').read_text()
            self.assertIn('inspectionUI=mountInspection(record,model.scene,wrap,{fitVisible:()=>fitVisibleParts(model.scene,camera,controls,THREE)});', text)
            self.assertIn('function paint(){inspectionUI?.paint(lang);', text)
            self.assertIn("document.querySelector('.pharynx-inspection')?.remove()", text)
            self.assertIn('camera.position.copy(center).add(new THREE.Vector3', text)
            self.assertEqual((target / 'review-data.json').read_bytes(), b'canonical-data-sentinel\n')

    def test_wrong_baseline_fails_without_any_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.fixture(directory)
            path = target / 'candidate.js'; path.write_bytes(path.read_bytes() + b'\n')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaisesRegex(ValueError, 'baseline'):
                patch.apply(target)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)

    def test_existing_module_fails_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.fixture(directory)
            (target / patch.MODULES[0]).write_bytes(b'existing\n')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaisesRegex(ValueError, 'already exist'):
                patch.apply(target)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)

    def test_replay_is_identical_and_double_application_fails(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one, two = self.fixture(first), self.fixture(second)
            self.assertEqual(patch.apply(one), patch.apply(two))
            before = {p.name: p.read_bytes() for p in one.iterdir()}
            with self.assertRaises(ValueError):
                patch.apply(one)
            self.assertEqual({p.name: p.read_bytes() for p in one.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
