import ast
import json
from pathlib import Path
import unittest

D = Path(__file__).resolve().parents[1] / "docs/dental-animation/fdi31-layer-reveal"

class FDI31AnimaticTests(unittest.TestCase):
    def test_source_identity_and_reset_receipt(self):
        m = json.loads((D / "manifest.json").read_text())
        g = json.loads((D / "geometry-check.json").read_text())
        self.assertEqual(m["source_sha256"], "90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7")
        self.assertEqual(m["source_sha256"], g["source_sha256"])
        self.assertTrue(g["geometry_identical"])
        self.assertTrue(g["relative_source_reset_exact"])
    def test_four_source_layers_remain_unvalidated(self):
        g = json.loads((D / "geometry-check.json").read_text())
        self.assertEqual(set(g["mesh_signatures"]), {"enamel", "dentin", "pulp", "bone"})
        self.assertFalse(g["clinical_validation"])
        self.assertFalse(g["physiological_motion"])
    def test_replay_scripts_parse(self):
        for name in ("render.py", "compose.py", "verify_geometry.py"):
            ast.parse((D / name).read_text())
    def test_timeline_and_labels(self):
        m = json.loads((D / "manifest.json").read_text())
        self.assertEqual((m["frames"], m["fps"]), (72, 8))
        self.assertIn("keyframe_insert", (D / "render.py").read_text())
        self.assertIn("No clinical or motion validation", (D / "compose.py").read_text())

if __name__ == "__main__":
    unittest.main()
