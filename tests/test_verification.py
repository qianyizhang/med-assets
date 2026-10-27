"""Failure-path checks for the verification boundary; synthetic fixtures only."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify
from lfs_transport import Stop, load_manifest


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b'synthetic payload, not a model'
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.pointer = (f'version https://git-lfs.github.com/spec/v1\noid sha256:{self.digest}\n'
                        f'size {len(self.data)}\n').encode()

    def test_pointer_requires_complete_canonical_fields(self):
        self.assertEqual(verify.parse_pointer(self.pointer), (self.digest, len(self.data)))
        for bad in (self.pointer.replace(b'sha256:', b'sha1:'), self.pointer + b'extra\n',
                    self.pointer.replace(b'size ', b'size -'), self.pointer[:-1],
                    self.pointer.replace(self.digest.encode(), b'0'*63)):
            with self.subTest(pointer=bad), self.assertRaises(ValueError):
                verify.parse_pointer(bad)

    def indexed_fixture(self, data):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        # Write synthetic Git objects directly: no LFS fetch, clean filter or credentials.
        for name, content in (('.gitattributes', b'*.glb filter=lfs -text\n'), ('asset.glb', data)):
            (self.root / name).write_bytes(content)
            oid = verify.git(self.root, 'hash-object', '-w', '--stdin', data=content).decode().strip()
            verify.git(self.root, 'update-index', '--add', '--cacheinfo', '100644', oid, name)

    def test_valid_pointer_checkout_needs_no_payload(self):
        self.indexed_fixture(self.pointer)
        self.assertEqual(verify.index_pointers(self.root), {'asset.glb': (self.digest, len(self.data))})

    def test_malformed_index_pointer_fails(self):
        self.indexed_fixture(self.pointer.replace(b'size ', b'missing-size '))
        with self.assertRaisesRegex(ValueError, 'Malformed LFS pointer'):
            verify.index_pointers(self.root)

    def test_changed_working_pointer_fails(self):
        self.indexed_fixture(self.pointer)
        (self.root / 'asset.glb').write_bytes(self.pointer.replace(self.digest.encode(), b'0'*64))
        with self.assertRaisesRegex(ValueError, 'Working pointer differs'):
            verify.index_pointers(self.root)

    def test_current_text_corruption_fails(self):
        path = self.root / 'head.svg'
        path.write_bytes(self.data)
        ref = {'file': path.name, 'sha256': self.digest}
        self.assertEqual(verify.check_reference(self.root, {}, ref), self.digest)
        path.write_bytes(self.data + b'corruption')
        with self.assertRaisesRegex(ValueError, 'Current file SHA-256 mismatch'):
            verify.check_reference(self.root, {}, ref)

    def test_pointer_identity_is_not_payload_integrity(self):
        path = self.root / 'asset.glb'
        path.write_bytes(self.pointer)
        pointers = {'asset.glb': (self.digest, len(self.data))}
        self.assertEqual(verify.check_reference(self.root, pointers, {'file': path.name, 'sha256': self.digest}), self.digest)
        with self.assertRaisesRegex(ValueError, 'Unresolved LFS pointer'):
            verify.payload_integrity(self.root, pointers, [])

    def test_payload_corruption_fails_after_good_bytes_pass(self):
        path = self.root / 'asset.glb'
        path.write_bytes(self.data)
        pointers = {'asset.glb': (self.digest, len(self.data))}
        with patch.object(verify, 'PAYLOAD_CHECKS', ()), contextlib.redirect_stdout(io.StringIO()):
            verify.payload_integrity(self.root, pointers, [])
        path.write_bytes(b'X' + self.data[1:])  # Same length, wrong hash.
        with self.assertRaisesRegex(ValueError, 'Payload size/SHA-256 mismatch'):
            verify.payload_integrity(self.root, pointers, [])

    def test_pointer_reference_mismatch_fails(self):
        (self.root / 'asset.glb').write_bytes(self.pointer)
        with self.assertRaisesRegex(ValueError, 'LFS pointer OID/reference mismatch'):
            verify.check_reference(self.root, {'asset.glb': (self.digest, len(self.data))},
                                   {'file': 'asset.glb', 'sha256': '0'*64})

    def test_historical_checksum_rewrite_fails(self):
        (self.root / 'SHA256SUMS').write_bytes(b'new checksums hide drift\n')
        with self.assertRaisesRegex(ValueError, 'Historical SHA256SUMS changed'):
            verify.current_import_checks(self.root, {})

    def test_historical_import_manifest_rewrite_fails(self):
        (self.root / 'SHA256SUMS').write_bytes((ROOT / 'SHA256SUMS').read_bytes())
        path = self.root / 'metadata/asset-manifest.json'
        path.parent.mkdir()
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Historical asset manifest changed'):
            verify.current_import_checks(self.root, {})

    def test_imported_lfs_pointer_wrong_size_fails(self):
        pointers = verify.index_pointers(ROOT)
        name = 'heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb'
        oid, size = pointers[name]
        pointers[name] = (oid, size + 1)
        with self.assertRaisesRegex(ValueError, 'LFS pointer size/import mismatch'):
            verify.current_import_checks(ROOT, pointers)

    def test_lfs_import_override_requires_current_size(self):
        pointers = verify.index_pointers(ROOT)
        name = 'heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb'
        overrides = json.loads((ROOT / 'metadata/current-import-overrides.json').read_text())
        overrides[name] = {'importSha256': pointers[name][0], 'currentSha256': '1'*64,
                           'changeCommit': '5fae2dd', 'reason': 'synthetic fixture'}
        read_json = verify.read_json
        def with_override(path):
            return overrides if path.name == 'current-import-overrides.json' else read_json(path)
        with patch.object(verify, 'read_json', side_effect=with_override):
            with self.assertRaisesRegex(ValueError, 'LFS import override requires currentBytes'):
                verify.current_import_checks(ROOT, pointers)

    def test_transport_lfs_pointer_wrong_size_fails(self):
        source = ROOT / 'transport/manifests/96dfb7956224d3331b0a095f26e4d89f34e8d7a4c6054f8b52bc826b041dda45.json'
        obj = json.loads(source.read_text())['objects'][0]
        with self.assertRaisesRegex(ValueError, 'LFS pointer size/transport mismatch'):
            verify.validate_transport_manifests(ROOT, {'synthetic.glb': (obj['sha256'], obj['bytes'] + 1)})

    def test_same_oid_with_conflicting_pointer_sizes_fails(self):
        oid = '0'*64
        with self.assertRaisesRegex(ValueError, 'Conflicting sizes for identical LFS OID'):
            verify.validate_transport_manifests(ROOT, {'a.glb': (oid, 10), 'b.glb': (oid, 11)})

    def test_same_oid_with_conflicting_manifest_sizes_fails(self):
        source = ROOT / 'transport/manifests/96dfb7956224d3331b0a095f26e4d89f34e8d7a4c6054f8b52bc826b041dda45.json'
        directory = self.root / 'transport/manifests'
        directory.mkdir(parents=True)
        for path in (ROOT / 'transport/manifests').glob('*.json'):
            (directory / path.name).write_bytes(path.read_bytes())
        changed = json.loads(source.read_text())
        changed['objects'][0]['bytes'] += 1
        changed['totalBytes'] += 1
        data = json.dumps(changed).encode()
        (directory / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'Conflicting transport manifest sizes'):
            verify.validate_transport_manifests(self.root, {})

    def test_missing_historical_transport_manifest_fails(self):
        directory = self.root / 'transport/manifests'
        directory.mkdir(parents=True)
        paths = sorted((ROOT / 'transport/manifests').glob('*.json'))
        missing = '025a8cd957159caa51c48096ddc9cf4197bb0d51a9b7119d1b08b3a51e41f748'
        for path in paths:
            if path.stem == missing:
                continue
            (directory / path.name).write_bytes(path.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Historical transport manifests missing'):
            verify.validate_transport_manifests(self.root, {})

    def test_new_transport_manifest_needs_no_baseline_update(self):
        directory = self.root / 'transport/manifests'
        directory.mkdir(parents=True)
        paths = sorted((ROOT / 'transport/manifests').glob('*.json'))
        for path in paths:
            (directory / path.name).write_bytes(path.read_bytes())
        source = ROOT / 'transport/manifests/96dfb7956224d3331b0a095f26e4d89f34e8d7a4c6054f8b52bc826b041dda45.json'
        changed = json.loads(source.read_text())
        changed['scope'] = 'Synthetic additional manifest; test only'
        data = json.dumps(changed).encode()
        (directory / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)
        self.assertEqual(verify.validate_transport_manifests(self.root, {}), len(paths) + 1)

    def test_missing_historical_foundation_record_fails(self):
        paths = verify.foundation_records(ROOT)
        for path in paths:
            if path.parts[-3] == 'aorta':
                continue
            target = self.root / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Historical foundation record set changed or missing'):
            verify.foundation_records(self.root)

    def test_content_addressed_manifest_mutation_fails(self):
        source = next((ROOT / 'transport/manifests').glob('*.json'))
        target = self.root / 'transport/manifests' / source.name
        target.parent.mkdir(parents=True)
        target.write_bytes(source.read_bytes())
        load_manifest(self.root, source.stem)
        target.write_bytes(source.read_bytes() + b'\n')
        with self.assertRaisesRegex(Stop, 'Manifest byte/hash mismatch'):
            load_manifest(self.root, source.stem)

    def test_invalid_manifest_fails_even_with_matching_content_hash(self):
        source = next((ROOT / 'transport/manifests').glob('*.json'))
        manifest = json.loads(source.read_text())
        manifest['objects'][0]['url'] = 'https://unapproved.example.invalid/review/asset.glb'
        data = json.dumps(manifest).encode()
        digest = hashlib.sha256(data).hexdigest()
        target = self.root / 'transport/manifests' / (digest + '.json')
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        with self.assertRaisesRegex(Stop, 'Source host/query not allowed'):
            load_manifest(self.root, digest)

    def fixture_suite(self, body):
        path = self.root / 'test_required.py'
        path.write_text('import unittest\n' + body)
        return path

    def run_fixture(self, body, minimum=1):
        return verify.run_suite(self.fixture_suite(body), minimum, stream=io.StringIO())

    def test_missing_required_suite_fails(self):
        with self.assertRaisesRegex(ValueError, 'Required suite missing'):
            verify.run_suite(self.root / 'missing.py', stream=io.StringIO())

    def test_empty_required_suite_fails(self):
        with self.assertRaisesRegex(ValueError, 'empty or incomplete'):
            self.run_fixture('')

    def test_missing_required_dependency_fails(self):
        with self.assertRaises(ModuleNotFoundError):
            self.run_fixture('import nonexistent_med_assets_dependency_fixture\n')

    def test_skipped_required_suite_fails(self):
        with self.assertRaisesRegex(ValueError, 'failed, skipped or expected-failed'):
            self.run_fixture('class Required(unittest.TestCase):\n @unittest.skip("missing dependency")\n def test_required(self): pass\n')

    def test_expected_failure_does_not_count_as_pass(self):
        with self.assertRaisesRegex(ValueError, 'failed, skipped or expected-failed'):
            self.run_fixture('class Required(unittest.TestCase):\n @unittest.expectedFailure\n def test_required(self): self.fail("required behavior")\n')

    def test_required_assertion_failure_fails(self):
        with self.assertRaisesRegex(ValueError, 'failed, skipped or expected-failed'):
            self.run_fixture('class Required(unittest.TestCase):\n def test_required(self): self.fail("broken")\n')

    def test_module_setup_failure_fails(self):
        with self.assertRaisesRegex(ValueError, 'failed, skipped or expected-failed'):
            self.run_fixture('def setUpModule(): raise RuntimeError("required setup unavailable")\n'
                             'class Required(unittest.TestCase):\n def test_required(self): pass\n')

    def test_module_teardown_failure_fails(self):
        with self.assertRaisesRegex(ValueError, 'failed, skipped or expected-failed'):
            self.run_fixture('def tearDownModule(): raise RuntimeError("required cleanup failed")\n'
                             'class Required(unittest.TestCase):\n def test_required(self): pass\n')

    def test_early_stopped_suite_fails(self):
        with self.assertRaisesRegex(ValueError, 'execution incomplete'):
            self.run_fixture('class Required(unittest.TestCase):\n'
                             ' def test_a(self): self._outcome.result.stop()\n'
                             ' def test_b(self): self.fail("must execute")\n', minimum=2)

    def test_complete_required_suite_passes(self):
        self.assertEqual(self.run_fixture('class Required(unittest.TestCase):\n def test_required(self): self.assertEqual(2 + 2, 4)\n'), 1)
        with self.assertRaisesRegex(ValueError, 'empty or incomplete'):
            self.run_fixture('class Required(unittest.TestCase):\n def test_required(self): pass\n', minimum=2)


if __name__ == '__main__':
    unittest.main()
