"""Retention lookup reports the scoped evidence and names its coverage gaps."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetentionTest(unittest.TestCase):
    def query(self, *paths):
        return subprocess.run([sys.executable, 'tools/verify.py', 'retained', *paths],
                              cwd=ROOT, capture_output=True, text=True)

    def test_report_follows_named_owners_and_keeps_unknown_paths_unresolved(self):
        result = self.query(
            'models/bronchial_tree/exports/first-fork-fairing-r15/bronchial-first-fork.glb',
            'models/bronchial_tree/recipes/first-fork-fairing-r15/build.py',
            'reviews/teaching-assessments/reopen-source/parathyroid-extents.webp',
            'experiments/dental-image26/results/films/01-early-decay.mp4',
            'sources/fonts/dejavu/LICENSE.txt',
            'heart/Cardiac_Atlas/exports/anatomy_details.json',
            'heart/Cardiac_Atlas/exports/anatomy_details.json.gz',
            'unknown/retention-fixture.file',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for text in ('Accepted teaching task bronchial-tree-first-fork',
                     'Maintained selection · Bronchial tree',
                     'Candidate Gallery read declaration /assets/',
                     'Maintained recipe entry point',
                     'Open work item (ready)',
                     'Declared recovery member · teaching-media',
                     'License or attribution record',
                     'Cardiac recovery backing path · heart/Cardiac_Atlas/exports/anatomy_details.json.gz',
                     'Cardiac recovery backing for heart/Cardiac_Atlas/exports/anatomy_details.json',
                     'unknown/retention-fixture.file\n  No reference found',
                     'An empty result does not establish that a path can be deleted.'):
            with self.subTest(text=text):
                self.assertIn(text, result.stdout)

    def test_path_traversal_is_rejected(self):
        result = self.query('../outside')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exact repository-relative file path', result.stderr)


if __name__ == '__main__':
    unittest.main()
