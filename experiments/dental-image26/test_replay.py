"""Failures that must stop a rebuild before narration and pictures drift."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import render


class RetainedEditTests(unittest.TestCase):
    def setUp(self):
        self.spec = render.specification()
        self.transcript = (render.ROOT / 'audio/narration.srt').read_text()

    def timing(self, transcript):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'audio').mkdir()
            (root / 'audio/narration.srt').write_text(transcript)
            with patch.object(render, 'ROOT', root):
                return render.retained_timings(self.spec)

    def test_retained_edit_preserves_full_scene_coverage(self):
        timings = self.timing(self.transcript)
        self.assertEqual(sum(timings.values()), 5035)
        for story in self.spec['stories']:
            for shot in story['shots']:
                self.assertGreaterEqual(timings[shot['id']], 192)

    def test_changed_narration_is_not_silently_reused(self):
        changed = self.transcript.replace('Five dental conditions.', 'Six dental conditions.', 1)
        with self.assertRaisesRegex(ValueError, 'transcript differs'):
            self.timing(changed)

    def test_missing_scene_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cue count differs'):
            self.timing(self.transcript.split('\n\n', 1)[1])

    def test_cut_gap_is_rejected(self):
        changed = self.transcript.replace('00:00:12,100', '00:00:12,200', 1)
        with self.assertRaisesRegex(ValueError, 'Noncontiguous'):
            self.timing(changed)

    def test_invalid_timestamp_is_rejected(self):
        changed = self.transcript.replace('00:00:12,100', '00:99:12,100', 1)
        with self.assertRaisesRegex(ValueError, 'Invalid narration timestamp'):
            self.timing(changed)


if __name__ == '__main__':
    unittest.main()
