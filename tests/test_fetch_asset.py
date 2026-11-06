import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import fetch_asset as fetch


class Response(io.BytesIO):
    status = 200
    headers = {}


class FetchAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name).resolve() / 'cache'
        self.payload = b'glTF-test-public-payload'
        self.digest = hashlib.sha256(self.payload).hexdigest()

    def download(self, data=None, **kwargs):
        return fetch.fetch_asset(self.cache, 'models/example.glb', self.digest, len(self.payload),
                                 open_url=lambda *a, **k: Response(self.payload if data is None else data), **kwargs)

    def test_verified_download_and_cache_reuse(self):
        target = self.download()
        self.assertEqual(target.read_bytes(), self.payload)
        unexpected_network = Mock(side_effect=AssertionError('Cached file must avoid network'))
        self.assertEqual(fetch.fetch_asset(self.cache, 'models/example.glb', self.digest,
                                          len(self.payload), open_url=unexpected_network), target)

    def test_corruption_and_truncation_leave_no_cache_entry_or_partial_file(self):
        for body in [b'x' * len(self.payload), self.payload[:-1], self.payload + b'x']:
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.download(body)
            self.assertEqual(list(self.cache.iterdir()), [])

    def test_corrupt_cache_is_not_silently_overwritten(self):
        target = self.download()
        target.write_bytes(b'x' * len(self.payload))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.download()
        self.assertEqual(target.read_bytes(), b'x' * len(self.payload))

    def test_cache_symlinks_are_refused(self):
        self.cache.mkdir()
        outside = self.cache.parent / 'outside'
        outside.write_bytes(self.payload)
        (self.cache / self.digest).symlink_to(outside)
        with self.assertRaises(OSError):
            self.download()
        self.assertEqual(outside.read_bytes(), self.payload)

    def test_cache_directory_symlink_is_refused(self):
        outside = self.cache.parent / 'outside'
        outside.mkdir()
        self.cache.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.download()

    def test_redirect_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'redirect'):
            fetch.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org')

    def test_error_status_and_encoding_are_refused(self):
        for status, headers in [(404, {}), (200, {'Content-Encoding': 'gzip'})]:
            response = Response(self.payload)
            response.status, response.headers = status, headers
            with self.subTest(status=status, headers=headers), self.assertRaises(ValueError):
                fetch.fetch_asset(self.cache, 'x.glb', self.digest, len(self.payload),
                                  open_url=lambda *a, **k: response)

    def test_disappearing_concurrent_cache_entry_does_not_report_success(self):
        with patch.object(fetch.os, 'link', side_effect=FileExistsError):
            with self.assertRaisesRegex(ValueError, 'disappeared'):
                self.download()
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_path_traversal_is_refused_before_git(self):
        for name in ['../x.glb', '/x.glb', './x.glb', 'x/../y.glb', 'x\\y.glb']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                fetch.pinned_asset(self.cache, 'HEAD', name)


if __name__ == '__main__':
    unittest.main()
