"""Offline backup checker safety and behavior, using synthetic bytes only."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import backup_check as b


class BackupCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.backup = Path(self.temp.name) / 'backup'
        self.backup.mkdir()
        self.payload = b'synthetic payload\0' * 80000
        digest = hashlib.sha256(self.payload).hexdigest()
        self.pointer = (f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\n'
                        f'size {len(self.payload)}\n').encode()
        self.contents = {'.gitattributes': b'*.bin filter=lfs -text\n',
                         'README.md': b'ordinary text mentions oid sha256: literally\n',
                         'nested/asset.bin': self.pointer, 'other.bin': self.pointer,
                         'run.sh': b'#!/bin/sh\nexit 0\n'}
        self.command('init', '-q')
        for name, data in self.contents.items():
            self.stage(name, data, '100755' if name == 'run.sh' else '100644')
        self.commit = self.commit_index()
        self.inventory = b.expected_tree(self.root, self.commit)
        for name, data in self.contents.items():
            path = self.backup / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.payload if name.endswith('.bin') else data)

    def test_tools_only_commands_do_not_require_review_test_tree(self):
        tools = self.root / 'standalone-tools'
        tools.mkdir()
        for name in ('backup_check.py', 'backup_transfer.py', 'lfs_transport.py'):
            (tools / name).write_bytes((Path(b.__file__).parent / name).read_bytes())
        for name in ('backup_check.py', 'backup_transfer.py'):
            with self.subTest(command=name):
                result = subprocess.run([sys.executable, str(tools / name), '--help'],
                                        capture_output=True, text=True, cwd=self.root)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('usage:', result.stdout)

    def command(self, *args, data=None):
        return subprocess.run(['git', *args], cwd=self.root, input=data,
                              env=dict(os.environ, GIT_AUTHOR_NAME='Fixture',
                                       GIT_AUTHOR_EMAIL='fixture@example.invalid',
                                       GIT_COMMITTER_NAME='Fixture',
                                       GIT_COMMITTER_EMAIL='fixture@example.invalid'),
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def stage(self, name, data, mode='100644'):
        oid = self.command('hash-object', '-w', '--stdin', data=data).decode().strip()
        self.command('update-index', '--add', '--cacheinfo', mode, oid, name)

    def commit_index(self):
        tree = self.command('write-tree').decode().strip()
        return self.command('commit-tree', tree, data=b'fixture\n').decode().strip()

    def check(self):
        return b.check(self.inventory, b.Tree(self.backup))

    def status(self, path):
        return {row['path']: row['status'] for row in self.check()['files']}[path]

    def test_exact_commit_and_duplicate_lfs_objects(self):
        self.assertEqual(self.inventory['commit'], self.commit)
        self.assertEqual(self.inventory['lfsPathCount'], 2)
        self.assertEqual(self.inventory['lfsUniqueObjectCount'], 1)
        self.assertEqual(self.inventory['lfsUniqueObjectBytes'], len(self.payload))
        self.assertEqual(len(self.inventory['files']), 5)
        self.assertTrue(self.check()['completeCurrentTree'])
        self.assertEqual(self.check()['plannedCopyBytes'], 0)

    def test_working_tree_index_and_attributes_cannot_change_expectations(self):
        (self.root / '.gitattributes').write_text('* filter=lfs\n')
        (self.root / 'README.md').write_text('dirty\n')
        self.stage('nested/asset.bin', b'broken staged pointer')
        self.stage('.gitattributes', b'* filter=lfs\n')
        self.assertEqual(b.expected_tree(self.root, self.commit), self.inventory)

    def test_missing_text_is_a_gap_even_when_all_media_match(self):
        (self.backup / 'README.md').unlink()
        result = self.check()
        self.assertFalse(result['completeCurrentTree'])
        self.assertEqual(result['counts'], {'verified': 4, 'missing': 1})
        row = next(r for r in result['files'] if r['path'] == 'README.md')
        self.assertEqual(row['action'], 'needs_copy')
        self.assertEqual(result['plannedCopyBytes'], len(self.contents['README.md']))

    def test_pointer_only_and_malformed_pointer_never_pass(self):
        for data in (self.pointer, self.pointer.replace(b'size ', b'malformed ')):
            (self.backup / 'other.bin').write_bytes(data)
            self.assertEqual(self.status('other.bin'), 'pointer_only')
            self.assertFalse(self.check()['completeCurrentTree'])

    def test_same_size_corruption_beyond_prefix_and_size_mismatch(self):
        damaged = bytearray(self.payload)
        damaged[100000] ^= 1
        for data in (damaged, self.payload[:-1], self.payload + b'x'):
            (self.backup / 'other.bin').write_bytes(data)
            self.assertEqual(self.status('other.bin'), 'mismatched')

    def test_missing_parent_and_nonregular_file(self):
        (self.backup / 'nested/asset.bin').unlink()
        (self.backup / 'nested').rmdir()
        self.assertEqual(self.status('nested/asset.bin'), 'missing')
        (self.backup / 'other.bin').unlink()
        os.mkfifo(self.backup / 'other.bin')
        self.assertEqual(self.status('other.bin'), 'unverifiable')

    def test_file_and_parent_symlinks_are_unverifiable(self):
        (self.backup / 'other.bin').unlink()
        (self.backup / 'other.bin').symlink_to(self.backup / 'nested/asset.bin')
        self.assertEqual(self.status('other.bin'), 'unverifiable')
        (self.backup / 'nested/asset.bin').unlink()
        (self.backup / 'nested').rmdir()
        (self.backup / 'nested').symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.status('nested/asset.bin'), 'unverifiable')

    def zip_bytes(self, extra=()):
        data = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
                for path in self.backup.rglob('*'):
                    if path.is_file():
                        archive.write(path, path.relative_to(self.backup).as_posix())
                for name, payload in extra:
                    archive.writestr(name, payload)
        data.seek(0)
        return data

    def test_zip_reads_actual_bytes_without_extracting(self):
        before = sorted(str(p) for p in Path(self.temp.name).rglob('*'))
        with zipfile.ZipFile(self.zip_bytes()) as archive:
            result = b.check(self.inventory, b.Zip(archive))
        self.assertTrue(result['completeCurrentTree'])
        self.assertEqual(before, sorted(str(p) for p in Path(self.temp.name).rglob('*')))

    def test_zip_pointer_corruption_and_root_prefix_fail(self):
        (self.backup / 'other.bin').write_bytes(self.pointer)
        (self.backup / 'README.md').write_bytes(b'corrupted')
        with zipfile.ZipFile(self.zip_bytes()) as archive:
            result = b.check(self.inventory, b.Zip(archive))
        statuses = {r['path']: r['status'] for r in result['files']}
        self.assertEqual(statuses['other.bin'], 'pointer_only')
        self.assertEqual(statuses['README.md'], 'mismatched')
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('prefix/README.md', self.contents['README.md'])
        with zipfile.ZipFile(data) as archive:
            self.assertEqual(b.check(self.inventory, b.Zip(archive))['counts'], {'missing': 5})

    def test_zip_traversal_absolute_alias_and_duplicate_refused(self):
        for name in ('../escape', '/absolute', 'a/../b', 'a//b', 'a\\b', 'C:/b',
                     './alias', 'README.md'):
            with self.subTest(name=name), zipfile.ZipFile(self.zip_bytes([(name, b'x')])) as archive:
                with self.assertRaises(ValueError):
                    b.Zip(archive)

    def test_zip_symlink_and_bad_crc_unverifiable(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            entry = zipfile.ZipInfo('other.bin')
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(entry, 'target')
        with zipfile.ZipFile(data) as archive:
            expected = next(r for r in self.inventory['files'] if r['path'] == 'other.bin')
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w') as archive:
            archive.writestr('README.md', self.contents['README.md'])
        damaged = raw.getvalue().replace(self.contents['README.md'], b'X' * len(self.contents['README.md']), 1)
        with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
            expected = next(r for r in self.inventory['files'] if r['path'] == 'README.md')
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')
        compressed = io.BytesIO()
        with zipfile.ZipFile(compressed, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('README.md', self.contents['README.md'])
        damaged = bytearray(compressed.getvalue())
        name_length, extra_length = struct.unpack_from('<HH', damaged, 26)
        offset = 30 + name_length + extra_length
        damaged[offset] = (damaged[offset] & ~7) | 7  # Invalid DEFLATE block type.
        with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')

    def test_commit_id_required_and_unsupported_git_entries_fail(self):
        for revision in ('HEAD', 'main', self.commit[:7], '-' + self.commit):
            with self.assertRaises(ValueError):
                b.expected_tree(self.root, revision)
        self.stage('link', b'README.md', '120000')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            b.expected_tree(self.root, self.commit_index())

    def test_malformed_committed_lfs_pointer_fails_closed(self):
        for data in (self.pointer.replace(b'size ', b'broken '), b'not a pointer'):
            self.stage('other.bin', data)
            with self.assertRaisesRegex(ValueError, 'Malformed LFS pointer'):
                b.expected_tree(self.root, self.commit_index())

    def test_local_attribute_override_refused(self):
        (self.root / '.git/info/attributes').write_text('* filter=other\n')
        with self.assertRaisesRegex(ValueError, 'override'):
            b.expected_tree(self.root, self.commit)

    def test_every_git_process_denies_fetch_even_with_permissive_environment(self):
        with patch.dict(os.environ, GIT_ALLOW_PROTOCOL='https:file', GIT_NO_LAZY_FETCH='0'):
            with patch.object(b.subprocess, 'Popen', wraps=subprocess.Popen) as processes:
                self.assertEqual(b.expected_tree(self.root, self.commit), self.inventory)
        self.assertGreaterEqual(len(processes.call_args_list), 5)
        for call in processes.call_args_list:
            self.assertIn('--no-lazy-fetch', call.args[0])
            self.assertEqual(call.kwargs['env']['GIT_ALLOW_PROTOCOL'], '')
            self.assertEqual(call.kwargs['env']['GIT_NO_LAZY_FETCH'], '1')

    def test_older_git_rejects_option_before_any_object_read_or_fetch(self):
        fake_bin = Path(self.temp.name) / 'fake-bin'
        fake_bin.mkdir()
        marker = fake_bin / 'unsafe-object-read'
        executable = fake_bin / 'git'
        executable.write_text(
            '#!' + sys.executable + '\nimport pathlib,sys\n'
            'if "--no-lazy-fetch" in sys.argv:\n'
            '    sys.stderr.write("unknown option: --no-lazy-fetch\\n")\n'
            '    sys.exit(129)\n'
            'pathlib.Path(__file__).with_name("unsafe-object-read").touch()\n'
            'sys.exit(1)\n')
        executable.chmod(0o700)
        args = ['--repo', str(self.root), '--commit', self.commit, '--inventory']
        with patch.dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ['PATH']):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(b.main(args), 2)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(marker.exists())

    def test_missing_promisor_blob_does_not_start_remote_helper(self):
        helper_dir = Path(self.temp.name) / 'remote-helper'
        helper_dir.mkdir()
        marker = helper_dir / 'invoked'
        helper = helper_dir / 'git-remote-backup-test'
        helper.write_text('#!' + sys.executable + '\nimport pathlib,sys\n'
                          'pathlib.Path(__file__).with_name("invoked").touch()\n'
                          'sys.exit(1)\n')
        helper.chmod(0o700)
        self.command('config', 'remote.origin.url', 'backup-test::offline')
        self.command('config', 'remote.origin.promisor', 'true')
        self.command('config', 'protocol.backup-test.allow', 'always')
        oid = self.command('rev-parse', self.commit + ':README.md').decode().strip()
        (self.root / '.git/objects' / oid[:2] / oid[2:]).unlink()
        with patch.dict(os.environ, PATH=str(helper_dir) + os.pathsep + os.environ['PATH']):
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                b.expected_tree(self.root, self.commit)
        self.assertFalse(marker.exists())

    def test_cli_inventory_pass_gap_and_error_exit_codes(self):
        base = ['--repo', str(self.root), '--commit', self.commit]
        for args, code in ((['--inventory'], 0), (['--backup-tree', str(self.backup)], 0)):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(b.main(base + args), code)
            self.assertEqual(json.loads(out.getvalue())['commit'], self.commit)
        (self.backup / 'README.md').unlink()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(b.main(base + ['--backup-tree', str(self.backup)]), 1)
        self.assertFalse(json.loads(out.getvalue())['completeCurrentTree'])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(b.main(base + ['--backup-zip', str(self.backup / 'absent.zip')]), 2)


class CurrentMirrorPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'current.json'
        self.commit = 'a' * 40
        self.payloads = {'a.bin': b'alpha', 'duplicate.bin': b'alpha',
                         'new.bin': b'bravo!', 'note.txt': b'new note'}
        self.inventory = {'commit': self.commit, 'files': [
            {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
             'kind': 'lfs' if path.endswith('.bin') else 'git'}
            for path, data in self.payloads.items()]}

    def row(self, path, data=b'alpha', remote_id='fixture_alpha', status='verified', staged=False):
        sha = hashlib.sha256(data).hexdigest()
        row = {'path': path, 'sha256': sha, 'size': len(data),
               'remote': {'fileId': remote_id, 'version': 'fixture_version_1',
                          'sha256': sha if status == 'verified' else None, 'size': len(data)},
               'verification': {'status': status, 'method': 'none' if status == 'unverified'
                                else 'sha256-size-readback',
                                'at': None if status == 'unverified' else '2020-01-02T03:04:05Z'}}
        if staged:
            row['forCommit'] = self.commit
        return row

    def document(self, files=(), staged=()):
        return {'schemaVersion': 1, 'revision': 3, 'commit': 'b' * 40 if files else None,
                'files': list(files), 'staged': list(staged)}

    def load(self, document):
        raw = (json.dumps(document, indent=2) + '\n').encode()
        self.path.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        return b.load_current_manifest(self.path, digest), digest

    def plan(self, files=(), staged=()):
        manifest, digest = self.load(self.document(files, staged))
        return b.incremental_plan(self.inventory, manifest, digest)

    def test_empty_mirror_plans_only_unique_payloads_and_bounded_staging(self):
        result = self.plan()
        budget = result['budget']
        self.assertEqual((budget['trackedFiles'], budget['uniquePayloadFiles']), (4, 3))
        self.assertEqual((budget['trackedPathBytes'], budget['desiredUniqueBytes']), (24, 19))
        self.assertEqual((budget['uploadFiles'], budget['uploadBytes']), (3, 19))
        self.assertEqual(budget['additionalStagingPeakBytes'], 8)
        self.assertEqual(budget['initialStepTotalPeakBytes'], 8)
        self.assertFalse(result['remoteCoverageVerified'])
        self.assertNotIn('completeCurrentTree', result)

    def test_unchanged_content_deduplicates_paths_and_never_asserts_remote_freshness(self):
        files = [self.row(path, data, remote_id='fixture_' + hashlib.sha256(data).hexdigest()[:8])
                 for path, data in self.payloads.items()]
        result = self.plan(files)
        self.assertEqual(result['budget']['uploadBytes'], 0)
        self.assertEqual(result['budget']['reuseCandidateFiles'], 3)
        self.assertEqual(result['budget']['existingCurrentBytes'], 19)
        self.assertEqual(result['budget']['uploadBytesIfAllCandidatesFail'], 19)
        alpha = next(r for r in result['objects'] if r['size'] == 5)
        self.assertEqual(alpha['paths'], ['a.bin', 'duplicate.bin'])
        self.assertTrue(all(r['needsRemoteValidation'] for r in result['objects']))
        self.assertFalse(result['remoteManifestFreshnessChecked'])
        self.assertFalse(result['atomicRemoteCAS'])
        self.assertEqual(alpha['candidates'][0]['verification']['at'], '2020-01-02T03:04:05Z')

    def test_changed_and_missing_payloads_have_exact_upload_and_storage_budgets(self):
        old = self.row('a.bin', b'older data', 'fixture_old')
        result = self.plan([old])
        self.assertEqual(result['budget']['uploadBytes'], 19)
        self.assertEqual(result['budget']['existingCurrentBytes'], 10)
        self.assertEqual(result['budget']['initialStepTotalPeakBytes'], 18)
        self.assertEqual(result['replacementCandidates'], [old])
        self.assertEqual({r['reason'] for r in result['objects']}, {'changed', 'missing'})

    def test_renamed_payload_reuses_content_without_authorizing_retirement(self):
        old = self.row('old-name.bin')
        result = self.plan([old])
        self.assertEqual(result['obsoleteCandidates'], [old])
        alpha = next(r for r in result['objects'] if r['size'] == 5)
        self.assertEqual(alpha['action'], 'reuse_candidate')
        self.assertEqual(alpha['candidates'][0]['remote']['fileId'], old['remote']['fileId'])
        self.assertEqual(result['budget']['uploadBytes'], 14)
        self.assertFalse(any(r['action'] in ('delete', 'replace') for r in result['objects']))

    def test_unverified_current_identity_needs_readback_before_reuse(self):
        result = self.plan([self.row('a.bin', status='unverified')])
        self.assertEqual(result['budget']['verifyCandidateBytes'], 5)
        self.assertEqual(result['budget']['reuseCandidateFiles'], 0)
        self.assertEqual(result['budget']['uploadBytes'], 14)
        self.assertFalse(result['remoteCoverageVerified'])

    def test_interrupted_upload_stays_separate_from_accepted_current_state(self):
        old = self.row('a.bin', b'older data', 'fixture_old')
        staged = self.row('a.bin', remote_id='fixture_staged', status='unverified', staged=True)
        result = self.plan([old], [staged])
        self.assertEqual(result['budget']['uploadBytes'], 14)
        self.assertEqual(result['budget']['existingStagedBytes'], 5)
        self.assertEqual(result['budget']['temporaryStagingPeakBytes'], 13)
        self.assertEqual(result['budget']['initialStepTotalPeakBytes'], 23)
        self.assertEqual(result['stagedReviewCandidates'], [staged])
        alpha = next(r for r in result['objects'] if r['size'] == 5)
        self.assertEqual(alpha['action'], 'verify_candidate')
        self.assertEqual(alpha['candidates'][0]['forCommit'], self.commit)

    def test_verified_staged_file_is_not_automatically_adopted_as_current(self):
        result = self.plan(staged=[self.row('a.bin', staged=True)])
        self.assertEqual(result['budget']['verifyCandidateFiles'], 1)
        self.assertEqual(result['budget']['reuseCandidateFiles'], 0)
        self.assertEqual(result['budget']['existingCurrentBytes'], 0)
        self.assertEqual(result['budget']['existingStagedBytes'], 5)

    def test_failed_or_mismatched_staging_cannot_suppress_a_planned_upload(self):
        for status in ('failed', 'unverified'):
            row = self.row('a.bin', status=status, staged=True)
            if status == 'unverified':
                row['remote']['sha256'] = 'f' * 64
            result = self.plan(staged=[row])
            self.assertEqual(result['budget']['uploadBytes'], 19)
            self.assertEqual(result['budget']['verifyCandidateFiles'], 0)
            self.assertEqual(result['stagedReviewCandidates'], [row])

    def test_failed_current_content_is_a_replacement_candidate(self):
        row = self.row('a.bin', status='failed')
        result = self.plan([row])
        self.assertEqual(result['budget']['uploadBytes'], 19)
        self.assertEqual(result['replacementCandidates'], [row])
        alpha = next(r for r in result['objects'] if r['size'] == 5)
        self.assertEqual(alpha['reason'], 'unusable_current')

    def test_stale_checkpoint_and_tampered_bytes_fail_closed(self):
        _, digest = self.load(self.document())
        with self.assertRaisesRegex(ValueError, 'Stale or changed'):
            b.load_current_manifest(self.path, '0' * 64)
        self.path.write_bytes(self.path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Stale or changed'):
            b.load_current_manifest(self.path, digest)
        for missing in (None, 'HEAD', 'A' * 64):
            with self.assertRaises(ValueError):
                b.load_current_manifest(self.path, missing)

    def test_exact_schema_and_validated_types(self):
        mutations = [lambda d: d.update(history=[]), lambda d: d.update(revision=True),
                     lambda d: d.update(schemaVersion=True), lambda d: d.update(commit=None),
                     lambda d: d['files'][0].update(size=True),
                     lambda d: d['files'][0].update(size=-1),
                     lambda d: d['files'][0]['remote'].update(version=''),
                     lambda d: d['files'][0]['remote'].update(fileId='https://example.invalid'),
                     lambda d: d['files'][0]['remote'].update(extra='not accepted'),
                     lambda d: d['files'][0]['verification'].update(method='metadata-only'),
                     lambda d: d['files'][0]['verification'].update(at='2026-02-30T00:00:00Z'),
                     lambda d: d['files'][0]['verification'].update(status='complete'),
                     lambda d: d['files'][0]['remote'].update(sha256='f' * 64)]
        for mutate in mutations:
            document = self.document([self.row('a.bin')])
            mutate(document)
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.load(document)

    def test_duplicate_json_keys_are_rejected_even_with_matching_raw_digest(self):
        raw = b'{"schemaVersion":1,"revision":1,"revision":2,"commit":null,"files":[],"staged":[]}'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            b.load_current_manifest(self.path, hashlib.sha256(raw).hexdigest())

    def test_duplicate_paths_and_conflicting_remote_objects_are_rejected(self):
        row = self.row('a.bin')
        for document in (self.document([row, copy.deepcopy(row)]),
                         self.document([row, self.row('other.bin', b'different')]),
                         self.document([row], [self.row('a.bin', staged=True)]),
                         self.document(staged=[self.row('a.bin', staged=True)] * 2)):
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.load(document)
        other = self.row('other.bin')
        other['remote']['version'] = 'fixture_version_2'
        with self.assertRaisesRegex(ValueError, 'Conflicting records'):
            self.load(self.document([row, other]))

    def test_same_sha256_with_conflicting_sizes_and_unsafe_paths_fail(self):
        other = self.row('other.bin', remote_id='fixture_other')
        other.update(size=6)
        other['remote']['size'] = 6
        with self.assertRaisesRegex(ValueError, 'Conflicting sizes'):
            self.load(self.document([self.row('a.bin'), other]))
        for path in ('../escape', '/absolute', 'a//b', 'a\\b', 'a/./b', 'a\nb'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.load(self.document([self.row(path)]))

    def test_symlink_and_oversized_manifest_are_refused(self):
        _, digest = self.load(self.document())
        link = self.root / 'link.json'
        link.symlink_to(self.path)
        with self.assertRaises(OSError):
            b.load_current_manifest(link, digest)
        with patch.object(b, 'MAX_MANIFEST_BYTES', 2), self.assertRaises(ValueError):
            b.load_current_manifest(self.path, digest)

    def test_incorrect_mapping_to_the_exact_selected_commit_fails(self):
        manifest, digest = self.load(self.document([self.row('a.bin', b'wrong')]))
        manifest['commit'] = self.commit
        with self.assertRaisesRegex(ValueError, 'mapping conflicts'):
            b.incremental_plan(self.inventory, manifest, digest)

    def test_cli_validation_is_metadata_only_and_plan_never_claims_atomic_cas(self):
        _, digest = self.load(self.document([self.row('a.bin')]))
        checkpoint = ['--expected-manifest-sha256', digest]
        with patch.object(b, 'expected_tree', side_effect=AssertionError('No Git needed')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(b.main(['--validate-manifest', str(self.path)] + checkpoint), 0)
        self.assertFalse(json.loads(out.getvalue())['atomicRemoteCAS'])
        with patch.object(b, 'expected_tree', return_value=self.inventory):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(b.main(['--commit', self.commit, '--plan-manifest', str(self.path)] + checkpoint), 0)
        self.assertEqual(json.loads(out.getvalue())['budget']['uploadBytes'], 14)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(b.main(['--validate-manifest', str(self.path)]), 2)
            self.assertEqual(b.main(['--plan-manifest', str(self.path)] + checkpoint), 2)


if __name__ == '__main__':
    unittest.main()
