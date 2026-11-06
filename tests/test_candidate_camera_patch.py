"""Current incorporated camera source binding; exact-vendor CPU checks are separate."""
from pathlib import Path
import hashlib
import importlib.util
import json
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class CameraSourceTests(unittest.TestCase):
    def test_exact_incorporated_source_and_reset_helper(self):
        current = ROOT / 'gallery/eye-inspection/r01'
        binding = json.loads((current / 'binding.json').read_text())
        self.assertEqual(hashlib.sha256((current / 'candidate.js').read_bytes()).hexdigest(),
                         binding['outputs']['candidate.js'])
        helper = ROOT / 'gallery/candidate-camera/r01/camera-reset.mjs'
        self.assertEqual(hashlib.sha256(helper.read_bytes()).hexdigest(),
                         'dcce015f6b0778337756ceaaa1f64aabed7e5db0137b17b62290e8bc4138be0f')


    def test_changed_current_source_refused_before_vendor_or_execution(self):
        spec = importlib.util.spec_from_file_location(
            'camera_cpu', ROOT / 'tests/candidate_camera/run_cpu.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / 'gallery/eye-inspection/r01'
            current.mkdir(parents=True)
            (current / 'candidate.js').write_bytes(b'changed source')
            (current / 'binding.json').write_bytes(
                (ROOT / 'gallery/eye-inspection/r01/binding.json').read_bytes())
            with patch.object(runner, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Wrong exact candidate source'):
                    runner.run(root / 'absent-vendor')


if __name__ == '__main__':
    unittest.main()
