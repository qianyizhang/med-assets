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
    def test_changed_current_source_refused_before_vendor_or_execution(self):
        spec = importlib.util.spec_from_file_location(
            'camera_cpu', ROOT / 'tests/candidate_camera/run_cpu.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / 'tests/viewer'
            current.mkdir(parents=True)
            (current / 'candidate.js').write_bytes(b'changed source')
            (current / 'source.json').write_bytes(
                (ROOT / 'tests/viewer/source.json').read_bytes())
            with patch.object(runner, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Wrong exact candidate source'):
                    runner.run(root / 'absent-vendor')


if __name__ == '__main__':
    unittest.main()
