"""Source-package identity and failure checks using tiny synthetic media."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_source_package import PackageFiles, verify, verify_studies


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class SourcePackageTests(unittest.TestCase):
    def replace_declared(self, root, name, raw):
        (root / name).write_bytes(raw)
        path = root / 'reviews/muscle/2026-10-24-bounded-migration/FILE-HASHES.json'
        checks = json.loads(path.read_bytes())
        checks[name] = {'bytes': len(raw), 'sha256': digest(raw)}
        path.write_text(json.dumps(checks))

    def fixture(self, root, package):
        review = f'reviews/{package}/2026-10-24-bounded-migration'
        source_name = 'sources/source.json'
        model_name = 'models/model.glb'
        image_name = review + '/evidence.webp'
        node = {'name': 'candidate', 'extras': {'source_object_name': 'native'}}
        chunk = json.dumps({'nodes': [node]}).encode()
        chunk += b' ' * (-len(chunk) % 4)
        model = struct.pack('<4sIIII', b'glTF', 2, 28 + len(chunk), len(chunk), 0x4e4f534a) + chunk + struct.pack('<II', 0, 0x004e4942)
        image = b'RIFF\x04\x00\x00\x00WEBP'
        source = {'selection': [{'sourceObjectName': 'native' if package == 'muscle' else 'candidate'}],
                  'externalHistoricalRecords': [], 'recipeDependencies': [],
                  'licenseReceipts': [{'bundled': False, 'sha256': '2' * 64}]}
        if package == 'muscle':
            source['sourceCollection'] = 'synthetic'
        evidence = {'path': image_name, 'sha256': digest(image), 'bytes': len(image),
                    'originalPNG': {'bundled': False, 'sha256': '3' * 64},
                    'selectionRole': 'candidate', 'assetBinding': digest(model)}
        record_name = review + '/bounded-record.json'
        record = {'evidence': [evidence], 'sourceDependencies': source_name,
                  'nodeIdentityMap': [{'index': 0, 'name': 'candidate',
                                       'sourceObjectName': 'native' if package == 'muscle' else None}]}
        manifest = {'reviewRecord': record_name, 'sourceMap': source_name, 'canonicalPath': model_name,
                    'transport': {'decodedBytes': len(model), 'decodedSha256': digest(model)},
                    'evidence': [evidence], 'uniqueMediaBytes': len(model) + len(image),
                    'uniqueMediaOids': 2, 'status': 'synthetic'}
        files = {source_name: json.dumps(source).encode(), model_name: model, image_name: image,
                 record_name: json.dumps(record).encode(),
                 review + '/transport-manifest.json': json.dumps(manifest).encode()}
        for name, raw in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        checks = {name: {'bytes': len(raw), 'sha256': digest(raw)} for name, raw in files.items()}
        (root / review / 'FILE-HASHES.json').write_text(json.dumps(checks))
        return source_name, model_name, image_name

    def test_package_clis_reject_retired_and_unknown_options(self):
        root = Path(__file__).resolve().parents[1]
        for folder in ('bp3d-head-studies', 'bp3d-body-studies', 'bp3d_bowels',
                       'joints', 'hra_lung', 'z_small_studies'):
            for option in ('--strict-package', '--unexpected'):
                with self.subTest(package=folder, option=option):
                    result = subprocess.run(
                        [sys.executable, str(root / 'tests' / folder / 'verify_bounded.py'), option],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('unrecognized arguments: ' + option, result.stderr)
                    self.assertNotIn('Traceback', result.stderr)

    def test_both_source_identity_schemes_and_unrelated_files(self):
        for package in ('muscle', 'breasts_hra'):
            with self.subTest(package=package), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.fixture(root, package)
                (root / 'unrelated.txt').write_text('not part of this package')
                self.assertEqual(verify(root, package)['identityChecks'], 'passed')

    def test_missing_or_corrupt_source_model_and_evidence_fail(self):
        for index in range(3):
            for corrupt in (False, True):
                with self.subTest(file=index, corrupt=corrupt), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    names = self.fixture(root, 'muscle')
                    path = root / names[index]
                    if corrupt:
                        path.write_bytes(b'corrupted retained bytes')
                    else:
                        path.unlink()
                    with self.assertRaisesRegex(ValueError, 'Missing package file|identity mismatch'):
                        verify(root, 'muscle')

    def test_changed_source_selection_fails_even_with_updated_file_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_name, _, _ = self.fixture(root, 'muscle')
            path = root / source_name
            source = json.loads(path.read_text())
            source['selection'][0]['sourceObjectName'] = 'different-source'
            raw = json.dumps(source).encode()
            path.write_bytes(raw)
            manifest = root / 'reviews/muscle/2026-10-24-bounded-migration/FILE-HASHES.json'
            checks = json.loads(manifest.read_text())
            checks[source_name] = {'bytes': len(raw), 'sha256': digest(raw)}
            manifest.write_text(json.dumps(checks))
            with self.assertRaisesRegex(ValueError, 'Source selection mismatch'):
                verify(root, 'muscle')

    def test_reads_recheck_bytes_and_contextual_expected_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, model, _ = self.fixture(root, 'muscle')
            files = PackageFiles(root, 'reviews/muscle/2026-10-24-bounded-migration/FILE-HASHES.json')
            raw = files.read(model)
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                files.read(model, {'sha256': '0' * 64, 'bytes': len(raw)})
            (root / model).write_bytes(b'X' + raw[1:])
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                files.read(model)
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                verify(root, 'muscle')

    def test_concurrent_roots_do_not_share_identities_or_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / name for name in ('first', 'second')]
            for number, root in enumerate(roots):
                source, _, _ = self.fixture(root, 'muscle')
                data = json.loads((root / source).read_bytes())
                data['syntheticRun'] = number
                self.replace_declared(root, source, json.dumps(data).encode())
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda root: verify(root, 'muscle'), roots))
            self.assertTrue(all(row['identityChecks'] == 'passed' for row in results))
            (roots[0] / source).write_bytes(b'corrupt')
            with ThreadPoolExecutor(max_workers=2) as pool:
                failed = pool.submit(verify, roots[0], 'muscle')
                passed = pool.submit(verify, roots[1], 'muscle')
                with self.assertRaises(ValueError):
                    failed.result()
                self.assertEqual(passed.result()['identityChecks'], 'passed')

    def test_paths_and_malformed_container_fail_even_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'checkout'
            _, model, _ = self.fixture(root, 'muscle')
            for name in ('../outside', '/absolute'):
                with self.assertRaisesRegex(ValueError, 'escapes checkout'):
                    PackageFiles(root, name)
            path = root / model
            original = path.read_bytes()
            path.unlink()
            target = root / 'target.glb'
            target.write_bytes(original)
            path.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                verify(root, 'muscle')
            path.unlink()
            malformed = b'not a GLB'
            self.replace_declared(root, model, malformed)
            manifest = 'reviews/muscle/2026-10-24-bounded-migration/transport-manifest.json'
            data = json.loads((root / manifest).read_bytes())
            data['transport'].update(decodedSha256=digest(malformed), decodedBytes=len(malformed))
            self.replace_declared(root, manifest, json.dumps(data).encode())
            with self.assertRaisesRegex(ValueError, 'Invalid GLB'):
                verify(root, 'muscle')

    def test_shared_study_accounting_and_package_callback_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, model, image = self.fixture(root, 'muscle')
            review = 'reviews/muscle/2026-10-24-bounded-migration'
            name = review + '/transport-manifest.json'
            data = json.loads((root / name).read_bytes())
            evidence = data['evidence']
            evidence[0]['format'] = 'WEBP'
            data['studies'] = [{'canonicalPath': model, 'transport': data['transport'], 'evidence': evidence}]
            self.replace_declared(root, name, json.dumps(data).encode())
            self.assertEqual(verify_studies(root, review)['uniqueMediaOids'], 2)
            def reject_source(files, study, document):
                raise ValueError('Package-specific source rejected')
            with self.assertRaisesRegex(ValueError, 'Package-specific source'):
                verify_studies(root, review, reject_source)
            data['uniqueMediaBytes'] += 1
            self.replace_declared(root, name, json.dumps(data).encode())
            with self.assertRaisesRegex(ValueError, 'Media accounting mismatch'):
                verify_studies(root, review)


if __name__ == '__main__':
    unittest.main()
