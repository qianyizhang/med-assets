"""Payload-free refusal tests, not a geometry or anatomical acceptance suite."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'models/fetus/exports/head-face-junction-r01/build.py'


class FetalJunctionGuardTests(unittest.TestCase):
    def invoke(self, source, output, optimized=False):
        return subprocess.run(
            [sys.executable] + (['-O'] if optimized else []) +
            [str(SCRIPT), '--source', str(source), '--output', str(output)],
            capture_output=True, text=True, timeout=15)

    def reject_wrong_source(self, optimized):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, output = root / 'source.glb', root / 'output.glb'
            source.write_bytes(b'not the exact source')
            result = self.invoke(source, output, optimized)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Exact original fetal source SHA256 required', result.stderr)
            self.assertEqual(source.read_bytes(), b'not the exact source')
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix('.build.json').exists())

    def test_wrong_source_no_output(self):
        self.reject_wrong_source(False)

    def test_optimized_python_cannot_disable_source_guard(self):
        self.reject_wrong_source(True)

    def test_existing_candidate_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, output = root / 'absent.glb', root / 'output.glb'
            output.write_bytes(b'preserved candidate')
            result = self.invoke(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Refusing to overwrite', result.stderr)
            self.assertEqual(output.read_bytes(), b'preserved candidate')
            self.assertFalse(output.with_suffix('.build.json').exists())

    def test_existing_receipt_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, output = root / 'absent.glb', root / 'output.glb'
            receipt = output.with_suffix('.build.json')
            receipt.write_bytes(b'preserved receipt')
            result = self.invoke(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Refusing to overwrite', result.stderr)
            self.assertEqual(receipt.read_bytes(), b'preserved receipt')
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
