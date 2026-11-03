"""Media-free state/build checks; real-source CPU evidence is a separate command."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'tools/dental/layer-controls'
spec = importlib.util.spec_from_file_location('dental_control_build', PACKAGE / 'build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DentalControlTests(unittest.TestCase):
    def test_complete_media_free_controller_suite(self):
        env = dict(os.environ)
        env.pop('DENTAL_SOURCE', None)
        result = subprocess.run(['node', '--test', '--test-reporter=tap', str(PACKAGE / 'controller.test.cjs')], env=env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in ['# tests 15', '# pass 15', '# fail 0', '# skipped 0', '# cancelled 0', '# todo 0']:
            self.assertIn(line + '\n', result.stdout)

    def test_javascript_parses(self):
        for filename in ['controller.js', 'renderer.js', 'app.js', 'app.test.cjs', 'render_preview.cjs']:
            subprocess.run(['node', '--check', str(PACKAGE / filename)], check=True, capture_output=True)

    def test_build_rejects_wrong_source_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, out = Path(directory) / 'source.glb', Path(directory) / 'out.html'
            source.write_bytes(b'version https://git-lfs.github.com/spec/v1\n')
            with self.assertRaises(ValueError):
                builder.build(source, out)
            self.assertFalse(out.exists())

    def test_build_embeds_exact_scripts_and_bytes_deterministically(self):
        fixture = b'build-only-fixture-not-a-model'
        with tempfile.TemporaryDirectory() as directory, patch.object(builder, 'EXPECTED', hashlib.sha256(fixture).hexdigest()):
            source, a, b = [Path(directory) / name for name in ['source.glb', 'a.html', 'b.html']]
            source.write_bytes(fixture)
            builder.build(source, a)
            builder.build(source, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            text = a.read_text()
            for script in ['controller.js', 'renderer.js', 'app.js']:
                self.assertIn((PACKAGE / script).read_text(), text)
            self.assertIn(base64.b64encode(fixture).decode(), text)
            self.assertNotIn('BASE64_DATA', text)
            self.assertNotIn('/* CONTROLLER */', text)
            self.assertNotIn('<script src=', text)

    def test_canonical_pointer_identity(self):
        source = ROOT / 'models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb'
        data = source.read_bytes()
        if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            self.assertIn(('oid sha256:' + builder.EXPECTED + '\n').encode(), data)
            self.assertIn(b'size 2052220\n', data)
        else:
            self.assertEqual(hashlib.sha256(data).hexdigest(), builder.EXPECTED)
            self.assertEqual(len(data), 2052220)

    def test_retained_evidence_matches_source_and_artifacts(self):
        receipt = json.loads((PACKAGE / 'review.json').read_text())
        self.assertEqual(receipt['source']['sha256'], builder.EXPECTED)
        self.assertEqual(receipt['runtime']['status'], 'unverified')
        self.assertFalse(receipt['clinicalValidation'])
        for path, digest in receipt['files'].items():
            self.assertEqual(hashlib.sha256((PACKAGE / path).read_bytes()).hexdigest(), digest, path)
        frames = json.loads((PACKAGE / 'preview-frames.json').read_text())
        self.assertTrue(frames['resetPixelsExact'])
        self.assertEqual(len(frames['records']), 20)
        self.assertEqual(frames['records'][0]['state'], frames['records'][-1]['state'])


if __name__ == '__main__':
    unittest.main()
