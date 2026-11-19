"""Verify recovery when the optional same-case restore is interrupted."""

from contextlib import redirect_stderr
from functools import partial
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

SURVEY = Path(__file__).resolve().parents[1] / "sites/body-systems-survey"
sys.path.insert(0, str(SURVEY))
try:
    import gallery_plan
    import report
finally:
    sys.path.pop(0)


class SameCaseRecovery(unittest.TestCase):
    def test_interrupted_restore_disables_optional_gallery_and_viewer_plates(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "assemblies.json").write_text(json.dumps({
                "configSha256": report.digest(gallery_plan.WORKSHOP_CONFIG),
            }))
            log = io.StringIO()
            with (
                patch.object(report, "WORKSHOP_ASSEMBLIES", folder),
                patch.object(report, "workshop_scenes", partial(gallery_plan.workshop_scenes, folder)),
                redirect_stderr(log),
            ):
                jobs, plates, warning, audit = report.workshop_presentation()
            self.assertEqual(jobs, [])
            self.assertEqual(plates, {})
            self.assertIsNone(audit)
            self.assertIn("fallbacks", warning)
            self.assertIn("mask-audit.json", log.getvalue())

    def test_colon_copy_reads_measurements_and_rejects_inconsistent_counts(self):
        colon = {
            "components6": 3,
            "voxels": 161648,
            "componentVoxelCounts6": [122899, 38714, 35],
            "largestComponentsMinimumVoxelCentreMm": 24.602,
        }
        audit = {"parts": {"colon": colon}}
        self.assertIn("122,899, 38,714, 35 voxels", report.colon_gap_copy(audit))
        self.assertIn("24.602 mm", report.colon_gap_copy(audit))
        colon["componentVoxelCounts6"].pop()
        with self.assertRaisesRegex(ValueError, "Invalid colon component measurements"):
            report.colon_gap_copy(audit)
