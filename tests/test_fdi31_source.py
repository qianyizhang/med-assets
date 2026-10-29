"""Offline safety checks for the source-only route."""
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fdi31_source', ROOT / 'ci/verify_fdi31_source.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


class SourceOnlyTests(unittest.TestCase):
    def test_manifest_failure_stops_before_network(self):
        with patch.object(source, 'download_source') as download:
            with self.assertRaises(source.Stop):
                source.verify(source.MANIFEST.read_bytes() + b' ')
            download.assert_not_called()

    def test_hash_failure_stops_batch_without_lfs(self):
        with patch('lfs_transport.http_bytes', return_value=b'bad bytes') as http, \
             patch('lfs_transport.batch') as lfs_batch, \
             patch('lfs_transport.git') as git:
            with self.assertRaisesRegex(source.Stop, 'Source transport size/hash mismatch'):
                source.verify(source.MANIFEST.read_bytes())
            self.assertEqual(http.call_count, 1)
            lfs_batch.assert_not_called()
            git.assert_not_called()

    def test_fixed_manifest_identity_and_scope(self):
        m = source.validate_manifest(source.MANIFEST.read_bytes(), source.MANIFEST_SHA256)
        self.assertEqual(len(m['objects']), 5)
        self.assertEqual(m['totalBytes'], 27593900)
        self.assertTrue(all(o['url'].startswith('https://anatomy-dental-review.landy123007.chatgpt.site/review/fdi31-interface-locked-20261027/') for o in m['objects']))

    def test_existing_output_is_refused_before_network(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(source, 'download_source') as download:
            with self.assertRaisesRegex(source.Stop, 'fresh directory'):
                source.verify(source.MANIFEST.read_bytes(), Path(directory))
            download.assert_not_called()

    def test_hash_failure_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as directory, patch('lfs_transport.http_bytes', return_value=b'bad'):
            output = Path(directory) / 'new'
            with self.assertRaises(source.Stop):
                source.verify(source.MANIFEST.read_bytes(), output)
            self.assertFalse(output.exists())

    def test_consumer_failure_removes_new_output(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(source, 'download_source', return_value=b'fixture'), \
             patch.object(source, 'consume', side_effect=source.Stop('parse failed')):
            output = Path(directory) / 'new'
            with self.assertRaisesRegex(source.Stop, 'parse failed'):
                source.verify(source.MANIFEST.read_bytes(), output)
            self.assertFalse(output.exists())
