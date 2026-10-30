"""Offline failures must not masquerade as verified native shoulder teaching."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('cuff_checks', Path(__file__).parent/'rotator_cuff/verify.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class CuffRecords(unittest.TestCase):
    def setUp(self):
        self.inventory, self.checks = CHECK.read_records()

    def test_retained_scope(self):
        CHECK.validate(self.inventory, self.checks)

    def test_wrong_source_or_export(self):
        for target, key in [(self.inventory, 'sourceSha256'), (self.checks, 'artifactSha256')]:
            old = target[key]
            target[key] = '0'*64
            with self.assertRaises(ValueError):
                CHECK.validate(self.inventory, self.checks)
            target[key] = old

    def test_failed_surface_check(self):
        for key, value in [('maxWorldError', float('nan')), ('maxWorldError', .01),
                           ('triangleMultisetMatches', False), ('triangles', 0)]:
            altered = deepcopy(self.checks)
            altered['objects'][0][key] = value
            with self.assertRaises(ValueError):
                CHECK.validate(self.inventory, altered)

    def test_incomplete_views_or_wrong_label(self):
        variants = [deepcopy(self.checks) for _ in range(3)]
        variants[0]['exportViews'].pop()
        variants[1]['exportViews'][0]['anchors'][0]['object'] = 'Scapula.r'
        variants[2]['exportViews'][0]['anchors'][0]['pixel'] = [-1, 300]
        for altered in variants:
            with self.assertRaises(ValueError):
                CHECK.validate(self.inventory, altered)
        presentation = json.loads((CHECK.ROOT/CHECK.REVIEW/'v2/composition.json').read_text())
        CHECK.validate_composition(presentation, self.inventory['artifact']['sha256'])
        for labels in [[], presentation['labelBindings'][:-1],
                       presentation['labelBindings'][:-1]+[presentation['labelBindings'][0]]]:
            altered = deepcopy(presentation)
            altered['labelBindings'] = labels
            with self.assertRaises(ValueError):
                CHECK.validate_composition(altered, self.inventory['artifact']['sha256'])

    def test_payload_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'payload.glb'
            path.write_bytes(b'changed payload')
            with self.assertRaises(ValueError):
                CHECK.require_hash(path, self.inventory['artifact']['sha256'])


if __name__ == '__main__':
    unittest.main()
