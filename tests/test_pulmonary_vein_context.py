"""Reject source drift, mirrored orientation and mismatched visibility comparisons."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.pulmonary_vein_context import build, source

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'reviews/pulmonary_vein/2026-10-30-context/render.json'


class PulmonaryContextBindingTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(RECEIPT.read_text())
        self.expected = copy.deepcopy(self.record['source'])

    def test_retained_visibility_pairs_are_bound(self):
        build.validate_record(self.record, self.expected)

    def test_unhydrated_or_changed_master_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'GLB identity mismatch'):
            source.decode_glb(b'version https://git-lfs.github.com/spec/v1\n')

    def test_context_from_another_case_is_rejected(self):
        self.record['source']['contexts'][0]['case'] = 's1336'
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            build.validate_record(self.record, self.expected)

    def test_independently_fitted_context_is_rejected(self):
        self.record['source']['coordinateMapping']['independentFitting'] = True
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            build.validate_record(self.record, self.expected)

    def test_mirrored_posterior_camera_is_rejected(self):
        self.record['views'][1]['cameraWorldMatrix'][0][0] = 1
        with self.assertRaisesRegex(ValueError, 'mirrored or rotated'):
            build.validate_record(self.record, self.expected)

    def test_context_camera_cannot_drift_from_isolated_camera(self):
        self.record['views'][3]['cameraPosition'][0] += .003
        with self.assertRaisesRegex(ValueError, 'Camera position differs'):
            build.validate_record(self.record, self.expected)

    def test_swapped_isolated_and_context_image_roles_are_rejected(self):
        self.record['views'][0]['file'] = 'overview-context.png'
        with self.assertRaisesRegex(ValueError, 'Swapped image role'):
            build.validate_record(self.record, self.expected)

    def test_missing_context_object_is_rejected(self):
        self.record['source']['contexts'].pop()
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            build.validate_record(self.record, self.expected)

    def test_unverified_geometry_preservation_is_rejected(self):
        self.record['sourceBytesAndGeometryUnchanged'] = False
        with self.assertRaisesRegex(ValueError, 'Geometry preservation'):
            build.validate_record(self.record, self.expected)

    def test_original_near_edge_overview_fails_margin_requirement(self):
        old = source.context_framing(self.expected['contexts'], {'position': [0., .55, .065], 'scale': .36})
        self.assertLess(old['minimumEdgeMarginPx'], 1)
        with self.assertRaisesRegex(ValueError, 'lacks breathing room'):
            source.require_framing_margin(old)

    def test_detail_reuse_rejects_a_different_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'render.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'reuse receipt identity mismatch'):
                source.reuse_v1_detail(directory, self.expected)


if __name__ == '__main__':
    unittest.main()
