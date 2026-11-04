import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

D = Path(__file__).resolve().parents[1] / "docs/dental-animation/caries-restoration"

class CariesStoryboardTests(unittest.TestCase):
    def setUp(self):
        self.s = json.loads((D / "storyboard.json").read_text())
    def test_equal_beats_and_fixed_canvas(self):
        self.assertEqual((self.s["width"], self.s["height"], self.s["fps"], self.s["duration"]), (960, 540, 30, 12))
        self.assertEqual([(b["start"], b["end"]) for b in self.s["beats"]], [(0, 3), (3, 6), (6, 9), (9, 12)])
    def test_all_layers_resolve_and_parse(self):
        for path in self.s["assets"].values():
            tree = ET.parse(D / path).getroot()
            self.assertEqual(tree.attrib["viewBox"], "0 0 960 540")
    def test_empty_preparation_precedes_restoration(self):
        self.assertLess(self.s["timing"]["cavity_in"][1], self.s["timing"]["restoration_in"][0])
    def test_persistent_safety_label(self):
        self.assertIn("NOT A PROCEDURE GUIDE", (D / "assets/base.svg").read_text())
        self.assertIn("Not an anatomical model", self.s["safety"])

if __name__ == "__main__":
    unittest.main()
