import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'gallery/study-origin-labels/r01'
BASELINE = ROOT / 'tests/study_origin_labels/fixtures/review-v48.js'
spec = importlib.util.spec_from_file_location('study_origin_recipe', PACKAGE / 'apply.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)

class StudyOriginLabelsTests(unittest.TestCase):
    def test_exact_output_and_actual_source_regressions(self):
        raw = BASELINE.read_bytes()
        updated = recipe.patched(raw)
        self.assertEqual(recipe.digest(updated), recipe.BINDING['output'])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'review.js'
            target.write_bytes(updated)
            env = dict(os.environ, LABEL_RENDERER=str(target))
            result = subprocess.run(['node', '--test', '--test-reporter=tap', str(ROOT / 'tests/study_origin_labels/renderer.test.mjs')], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for expected in ['# tests 3', '# pass 3', '# fail 0', '# skipped 0']:
                self.assertIn(expected, result.stdout)

    def fixture(self, directory):
        target = Path(directory)
        (target / 'review.js').write_bytes(BASELINE.read_bytes())
        (target / 'review-data.json').write_bytes(b'opaque preserved data')
        binding = copy.deepcopy(recipe.BINDING)
        binding['inputs']['review-data.json'] = recipe.digest((target / 'review-data.json').read_bytes())
        return target, binding

    def test_apply_preserves_data_and_refuses_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            target, binding = self.fixture(directory)
            with patch.object(recipe, 'BINDING', binding):
                recipe.apply(target)
                after = {p.name: p.read_bytes() for p in target.iterdir()}
                self.assertEqual(after['review-data.json'], b'opaque preserved data')
                with self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(after, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_each_wrong_input_refuses_without_writes(self):
        for name in recipe.BINDING['inputs']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target, binding = self.fixture(directory)
                (target / name).write_bytes(b'corrupt')
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                with patch.object(recipe, 'BINDING', binding), self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_wrong_output_or_nonunique_expression_refuses_without_writes(self):
        for case in ['output', 'missing', 'duplicate']:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                target, binding = self.fixture(directory)
                if case == 'output': binding['output'] = '0' * 64
                else:
                    old = recipe.EDITS[0][0]
                    raw = BASELINE.read_text().replace(old, '' if case == 'missing' else old + old)
                    (target / 'review.js').write_text(raw)
                    binding['inputs']['review.js'] = recipe.digest(raw.encode())
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                with patch.object(recipe, 'BINDING', binding), self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})
