"""Metadata-only guard: does not certify geometry, media delivery, or anatomy."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'reviews/swirendo_fdi31/2026-10-27-interface-locked'


class FDI31EvidenceTests(unittest.TestCase):
    def test_text_receipts_are_exact(self):
        record = json.loads((RUN / 'evidence-index.json').read_text())
        for entry in record['text_evidence']:
            path = RUN / entry['file']
            self.assertEqual(path.parent, RUN)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
            json.loads(path.read_text())

    def test_no_missing_payload_is_claimed_delivered(self):
        record = json.loads((RUN / 'evidence-index.json').read_text())
        self.assertTrue(record['model_delivered_in_this_pr'])
        self.assertTrue(record['pointers_published'])
        self.assertEqual(len(record['media']), 5)
        for entry in record['media']:
            self.assertEqual(entry['availability'], 'repository_lfs_verified')
            path = RUN / entry['file']
            self.assertEqual(path.parent, RUN / 'media')
            data = path.read_bytes()
            expected = f"version https://git-lfs.github.com/spec/v1\noid sha256:{entry['sha256']}\nsize {entry['bytes']}\n".encode()
            if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                self.assertEqual(data, expected)
            else:
                self.assertEqual(len(data), entry['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
        candidate = record['media'][0]
        self.assertEqual(candidate['bytes'], 26524356)
        self.assertEqual(candidate['sha256'], 'c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014')

    def test_gates_remain_separate(self):
        record = json.loads((RUN / 'evidence-index.json').read_text())
        self.assertEqual(record['gates']['anatomy'], 'unapproved')
        self.assertEqual(record['gates']['clinical'], 'unapproved')
        self.assertEqual(record['gates']['runtime'], 'unmeasured')
        self.assertEqual(len(record['rejected_attempts']), 2)
        receipt = json.loads((RUN / 'interface-independent-validation.json').read_text())
        self.assertEqual(receipt['candidate_glb_sha256'], record['media'][0]['sha256'])


if __name__ == '__main__':
    unittest.main()
