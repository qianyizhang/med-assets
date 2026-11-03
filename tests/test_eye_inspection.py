import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'gallery/eye-inspection/r01'
spec = importlib.util.spec_from_file_location('eye_recipe', PACKAGE / 'apply.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)

class EyeInspectionTests(unittest.TestCase):
    def fixture(self, directory):
        target = Path(directory)
        prior = {'assets': [{'id': 'preserved'}], 'candidates': [{'id': 'existing', 'gates': {'runtime': 'unverified'}}], 'history': [{'id': 'retained'}]}
        binding = copy.deepcopy(recipe.BINDING)
        for name in binding['inputs']:
            p = target / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((json.dumps(prior) if name == 'review-data.json' else 'original:' + name).encode())
            binding['inputs'][name] = recipe.digest(p.read_bytes())
        updated = copy.deepcopy(prior)
        updated['candidates'].append(json.loads((PACKAGE / 'record.json').read_text()))
        binding['outputs']['review-data.json'] = recipe.digest((json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode())
        return target, binding, prior

    def snapshot(self, target):
        return {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}

    def test_apply_preserves_existing_records_dependencies_and_rejects_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            target, binding, prior = self.fixture(directory)
            before = self.snapshot(target)
            with patch.object(recipe, 'BINDING', binding):
                recipe.apply(target)
                after = self.snapshot(target)
                data = json.loads(after['review-data.json'])
                self.assertEqual(data['candidates'][:-1], prior['candidates'])
                for name in prior:
                    if name != 'candidates': self.assertEqual(data[name], prior[name])
                for name in binding['inputs']:
                    if name not in binding['outputs']: self.assertEqual(after[name], before[name])
                with self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(self.snapshot(target), after)

    def test_every_wrong_input_refuses_before_write(self):
        for name in recipe.BINDING['inputs']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target, binding, _ = self.fixture(directory)
                (target / name).write_bytes(b'corrupt')
                before = self.snapshot(target)
                with patch.object(recipe, 'BINDING', binding), self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(self.snapshot(target), before)

    def test_wrong_output_or_record_refuses_before_write(self):
        for case in ['record'] + list(recipe.BINDING['outputs']):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                target, binding, _ = self.fixture(directory)
                if case == 'record': binding['recordSha256'] = '0' * 64
                else: binding['outputs'][case] = '0' * 64
                before = self.snapshot(target)
                with patch.object(recipe, 'BINDING', binding), self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(self.snapshot(target), before)

    def test_existing_module_or_duplicate_record_refuses(self):
        for case in ['inspection-modes.mjs', 'eye-r03-changelog.md', 'duplicate']:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                target, binding, _ = self.fixture(directory)
                if case == 'duplicate':
                    p = target / 'review-data.json'
                    data = json.loads(p.read_text())
                    data['candidates'].append(json.loads((PACKAGE / 'record.json').read_text()))
                    p.write_text(json.dumps(data))
                    binding['inputs']['review-data.json'] = recipe.digest(p.read_bytes())
                else: (target / case).write_bytes(b'preserved')
                before = self.snapshot(target)
                with patch.object(recipe, 'BINDING', binding), self.assertRaises(ValueError): recipe.apply(target)
                self.assertEqual(self.snapshot(target), before)

    def test_actual_payload_and_dependency_identities(self):
        for name, digest in recipe.BINDING['outputs'].items():
            if name != 'review-data.json': self.assertEqual(recipe.digest((PACKAGE / name).read_bytes()), digest)
        for name, path in {
            'candidate-contract.mjs': ROOT / 'tests/knee_inspection/fixtures/candidate-contract.mjs',
            'viewer-lifecycle.mjs': ROOT / 'gallery/candidate-lifecycle/r01/viewer-lifecycle.mjs',
            'context-loss.mjs': ROOT / 'gallery/candidate-context/r01/context-loss.mjs',
            'model-media.mjs': ROOT / 'tests/eye_inspection/fixtures/model-media.mjs',
        }.items(): self.assertEqual(recipe.digest(path.read_bytes()), recipe.BINDING['inputs'][name])

    def test_actual_reviewed_helper_and_composition_without_media(self):
        run = subprocess.run(['python3', str(ROOT / 'tests/eye_inspection/run.py')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn('# fail 0', run.stdout)
        self.assertIn('# skipped 0', run.stdout)
        self.assertIn('# tests 14', run.stdout)
