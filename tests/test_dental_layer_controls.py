"""Media-free state/build checks; real-source CPU evidence is a separate command."""
import base64
import hashlib
from html.parser import HTMLParser
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

    def test_generic_named_controller_suite(self):
        result = subprocess.run(['node', '--test', '--test-reporter=tap', str(PACKAGE / 'named-controller.test.cjs')], text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in ['# tests 6', '# pass 6', '# fail 0', '# skipped 0', '# cancelled 0', '# todo 0']:
            self.assertIn(line + '\n', result.stdout)

    def test_timeline_controller_suite(self):
        env = dict(os.environ)
        env.pop('DENTAL_SOURCE', None)
        result = subprocess.run(['node', '--test', '--test-reporter=tap', str(PACKAGE / 'timeline.test.cjs')], env=env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in ['# tests 8', '# pass 8', '# fail 0', '# skipped 0', '# cancelled 0', '# todo 0']:
            self.assertIn(line + '\n', result.stdout)

    def test_authoring_script_suite(self):
        result = subprocess.run(['node', '--test', '--test-reporter=tap', str(PACKAGE / 'authoring.test.cjs')], text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in ['# tests 9', '# pass 9', '# fail 0', '# skipped 0', '# cancelled 0', '# todo 0']:
            self.assertIn(line + '\n', result.stdout)

    def test_javascript_parses(self):
        for filename in ['controller.js', 'renderer.js', 'app.js', 'app.test.cjs', 'render_preview.cjs', 'bp3d-source.cjs', 'bp3d-source.test.cjs', 'named-controller.test.cjs', 'timeline.test.cjs', 'authoring.js', 'authoring.test.cjs', 'script.cjs', 'app-harness.cjs', 'render_presentation.cjs']:
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
            for script in ['controller.js', 'renderer.js', 'app.js', 'authoring.js']:
                self.assertIn((PACKAGE / script).read_text(), text)
            self.assertIn(base64.b64encode(fixture).decode(), text)
            self.assertNotIn('BASE64_DATA', text)
            self.assertNotIn('SCRIPT_BASE64', text)
            self.assertNotIn('/* CONTROLLER */', text)
            self.assertNotIn('<script src=', text)

    def test_timeline_markup_has_native_named_controls_and_absolute_range(self):
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = {}
                self.labels = set()
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'id' in attrs:
                    self.tags[attrs['id']] = (tag, attrs)
                if tag == 'label':
                    self.labels.add(attrs.get('for'))
        parsed = Tags()
        parsed.feed((PACKAGE / 'index.template.html').read_text())
        for name in ['play', 'pause', 'reset']:
            self.assertEqual(parsed.tags[name][0], 'button')
        tag, attrs = parsed.tags['timeline']
        self.assertEqual(tag, 'input')
        self.assertEqual(attrs['type'], 'range')
        self.assertEqual((attrs['min'], attrs['max'], attrs['step']), ('0', '8000', '10'))
        self.assertIn('timeline', parsed.labels)
        self.assertIn(attrs['aria-describedby'], parsed.tags)
        self.assertEqual(parsed.tags['playback-status'][1]['role'], 'status')
        self.assertEqual(parsed.tags['time'][1]['aria-live'], 'off')
        self.assertEqual(parsed.tags['amount'][1]['aria-live'], 'off')

    def test_presentation_inputs_are_named_and_bounded(self):
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__()
                self.inputs = {}
                self.labels = set()
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'input':
                    self.inputs[attrs['id']] = attrs
                if tag == 'label':
                    self.labels.add(attrs.get('for'))
        tags = Tags()
        tags.feed((PACKAGE / 'index.template.html').read_text())
        names = ['camera-yaw', 'camera-pitch', 'camera-zoom', 'target-0', 'target-1', 'target-2']
        for name in names:
            self.assertIn(name, tags.labels)
            self.assertEqual(tags.inputs[name]['type'], 'number')
            self.assertLess(float(tags.inputs[name]['min']), float(tags.inputs[name]['max']))
            self.assertEqual(tags.inputs[name]['aria-describedby'], 'camera-help')
        for name in ['enamel', 'dentin', 'pulp', 'bone']:
            self.assertIn('colour-' + name, tags.labels)
            self.assertEqual(tags.inputs['colour-' + name]['type'], 'color')

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
