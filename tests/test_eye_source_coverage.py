"""Lean synthetic contract checks; actual payload/replay is a separate local gate."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tests/eye_anterior_segment/verify_source_coverage.py'
spec = importlib.util.spec_from_file_location('eye_coverage', SCRIPT)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class EyeSourceCoverageTests(unittest.TestCase):
    def setUp(self):
        self.inventory = json.loads((ROOT / coverage.INVENTORY_FILE).read_text())
        self.record = json.loads((ROOT / coverage.RECORD_FILE).read_text())
        # Synthetic container follows retained names; no media bytes claimed here.
        names = list(dict.fromkeys(m for r in self.inventory['meshNodes'] for m in r['materials']))
        self.model = {'nodes': [], 'meshes': [], 'materials': [{'name': n} for n in names]}
        for row in self.inventory['meshNodes']:
            self.model['nodes'].append({'name': row['node'], 'mesh': row['mesh']})
            self.model['meshes'].append({'primitives': [{'material': names.index(n)} for n in row['materials']]})

    def validate(self):
        coverage.validate_inventory(self.model, self.inventory, self.record)

    def test_complete_inventory(self):
        self.validate()

    def test_identity_and_count_fields(self):
        for key, bad in [('sourceBytes', 1), ('sourceFile', 'wrong.glb'),
                         ('meshNodeCount', 0), ('sourceSha256', '0' * 64)]:
            with self.subTest(field=key):
                original = self.inventory[key]
                self.inventory[key] = bad
                with self.assertRaises(ValueError): self.validate()
                self.inventory[key] = original

    def test_exclusions_are_exact_partition(self):
        scope = copy.deepcopy(self.record['sourceScope'])
        for excluded in [[], scope['excludedSourceMeshes'][:-1],
                         scope['excludedSourceMeshes'][:-1] + [scope['selectedNodes'][0]],
                         scope['excludedSourceMeshes'][:-1] + [scope['excludedSourceMeshes'][0]],
                         scope['excludedSourceMeshes'][:-1] + ['not_a_source_node']]:
            with self.subTest(excluded=excluded):
                self.record['sourceScope']['excludedSourceMeshes'] = excluded
                with self.assertRaises(ValueError): self.validate()

    def test_changed_node_or_material_rejected(self):
        for field, bad in [('node', 'wrong'), ('materials', ['wrong'])]:
            with self.subTest(field=field):
                original = self.inventory['meshNodes'][0][field]
                self.inventory['meshNodes'][0][field] = bad
                with self.assertRaises(ValueError): self.validate()
                self.inventory['meshNodes'][0][field] = original

    def test_invalid_indices_rejected(self):
        self.model['nodes'][0]['mesh'] = -1
        with self.assertRaises(ValueError): self.validate()
        self.model['nodes'][0]['mesh'] = 0
        self.model['meshes'][0]['primitives'][0]['material'] = -1
        with self.assertRaises(ValueError): self.validate()

    def test_optimized_cli_fails_before_reading_payload(self):
        result = subprocess.run([sys.executable, '-O', str(SCRIPT)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Do not use Python -O', result.stderr)
        self.assertNotIn('PASS', result.stdout)


if __name__ == '__main__':
    unittest.main()
