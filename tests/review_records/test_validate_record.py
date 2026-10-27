"""Synthetic text fixtures test the validator, not any medical model."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from validate_record import reference, validate

class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'artifact.txt').write_bytes(b'synthetic test artifact')
        (self.root / 'evidence.txt').write_bytes(b'synthetic test evidence')
        def ref(name):
            return {'file': name, 'sha256': hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
        artifact = ref('artifact.txt')
        self.record = {'schemaVersion': 1, 'id': 'synthetic', 'assetId': 'synthetic',
                       'variantId': 'synthetic', 'reviewedAt': '2026-10-23T00:00:00Z',
                       'artifact': artifact,
                       'gates': {k: {'status': 'unreviewed', 'scope': 'Synthetic fixture only'}
                                 for k in ('technical','visual','anatomy','runtime')},
                       'evidence': [dict(ref('evidence.txt'), artifactSha256=artifact['sha256'], kind='synthetic')],
                       'failureSummary': {k: 'Synthetic fixture only' for k in ('failure','cause','fix','retest','lesson')},
                       'limitations': ['No real asset or quality claim']}

    def test_valid_contract(self):
        self.assertEqual(validate(self.record, self.root)['result'], 'passed')

    def test_bad_hash(self):
        self.record['artifact']['sha256'] = '0'*64
        with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_traversal(self):
        self.record['artifact']['file'] = '../artifact.txt'
        with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_unbound_evidence(self):
        self.record['evidence'][0]['artifactSha256'] = '0'*64
        with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_missing_independent_gate(self):
        del self.record['gates']['runtime']
        with self.assertRaises(KeyError): validate(self.record, self.root)

    def test_lfs_pointer_not_payload(self):
        data = b'version https://git-lfs.github.com/spec/v1\noid sha256:' + b'0'*64 + b'\nsize 1\n'
        (self.root/'artifact.txt').write_bytes(data)
        self.record['artifact']['sha256'] = hashlib.sha256(data).hexdigest()
        with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as other:
            p = Path(other)/'outside.txt'; p.write_bytes(b'outside')
            (self.root/'link.txt').symlink_to(p)
            self.record['artifact'] = {'file':'link.txt','sha256':hashlib.sha256(b'outside').hexdigest()}
            with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_timezone_required(self):
        self.record['reviewedAt'] = '2026-10-23T00:00:00'
        with self.assertRaises(ValueError): validate(self.record, self.root)

    def test_symlink_root_accepts_internal_reference(self):
        with tempfile.TemporaryDirectory() as other:
            alias = Path(other) / 'root'
            alias.symlink_to(self.root.resolve(), target_is_directory=True)
            path, digest = reference(alias, self.record['artifact'])
            self.assertEqual(path, (self.root / 'artifact.txt').resolve())
            self.assertEqual(digest, self.record['artifact']['sha256'])

    def test_symlink_root_still_rejects_escape(self):
        with tempfile.TemporaryDirectory() as other:
            alias = Path(other) / 'root'
            alias.symlink_to(self.root.resolve(), target_is_directory=True)
            outside = Path(other) / 'outside.txt'
            outside.write_bytes(b'outside')
            (self.root / 'escape.txt').symlink_to(outside.resolve())
            entry = {'file': 'escape.txt', 'sha256': hashlib.sha256(b'outside').hexdigest()}
            with self.assertRaisesRegex(ValueError, 'escapes repository'):
                reference(alias, entry)

if __name__ == '__main__': unittest.main()
