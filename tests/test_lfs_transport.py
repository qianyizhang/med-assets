"""Offline checks only: no network, credentials, uploads, or repository mutations."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('lfs_transport', Path(__file__).parents[1] / 'tools/lfs_transport.py')
t = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t)
GLB = b'glTF' + struct.pack('<II', 2, 24) + struct.pack('<I4s', 4, b'JSON') + b'{}  '
OID = hashlib.sha256(GLB).hexdigest()
OBJ = {'file': 'models/test.glb', 'sha256': OID, 'bytes': len(GLB),
       'url': f'https://{t.SOURCE_HOST}/review/candidates/test/{OID}.glb'}
MANIFEST = {'objects': [OBJ], 'totalBytes': len(GLB)}


def encode(m):
    raw = json.dumps(m).encode()
    return raw, hashlib.sha256(raw).hexdigest()


class Validation(unittest.TestCase):
    def invalid(self, mutate):
        m = copy.deepcopy(MANIFEST)
        mutate(m)
        with self.assertRaises(t.Stop):
            t.validate_manifest(*encode(m))

    def test_valid_identity_and_gzip(self):
        self.assertEqual(t.validate_manifest(*encode(MANIFEST)), MANIFEST)
        m = copy.deepcopy(MANIFEST)
        compressed = gzip.compress(GLB)
        m['objects'][0].update(encoding='gzip', transportBytes=len(compressed), transportSha256=hashlib.sha256(compressed).hexdigest())
        t.validate_manifest(*encode(m))
        with patch.object(t, 'http_bytes', return_value=compressed):
            self.assertEqual(t.download_source(m['objects'][0]), GLB)

    def test_manifest_hash_and_size(self):
        raw, digest = encode(MANIFEST)
        for data, sha in [(raw + b' ', digest), (raw, '../escape'), (b' ' * (t.MAX_MANIFEST + 1), digest)]:
            with self.subTest(sha=sha), self.assertRaises(t.Stop):
                t.validate_manifest(data, sha)

    def test_duplicate_json_key(self):
        raw = b'{"objects":[],"objects":[],"totalBytes":1}'
        with self.assertRaises(t.Stop):
            t.validate_manifest(raw, hashlib.sha256(raw).hexdigest())

    def test_unknown_fields(self):
        self.invalid(lambda m: m.update(command='run something'))
        self.invalid(lambda m: m['objects'][0].update(token='not accepted'))

    def test_count_limits_and_duplicates(self):
        self.invalid(lambda m: m.update(objects=[]))
        self.invalid(lambda m: m.update(objects=[OBJ] * (t.MAX_OBJECTS + 1)))
        self.invalid(lambda m: m.update(objects=[OBJ, OBJ], totalBytes=48))
        self.invalid(lambda m: m.update(objectCount=2))

    def test_byte_limits_and_bool(self):
        for value in (True, 0, -1, t.MAX_OBJECT + 1, '24'):
            self.invalid(lambda m, value=value: m['objects'][0].update(bytes=value))
        self.invalid(lambda m: m.update(totalBytes=t.MAX_TOTAL + 1))
        self.invalid(lambda m: m.update(totalBytes=25))

    def test_40mb_raw_object_and_batch_boundaries(self):
        # Schema-only sizes: no large payload allocation or network.
        self.assertEqual((t.MAX_OBJECT, t.MAX_TOTAL), (40_000_000, 40_000_000))
        m = {'objects': [dict(OBJ, bytes=40_000_000)], 'totalBytes': 40_000_000}
        t.validate_manifest(*encode(m))
        m['objects'][0]['bytes'] += 1
        with self.assertRaisesRegex(t.Stop, 'Object outside fixed cap'):
            t.validate_manifest(*encode(m))
        m = {'objects': [dict(OBJ, bytes=20_000_000),
                         dict(OBJ, sha256='2' * 64, bytes=20_000_000)], 'totalBytes': 40_000_000}
        t.validate_manifest(*encode(m))
        m['objects'][1]['bytes'] += 1
        m['totalBytes'] += 1
        with self.assertRaisesRegex(t.Stop, 'Total outside fixed cap'):
            t.validate_manifest(*encode(m))

    def test_40mb_gzip_transport_boundaries(self):
        o = dict(OBJ, encoding='gzip', transportBytes=40_000_000, transportSha256='3' * 64)
        m = {'objects': [o], 'totalBytes': len(GLB)}
        t.validate_manifest(*encode(m))
        o['transportBytes'] += 1
        with self.assertRaisesRegex(t.Stop, 'Gzip transport outside fixed cap'):
            t.validate_manifest(*encode(m))
        o['transportBytes'] = 20_000_000
        m['objects'].append(dict(o, sha256='2' * 64, transportSha256='4' * 64))
        m['totalBytes'] = 2 * len(GLB)
        t.validate_manifest(*encode(m))
        m['objects'][1]['transportBytes'] += 1
        with self.assertRaisesRegex(t.Stop, 'Aggregate transport cap exceeded'):
            t.validate_manifest(*encode(m))

    def test_oid_and_file(self):
        self.invalid(lambda m: m['objects'][0].update(sha256='X' * 64))
        for name in ('../x.glb', '/x.glb', 'x/../x.glb', 'x\\x.glb', 'x.py', 'x\nx.glb'):
            self.invalid(lambda m, name=name: m['objects'][0].update(file=name))

    def test_host_and_url_guards(self):
        for url in ('http://' + t.SOURCE_HOST + '/review/x.glb',
                    'https://evil.example/review/x.glb',
                    'https://' + t.SOURCE_HOST + '.evil.example/review/x.glb',
                    'https://user:pass@' + t.SOURCE_HOST + '/review/x.glb',
                    'https://' + t.SOURCE_HOST + ':444/review/x.glb',
                    'https://' + t.SOURCE_HOST + '/review/../x.glb',
                    'https://' + t.SOURCE_HOST + '/review/%2e%2e/x.glb',
                    'https://' + t.SOURCE_HOST + '/review/x.glb?token=x',
                    'https://' + t.SOURCE_HOST + '/elsewhere/x.glb'):
            self.invalid(lambda m, url=url: m['objects'][0].update(url=url))

    def test_encoding_guards(self):
        self.invalid(lambda m: m['objects'][0].update(encoding='zip'))
        self.invalid(lambda m: m['objects'][0].update(encoding='gzip'))
        self.invalid(lambda m: m['objects'][0].update(transportBytes=24))

    def test_bounded_gzip_and_bad_transport_hash(self):
        o = copy.deepcopy(OBJ)
        data = gzip.compress(GLB + b'oversized')
        o.update(encoding='gzip', transportBytes=len(data), transportSha256=hashlib.sha256(data).hexdigest())
        with patch.object(t, 'http_bytes', return_value=data), self.assertRaises(t.Stop):
            t.download_source(o)
        o['transportSha256'] = '0' * 64
        with patch.object(t, 'http_bytes', return_value=data), self.assertRaises(t.Stop):
            t.download_source(o)

    def test_header_and_exact_bytes(self):
        t.verify_bytes(GLB, OBJ)
        for data in (GLB + b'x', b'wrong', b'x' * len(GLB)):
            with self.assertRaises(t.Stop):
                t.verify_bytes(data, OBJ)
        malformed = b'glTF' + struct.pack('<II', 1, 24) + GLB[12:]
        o = dict(OBJ, sha256=hashlib.sha256(malformed).hexdigest())
        with self.assertRaises(t.Stop):
            t.verify_bytes(malformed, o)

    def test_png_webp_headers(self):
        png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + struct.pack('>II', 2, 3)
        webp = b'RIFF' + struct.pack('<I', 4) + b'WEBP'
        for suffix, data in [('png', png), ('webp', webp)]:
            o = dict(OBJ, file='reviews/test.' + suffix, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            t.verify_bytes(data, o)

    def test_aggregate_transport_cap(self):
        m = {'objects': [dict(OBJ, bytes=15_000_000, encoding='gzip', transportBytes=25_000_000,
                              transportSha256='3' * 64),
                         dict(OBJ, sha256='2' * 64, bytes=15_000_000, encoding='gzip',
                              transportBytes=25_000_000, transportSha256='4' * 64)], 'totalBytes':30_000_000}
        with self.assertRaises(t.Stop):
            t.validate_manifest(*encode(m))

    def test_manifest_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, digest = encode(MANIFEST)
            (root / 'transport/manifests').mkdir(parents=True)
            (root / 'outside').write_bytes(raw)
            (root / 'transport/manifests' / (digest + '.json')).symlink_to(root / 'outside')
            with self.assertRaises(t.Stop):
                t.load_manifest(root, digest)


class TriggerAndExecution(unittest.TestCase):
    def setUp(self):
        quiet = patch('builtins.print')
        quiet.start()
        self.addCleanup(quiet.stop)
        self.env = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': t.REPOSITORY, 'GITHUB_REF': 'refs/heads/main',
                    'GITHUB_SHA': '1' * 40, 'GITHUB_EVENT_NAME': 'push', 'PUSH_BEFORE': '2' * 40}
        self.digest = encode(MANIFEST)[1]

    def select(self, diff, env=None):
        with patch.object(t, 'git', side_effect=[b'1' * 40 + b'\n', diff.encode()]):
            return t.select_run_manifest(Path('.'), env or self.env)

    def test_single_new_manifest(self):
        self.assertEqual(self.select('A\ttransport/manifests/' + self.digest + '.json\n'), self.digest)

    def test_modified_deleted_multiple_mixed_or_bad_name(self):
        path = 'transport/manifests/' + self.digest + '.json'
        for diff in ('M\t' + path, 'D\t' + path, 'A\t' + path + '\nA\tother.json',
                     'A\t' + path + '\nM\ttools/lfs_transport.py', 'A\ttransport/manifests/free-form.json', ''):
            with self.subTest(diff=diff), self.assertRaises(t.Stop):
                self.select(diff)

    def test_untrusted_execution_contexts(self):
        for key, value in [('GITHUB_REPOSITORY', 'evil/fork'), ('GITHUB_REF', 'refs/pull/1/merge'),
                           ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_ACTIONS', 'false'), ('PUSH_BEFORE', '0' * 40)]:
            env = dict(self.env, **{key: value})
            with self.assertRaises(t.Stop):
                self.select('A\ttransport/manifests/' + self.digest + '.json', env)

    def test_manual_digest(self):
        env = dict(self.env, GITHUB_EVENT_NAME='workflow_dispatch', MANIFEST_SHA256=self.digest)
        self.assertEqual(self.select('', env), self.digest)
        env['MANIFEST_SHA256'] = '../../escape'
        with self.assertRaises(t.Stop):
            self.select('', env)

    def test_no_upload_if_any_source_fails(self):
        other = dict(OBJ, sha256='2' * 64)
        with tempfile.TemporaryDirectory() as tmp, patch.object(t, 'download_source', side_effect=[GLB, t.Stop('bad source')]), \
             patch.object(t, 'git') as git, patch.object(t, 'batch') as batch:
            with self.assertRaises(t.Stop):
                t.upload_and_readback(Path('.'), {'objects': [OBJ, other]}, Path(tmp))
            git.assert_not_called()
            batch.assert_not_called()

    def test_only_missing_uploads_then_readback(self):
        existing = dict(OBJ, sha256='2' * 64)
        remote = {OID: {'error': {'code': 404}}, existing['sha256']: {'actions': {'download': {}}}}
        calls = []
        def git(root, *args, data=None, storage=None):
            calls.append(args)
            if args[0] == 'remote':
                return ('https://github.com/' + t.REPOSITORY).encode()
            if args[:2] == ('lfs', 'clean'):
                oid = args[2].removeprefix('approved-')
                return f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize 24\n'.encode()
            return b''
        with tempfile.TemporaryDirectory() as tmp, patch.object(t, 'download_source', return_value=GLB), \
             patch.object(t, 'batch', return_value=remote), patch.object(t, 'git', side_effect=git), \
             patch.object(t, 'readback', return_value=[{'verified': True}]) as readback:
            result = t.upload_and_readback(Path('.'), {'objects': [OBJ, existing]}, Path(tmp))
        self.assertEqual([x for x in calls if x[:2] == ('lfs', 'push')], [('lfs', 'push', '--object-id', 'origin', OID)])
        self.assertEqual(result['uploadedObjects'], 1)
        self.assertEqual(result['existingObjectsSkipped'], 1)
        readback.assert_called_once()

    def test_quota_error_not_treated_as_missing(self):
        for code in (403, 429, 500):
            with self.assertRaises(t.Stop):
                t.missing_objects([OBJ], {OID: {'error': {'code': code}}})

    def test_redirects_do_not_leak_headers_to_other_origins(self):
        request = t.urllib.request.Request('https://github-cloud.s3.amazonaws.com/object', headers={'Authorization': 'dummy'})
        with self.assertRaises(t.Stop):
            t.SameOriginRedirect().redirect_request(request, None, 302, '', {}, 'https://evil.example/object')

    def test_response_cap_and_http_error_redaction(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'x' * limit
        with patch.object(t.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = Response()
            with self.assertRaises(t.Stop):
                t.http_bytes('https://example.com/object', 24)
            opener.return_value.open.side_effect = t.urllib.error.HTTPError('https://example.com/?secret=DO_NOT_LOG', 403, 'DO_NOT_LOG', {}, None)
            with self.assertRaises(t.Stop) as error:
                t.http_bytes('https://example.com/object', 24)
            self.assertNotIn('DO_NOT_LOG', str(error.exception))


if __name__ == '__main__':
    unittest.main()
