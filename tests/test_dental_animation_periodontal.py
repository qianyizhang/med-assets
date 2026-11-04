import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("periodontal", ROOT / "docs/dental-animation/periodontal-cleaning/render.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class PeriodontalAnimaticTests(unittest.TestCase):
    def test_all_frames_are_well_formed_and_bounded(self):
        for frame in range(M.N):
            tree = ET.fromstring(M.render(frame))
            self.assertEqual(tree.attrib["width"], "960")
            self.assertEqual(tree.attrib["height"], "540")
            for node in tree.iter():
                if "opacity" in node.attrib:
                    self.assertGreaterEqual(float(node.attrib["opacity"]), 0)
                    self.assertLessEqual(float(node.attrib["opacity"]), 1)
    def test_tissue_geometry_is_constant(self):
        def paths(f):
            return [n.attrib["d"] for n in ET.fromstring(M.render(f)).iter() if n.tag.endswith("path") and "fill" in n.attrib and n.attrib["fill"] != "none"]
        for frame in range(M.N):
            self.assertEqual(paths(0), paths(frame))
    def test_stages_keep_schematic_and_review_limits(self):
        for frame, title in zip((0, 36, 72, 108), M.HEAD):
            svg = M.render(frame)
            self.assertIn(title, svg)
            self.assertIn("SCHEMATIC ANATOMY", svg)
            self.assertIn("Clinical review still required", svg)
    def test_deposits_clear_without_tissue_regrowth(self):
        def opacity(f):
            return [float(n.attrib["opacity"]) for n in ET.fromstring(M.render(f)).iter() if n.tag.endswith("ellipse") and n.attrib.get("fill") == "#e6ae4a"]
        self.assertEqual(opacity(0), [1.] * 10)
        self.assertEqual(opacity(143), [0.] * 10)
        self.assertIn("No instant gum or bone regrowth", M.render(143))

if __name__ == "__main__":
    unittest.main()
