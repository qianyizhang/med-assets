"""Current external-renderer contracts; no old patch applicability or browser claims."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/gallery/fixtures'


class GalleryRendererTests(unittest.TestCase):
    def test_exact_current_source_and_behavior(self):
        binding = json.loads((FIXTURES / 'source.json').read_text())
        for name, digest in binding['files'].items():
            self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), digest, name)
        result = subprocess.run(['node', '--test', '--test-reporter=tap',
                                 str(ROOT / 'tests/gallery/renderer.test.mjs')],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in ('# tests 8', '# pass 8', '# fail 0', '# cancelled 0', '# skipped 0', '# todo 0'):
            self.assertIn(line, result.stdout)

    def test_retained_elbow_material_evidence(self):
        proof = json.loads((ROOT / 'gallery/elbow-legend-source.json').read_text())
        self.assertEqual(proof['artifactSHA256'], 'cd6cd488943fe721101955322b343a8c9441f1d4ff8c5042dd4e1ca7462f7891')
        self.assertEqual(proof['contactEvidence']['imageSHA256'], '5d98b09ffac33ed679ec9087d7dc8da52bbffaf98efcbdc81d2c4a79962d227d')
        selected = [node for node in proof['nodes'] if node['materialIndices'] == [1]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['extras']['source_object_name'], 'Articular capsule of elbow joint.r')
        self.assertEqual(proof['materials'][1]['name'], 'Capsule | illustrative transparency')
