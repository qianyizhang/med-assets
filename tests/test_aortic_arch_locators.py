"""Offline failure tests for source-named editorial locator bindings."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.aortic_arch_locators import build as builder
sys.path.pop(0)
RECORD = ROOT / "reviews/aortic_tree_z/2026-10-29-arch-locators/render.json"


class LocatorBindingTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(RECORD.read_text())
        self.source_inventory = copy.deepcopy(self.record)

    def test_retained_projection_receipt_is_accepted(self):
        builder.validate_mapping(self.record, self.source_inventory)

    def test_changed_source_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            builder.inventory(b"version https://git-lfs.github.com/spec/v1\n")

    def test_swapped_right_left_name_is_rejected(self):
        a = self.record["views"][1]["anchors"]
        a[2]["sourceNode"], a[3]["sourceNode"] = a[3]["sourceNode"], a[2]["sourceNode"]
        with self.assertRaisesRegex(ValueError, "Swapped source-to-callout"):
            builder.validate_mapping(self.record, self.source_inventory)

    def test_mirrored_camera_is_rejected(self):
        self.record["views"][0]["cameraWorldMatrix"][0][0] = -1
        with self.assertRaisesRegex(ValueError, "camera orientation"):
            builder.validate_mapping(self.record, self.source_inventory)

    def test_plausible_pixel_with_wrong_source_coordinate_is_rejected(self):
        a = self.record["views"][1]["anchors"][0]
        a["pixel"][0] += 4
        a["projectedHitPixel"][0] += 4
        with self.assertRaisesRegex(ValueError, "Source/camera projection mismatch"):
            builder.validate_mapping(self.record, self.source_inventory)

    def test_claimed_nonexistent_polygon_is_rejected(self):
        self.record["views"][0]["anchors"][0]["rayHitPolygon"] = 999999
        with self.assertRaisesRegex(ValueError, "polygon outside source"):
            builder.validate_mapping(self.record, self.source_inventory)

    def test_composite_cannot_be_relabelled_as_single_structure(self):
        self.record["groups"][0]["sourceNames"] = ["Brachiocephalic trunk"]
        with self.assertRaisesRegex(ValueError, "inventory mismatch: groups"):
            builder.validate_mapping(self.record, self.source_inventory)

    def test_missing_ray_hit_is_rejected(self):
        self.record["views"][1]["anchors"][2]["rayHitExactSourceNode"] = False
        with self.assertRaisesRegex(ValueError, "lacks exact node ray hit"):
            builder.validate_mapping(self.record, self.source_inventory)


if __name__ == "__main__":
    unittest.main()
