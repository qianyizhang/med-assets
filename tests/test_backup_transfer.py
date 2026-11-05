"""Synthetic local-only tests for one-file Drive request/receipt preparation."""
import contextlib
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import backup_check as b
import backup_transfer as t


class TransferFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.work = self.root / 'one-job'
        self.manifest_path = self.root / 'current.json'
        self.manifest = {'schemaVersion': 1, 'revision': 0, 'commit': None, 'files': [], 'staged': []}
        self.manifest_path.write_bytes(t.encoded(self.manifest))
        self.checkpoint = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        self.payload = b'fixture public payload\0'
        self.sha = hashlib.sha256(self.payload).hexdigest()
        pointer = (f'version https://git-lfs.github.com/spec/v1\noid sha256:{self.sha}\n'
                   f'size {len(self.payload)}\n').encode()
        self.git('init', '-q')
        for name, data in (('.gitattributes', b'*.bin filter=lfs -text\n'),
                           ('payload.bin', pointer), ('normal.txt', b'committed text')):
            oid = self.git('hash-object', '-w', '--stdin', data=data).decode().strip()
            self.git('update-index', '--add', '--cacheinfo', '100644', oid, name)
        tree = self.git('write-tree').decode().strip()
        self.commit = self.git('commit-tree', tree, data=b'fixture\n').decode().strip()
        (self.repo / 'payload.bin').write_bytes(self.payload)
        (self.repo / 'normal.txt').write_bytes(b'dirty working text')

    def git(self, *args, data=None):
        return subprocess.run(['git', *args], cwd=self.repo, input=data, check=True,
                              env=dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_COMMITTER_NAME='Fixture',
                                       GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_EMAIL='fixture@example.invalid'),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def prepare(self, path='payload.bin', budget=64):
        return t.prepare_one(self.repo, self.commit, path, self.manifest_path,
                             self.checkpoint, self.work, 'fixture_folder', budget)

    def meta(self, job):
        return {'id': 'fixture_remote', 'title': t.object_name(job),
                'size': str(job['size']), 'parent_ids': ['fixture_folder'], 'version': 'fixture_version_1'}

    def receipt(self, job):
        downloaded = self.root / 'downloaded.bin'
        downloaded.write_bytes(self.payload)
        return t.verify_readback(job, 'fixture_remote', downloaded, self.meta(job), self.meta(job),
                                 '2026-01-02T03:04:05Z')


class BackupTransferTests(TransferFixture):
    def test_exact_lfs_stage_and_supported_upload_arguments_with_execution_block(self):
        result = self.prepare()
        self.assertEqual((self.work / 'payload.bin').read_bytes(), self.payload)
        request = result['requests']['upload']
        self.assertEqual(request['tool'], 'google_drive.upload_file')
        self.assertEqual(set(request['arguments']), {'file_uri', 'file_name', 'mime_type', 'parent_folder_id'})
        self.assertEqual(request['arguments']['parent_folder_id'], 'fixture_folder')
        self.assertTrue(result['requests']['executionBlocked'])
        self.assertEqual(result['job']['size'], len(self.payload))
        self.assertFalse(t.capabilities()['conditionalManifestWrite'])
        self.assertFalse(t.capabilities()['stableVersionInNormalizedMetadata'])

    def test_normal_git_source_ignores_dirty_working_file(self):
        result = self.prepare('normal.txt')
        self.assertEqual((self.work / 'payload.bin').read_bytes(), b'committed text')
        self.assertEqual(result['job']['commit'], self.commit)

    def test_untracked_path_budget_and_stale_manifest_fail_before_staging(self):
        (self.repo / 'private.txt').write_bytes(b'not in selected commit')
        for path, budget in (('private.txt', 64), ('payload.bin', 1), ('payload.bin', t.MAX_TRANSFER_BYTES + 1)):
            with self.subTest(path=path, budget=budget), self.assertRaises(ValueError):
                self.prepare(path, budget)
            self.assertFalse(self.work.exists())
        self.manifest_path.write_bytes(self.manifest_path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.work.exists())

    def test_private_job_metadata_must_stay_outside_the_checkout(self):
        work = self.repo / 'job'
        with self.assertRaisesRegex(t.TransferBlocked, 'outside the repository'):
            t.prepare_one(self.repo, self.commit, 'payload.bin', self.manifest_path,
                          self.checkpoint, work, 'fixture_folder', 64)
        self.assertFalse(work.exists())

    def test_wrong_or_pointer_only_lfs_source_is_never_accepted(self):
        (self.repo / 'payload.bin').write_bytes(b'wrong bytes')
        with self.assertRaisesRegex(t.TransferBlocked, 'mismatch'):
            self.prepare()
        self.assertTrue((self.work / 'prepared.json').exists())
        original = (self.work / 'payload.bin').read_bytes()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual((self.work / 'payload.bin').read_bytes(), original)

    def test_restart_reconciles_and_does_not_offer_upload_retry(self):
        first = self.prepare()
        result = self.prepare()
        self.assertEqual(first['job'], result['job'])
        self.assertTrue(result['restart'])
        self.assertNotIn('upload', result['requests'])
        self.assertEqual(result['next'], 'reconcile_only_no_upload_retry')
        self.assertEqual(len(list(self.work.iterdir())), 2)
        with self.assertRaisesRegex(t.TransferBlocked, 'Existing job differs'):
            self.prepare('normal.txt')

    def test_corrupt_existing_stage_and_symlink_job_are_refused(self):
        self.prepare()
        (self.work / 'payload.bin').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            self.prepare()
        link = self.root / 'linked-job'
        link.symlink_to(self.work, target_is_directory=True)
        with self.assertRaises(ValueError):
            t.prepare_one(self.repo, self.commit, 'payload.bin', self.manifest_path,
                          self.checkpoint, link, 'fixture_folder', 64)

    def test_uncertain_upload_and_ambiguous_search_never_retry(self):
        job = self.prepare()['job']
        for result in ({'isError': True}, {}, {'success': False}, {'success': True, 'id': '../bad'}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                t.confirmed_upload(result)
        self.assertEqual(t.confirmed_upload({'structuredContent': {'success': True, 'id': 'fixture_remote'}}), 'fixture_remote')
        for candidates in ([], [self.meta(job), self.meta(job)]):
            with self.assertRaisesRegex(t.TransferBlocked, 'uncertain'):
                t.reconcile_one(job, candidates)
        with self.assertRaisesRegex(t.TransferBlocked, 'Incomplete'):
            t.reconcile_one(job, [self.meta(job)], 'another_page')
        result = t.reconcile_one(job, [self.meta(job)])
        self.assertFalse(result['verified'])

    def test_wrong_folder_size_or_name_cannot_reconcile(self):
        job = self.prepare()['job']
        for change in ({'parent_ids': None}, {'size': True}, {'size': '999'}, {'title': 'unrelated'}):
            candidate = dict(self.meta(job), **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                t.reconcile_one(job, [candidate])

    def test_readback_requests_use_supported_raw_fetch_and_metadata_fields(self):
        job = self.prepare()['job']
        url = 'https://drive.google.com/file/d/fixture_remote/view'
        requests = t.readback_requests(job, 'fixture_remote', url)
        self.assertEqual(requests['fetch']['arguments'], {'url': url, 'download_raw_file': True, 'include_base64': False})
        self.assertNotIn('If-Match', json.dumps(requests))
        with self.assertRaises(ValueError):
            t.readback_requests(job, 'fixture_remote', 'https://example.invalid/download')

    def test_normalized_metadata_without_version_blocks_receipt(self):
        job = self.prepare()['job']
        normalized = self.meta(job)
        normalized.pop('version')
        downloaded = self.root / 'downloaded.bin'
        downloaded.write_bytes(self.payload)
        with self.assertRaisesRegex(t.TransferBlocked, 'version unavailable'):
            t.verify_readback(job, 'fixture_remote', downloaded, normalized, normalized)

    def test_corruption_version_race_and_wrong_file_id_fail_readback(self):
        job = self.prepare()['job']
        downloaded = self.root / 'downloaded.bin'
        downloaded.write_bytes(b'X' * len(self.payload))
        with self.assertRaisesRegex(t.TransferBlocked, 'mismatch'):
            t.verify_readback(job, 'fixture_remote', downloaded, self.meta(job), self.meta(job))
        downloaded.write_bytes(self.payload)
        for change in ({'version': 'fixture_version_2'}, {'id': 'fixture_other'}, {'sha256Checksum': 'f' * 64}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                t.verify_readback(job, 'fixture_remote', downloaded, self.meta(job), dict(self.meta(job), **change))

    def test_verified_receipt_drafts_only_staged_state_and_preserves_checkpoint(self):
        job = self.prepare()['job']
        receipt = self.receipt(job)
        before = self.manifest_path.read_bytes()
        result = t.draft_staged_manifest(self.manifest_path, self.checkpoint, job, receipt)
        self.assertFalse(result['adoptedAsCurrent'])
        self.assertTrue(result['remotePublicationBlocked'])
        self.assertEqual(result['proposedManifest']['files'], [])
        self.assertEqual(result['proposedManifest']['staged'], [receipt])
        self.assertEqual(result['proposedManifest']['revision'], 1)
        self.assertEqual(self.manifest_path.read_bytes(), before)
        self.assertEqual(t.draft_staged_manifest(self.manifest_path, self.checkpoint, job, receipt), result)
        self.manifest_path.write_bytes(before + b' ')
        with self.assertRaises(ValueError):
            t.draft_staged_manifest(self.manifest_path, self.checkpoint, job, receipt)

    def test_wrong_or_unverified_receipt_and_unresolved_staging_block_another_step(self):
        job = self.prepare()['job']
        receipt = self.receipt(job)
        receipt['path'] = 'other.bin'
        with self.assertRaises(ValueError):
            t.draft_staged_manifest(self.manifest_path, self.checkpoint, job, receipt)
        receipt = self.receipt(job)
        receipt['verification'] = {'status': 'unverified', 'method': 'none', 'at': None}
        with self.assertRaises(ValueError):
            t.draft_staged_manifest(self.manifest_path, self.checkpoint, job, receipt)
        self.manifest['staged'] = [self.receipt(job)]
        self.manifest_path.write_bytes(t.encoded(self.manifest))
        checkpoint = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(t.TransferBlocked, 'Unresolved staged'):
            t.prepare_one(self.repo, self.commit, 'payload.bin', self.manifest_path,
                          checkpoint, self.root / 'another-job', 'fixture_folder', 64)
        self.assertFalse((self.root / 'another-job').exists())

    def test_current_reuse_candidate_is_not_staged_or_uploaded_again(self):
        job = self.prepare()['job']
        receipt = self.receipt(job)
        receipt.pop('forCommit')
        manifest = {'schemaVersion': 1, 'revision': 1, 'commit': self.commit,
                    'files': [receipt], 'staged': []}
        self.manifest_path.write_bytes(t.encoded(manifest))
        checkpoint = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        another = self.root / 'another-job'
        with self.assertRaisesRegex(t.TransferBlocked, 'reuse/readback candidate'):
            t.prepare_one(self.repo, self.commit, 'payload.bin', self.manifest_path,
                          checkpoint, another, 'fixture_folder', 64)
        self.assertFalse(another.exists())

    def test_capabilities_cli_is_explicitly_blocked_and_missing_arguments_fail(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(t.main(['--capabilities']), 0)
        self.assertTrue(json.loads(out.getvalue())['remoteExecutionBlocked'])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(t.main([]), 2)


class FakeDrive:
    """Only bytes and dictionaries; no connector, HTTP or real destination."""
    def __init__(self):
        self.files, self.calls = {}, []

    def mutate(self, request, timeout=False):
        self.calls.append(request)
        args = request['arguments']
        if request['tool'] == 'google_drive.upload_file':
            file_id = 'fixture_' + str(len(self.files))
            self.files[file_id] = {'name': args['file_name'], 'parent': args['parent_folder_id'],
                                   'raw': Path(args['file_uri']).read_bytes()}
        elif request['tool'] == 'google_drive.update_file':
            file_id = args['fileId']
            self.files[file_id]['raw'] = Path(args['file_uri']).read_bytes()
        else:
            raise AssertionError('Unexpected mutation tool')
        if timeout:
            raise TimeoutError('Fixture outcome uncertain after execution')
        return {'structuredContent': {'success': True, 'id': file_id}}

    def meta(self, file_id):
        record = self.files[file_id]
        return {'id': file_id, 'title': record['name'], 'size': str(len(record['raw'])),
                'parent_ids': [record['parent']]}


class SerializedSyncTests(TransferFixture):
    def setUp(self):
        super().setUp()
        self.inventory = b.expected_tree(self.repo, self.commit)
        self.sync_work = self.root / 'sync-controller'
        self.drive = FakeDrive()
        self.drive.files['fixture_manifest'] = {'name': 'fixture_current.json',
            'parent': 'fixture_folder', 'raw': self.manifest_path.read_bytes()}
        self.counter = 0

    def controller(self, work=None):
        raw = self.drive.files['fixture_manifest']['raw']
        return t.SerializedSync(work or self.sync_work, self.inventory, 'fixture_folder',
                                'fixture_manifest', raw, hashlib.sha256(raw).hexdigest(), exclusive_writer=True)

    def stage_for(self, sync, path):
        self.counter += 1
        work = self.root / ('local-stage-' + str(self.counter))
        self.manifest_path.write_bytes(sync.state['current'].encode())
        result = t.prepare_one(self.repo, self.commit, path, self.manifest_path,
                               sync.state['checkpoint'], work, 'fixture_folder', 64, exclusive_writer=True)
        return result['job'], work

    def send(self, sync, path):
        job, work = self.stage_for(sync, path)
        request = sync.upload_intent(job, work)
        result = self.drive.mutate(request)
        file_id = sync.upload_known(result)
        downloaded = self.root / ('readback-' + file_id)
        downloaded.write_bytes(self.drive.files[file_id]['raw'])
        receipt = t.verify_readback(job, file_id, downloaded, self.drive.meta(file_id),
                                    self.drive.meta(file_id), '2026-01-02T03:04:05Z', exclusive_writer=True)
        sync.payload_verified(receipt)
        return receipt

    def flush(self, sync):
        file_id = sync.state['manifestId']
        request = sync.manifest_intent(self.drive.files[file_id]['raw'])
        self.assertEqual(set(request['arguments']), {'fileId', 'file_uri', 'mime_type'})
        self.drive.mutate(request)
        return sync.observe_manifest(file_id, self.drive.files[file_id]['raw'])

    def test_explicit_agreement_and_concurrent_local_run_rejection(self):
        with self.assertRaises(t.TransferBlocked):
            t.SerializedSync(self.sync_work, self.inventory, 'fixture_folder')
        with self.controller() as first:
            with self.assertRaisesRegex(t.TransferBlocked, 'Another local writer'):
                with self.controller():
                    pass
            self.assertFalse(first.status()['completeCurrentTree'])
        with self.controller() as resumed:
            self.assertEqual(resumed.state['phase'], 'idle')

    def test_exclusive_receipt_does_not_invent_a_version_and_strong_mode_still_blocks(self):
        job = self.prepare()['job']
        normalized = self.meta(job)
        normalized.pop('version')
        downloaded = self.root / 'bytes.bin'
        downloaded.write_bytes(self.payload)
        with self.assertRaisesRegex(t.TransferBlocked, 'version unavailable'):
            t.verify_readback(job, 'fixture_remote', downloaded, normalized, normalized)
        receipt = t.verify_readback(job, 'fixture_remote', downloaded, normalized, normalized,
                                    exclusive_writer=True)
        self.assertIsNone(receipt['remote']['version'])
        self.assertEqual(receipt['verification']['method'], 'exclusive-writer-sha256-size-readback')
        b.manifest_record(receipt, True)

    def test_bootstrap_intent_is_durable_and_no_blind_retry(self):
        work = self.root / 'bootstrap-controller'
        with t.SerializedSync(work, self.inventory, 'fixture_folder', exclusive_writer=True) as sync:
            with self.assertRaises(t.TransferBlocked):
                sync.bootstrap_intent([{'id': 'fixture_existing'}])
            request = sync.bootstrap_intent([])
            envelope = json.loads((work / 'journal.json').read_text())
            self.assertEqual(envelope['state']['phase'], 'bootstrap_unknown')
            with self.assertRaises(t.TransferBlocked):
                sync.bootstrap_intent([])
            result = self.drive.mutate(request)
            file_id = t.confirmed_upload(result)
            with self.assertRaises(t.TransferBlocked):
                sync.bootstrap_known(candidates=[])
            sync.bootstrap_known(result)
            with self.assertRaises(t.TransferBlocked):
                sync.observe_bootstrap(file_id, b'wrong')
            sync.observe_bootstrap(file_id, self.drive.files[file_id]['raw'])
            self.assertEqual(sync.state['phase'], 'idle')

    def test_partial_publication_keeps_commit_unassigned_until_complete(self):
        with self.controller() as sync:
            self.send(sync, 'payload.bin')
            result = self.flush(sync)
            self.assertFalse(result['completeCurrentTree'])
            current = json.loads(self.drive.files['fixture_manifest']['raw'])
            self.assertIsNone(current['commit'])
            self.assertEqual(current['files'], [])
            self.assertEqual(current['staged'][0]['forCommit'], self.commit)
        with self.controller() as sync:
            for path in ('.gitattributes', 'normal.txt'):
                self.send(sync, path)
            self.assertTrue(self.flush(sync)['completeCurrentTree'])
            current = json.loads(self.drive.files['fixture_manifest']['raw'])
            self.assertEqual(current['commit'], self.commit)
            self.assertEqual(len(current['files']), 3)
            self.assertEqual(current['staged'], [])

    def test_uncertain_upload_restart_and_duplicate_reconciliation(self):
        with self.controller() as sync:
            job, work = self.stage_for(sync, 'payload.bin')
            request = sync.upload_intent(job, work)
            with self.assertRaises(TimeoutError):
                self.drive.mutate(request, timeout=True)
        with self.controller() as sync:
            self.assertEqual(sync.state['phase'], 'upload_unknown')
            with self.assertRaises(t.TransferBlocked):
                sync.upload_intent(job, work)
            with self.assertRaises(t.TransferBlocked):
                sync.upload_known(candidates=[])
            candidate_id = next(k for k in self.drive.files if k != 'fixture_manifest')
            candidate = self.drive.meta(candidate_id)
            for candidates, token in (([candidate, candidate], None), ([candidate], 'more')):
                with self.assertRaises(t.TransferBlocked):
                    sync.upload_known(candidates=candidates, next_page_token=token)
            self.assertEqual(sync.upload_known(candidates=[candidate]), candidate_id)
            self.assertEqual(len(self.drive.calls), 1)

    def test_uncertain_manifest_old_value_is_not_a_retry_permission(self):
        with self.controller() as sync:
            self.send(sync, 'payload.bin')
            old = self.drive.files['fixture_manifest']['raw']
            request = sync.manifest_intent(old)
            for raw in (old, b'unexpected remote bytes'):
                with self.assertRaisesRegex(t.TransferBlocked, 'unresolved'):
                    sync.observe_manifest('fixture_manifest', raw)
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(old)
            self.drive.mutate(request)
            result = sync.observe_manifest('fixture_manifest', self.drive.files['fixture_manifest']['raw'])
            self.assertFalse(result['completeCurrentTree'])
            self.assertEqual(sync.observe_manifest('fixture_manifest', self.drive.files['fixture_manifest']['raw']), result)
            self.assertEqual(sum(c['tool'] == 'google_drive.update_file' for c in self.drive.calls), 1)

    def test_manifest_timeout_after_execution_reconciles_by_proposed_bytes(self):
        with self.controller() as sync:
            self.send(sync, 'payload.bin')
            request = sync.manifest_intent(self.drive.files['fixture_manifest']['raw'])
            with self.assertRaises(TimeoutError):
                self.drive.mutate(request, timeout=True)
        with self.controller() as sync:
            self.assertEqual(sync.state['phase'], 'manifest_unknown')
            self.assertFalse(sync.observe_manifest('fixture_manifest', self.drive.files['fixture_manifest']['raw'])['completeCurrentTree'])
            self.assertEqual(sum(c['tool'] == 'google_drive.update_file' for c in self.drive.calls), 1)

    def test_stale_manifest_enters_stopped_conflict_state(self):
        with self.controller() as sync:
            self.send(sync, 'payload.bin')
            with self.assertRaisesRegex(t.TransferBlocked, 'Unexpected remote manifest'):
                sync.manifest_intent(b'changed checkpoint')
            self.assertEqual(sync.state['phase'], 'conflict')
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(sync.state['current'].encode())
            self.assertFalse(any(c['tool'] == 'google_drive.update_file' for c in self.drive.calls))

    def test_wrong_readback_leaves_pending_without_publication_or_new_upload(self):
        with self.controller() as sync:
            job, work = self.stage_for(sync, 'payload.bin')
            result = self.drive.mutate(sync.upload_intent(job, work))
            file_id = sync.upload_known(result)
            path = self.root / 'wrong.bin'
            path.write_bytes(b'X' * job['size'])
            with self.assertRaises(t.TransferBlocked):
                t.verify_readback(job, file_id, path, self.drive.meta(file_id), self.drive.meta(file_id), exclusive_writer=True)
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(sync.state['current'].encode())
            self.assertEqual(sync.state['phase'], 'payload_known')

    def test_batch_limits_require_a_checkpoint_before_more_uploads(self):
        with self.controller() as sync, patch.object(t, 'BATCH_FILES', 1):
            self.send(sync, 'payload.bin')
            job, work = self.stage_for(sync, 'normal.txt')
            with self.assertRaisesRegex(t.TransferBlocked, 'bounded verified batch'):
                sync.upload_intent(job, work)
            self.assertEqual(sync.status()['unpublishedVerifiedBatchBytes'], len(self.payload))
            self.flush(sync)
            self.send(sync, 'normal.txt')

    def test_replacement_stops_with_exact_cleanup_targets_and_no_delete(self):
        old = b'previous accepted content'
        row = {'path': 'normal.txt', 'sha256': hashlib.sha256(old).hexdigest(), 'size': len(old),
               'remote': {'fileId': 'fixture_old', 'version': None, 'sha256': hashlib.sha256(old).hexdigest(), 'size': len(old)},
               'verification': {'status': 'verified', 'method': 'exclusive-writer-sha256-size-readback', 'at': '2020-01-01T00:00:00Z'}}
        initial = {'schemaVersion': 1, 'revision': 4, 'commit': 'b' * 40, 'files': [row], 'staged': []}
        self.drive.files['fixture_manifest']['raw'] = t.encoded(initial)
        self.drive.files['fixture_old'] = {'name': 'fixture_old.bin', 'parent': 'fixture_folder', 'raw': old}
        with self.controller() as sync:
            self.send(sync, 'normal.txt')
            with self.assertRaisesRegex(t.TransferBlocked, 'resolve cleanup'):
                job, work = self.stage_for(sync, 'payload.bin')
                sync.upload_intent(job, work)
            result = self.flush(sync)
            self.assertEqual(result['phase'], 'cleanup_required')
            self.assertEqual(result['cleanupProposal'][0]['remote']['fileId'], 'fixture_old')
            self.assertEqual(result['cleanupProposal'][0]['size'], len(old))
            current = json.loads(self.drive.files['fixture_manifest']['raw'])
            self.assertEqual(current['commit'], 'b' * 40)
            self.assertEqual(current['files'], [row])
            self.assertEqual(self.drive.files['fixture_old']['raw'], old)
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(sync.state['current'].encode())
        self.assertTrue(all(c['tool'] in ('google_drive.upload_file', 'google_drive.update_file') for c in self.drive.calls))

    def test_full_reuse_performs_no_new_payload_or_manifest_write(self):
        with self.controller() as sync:
            for path in ('.gitattributes', 'normal.txt', 'payload.bin'):
                self.send(sync, path)
            self.flush(sync)
        calls = len(self.drive.calls)
        with self.controller(self.root / 'next-controller') as sync:
            current = json.loads(sync.state['current'])
            with self.assertRaises(t.TransferBlocked):
                sync.finish_unchanged()
            for row in current['files']:
                file_id = row['remote']['fileId']
                sync.observe_reuse(file_id, self.drive.meta(file_id))
            self.assertTrue(sync.finish_unchanged()['completeCurrentTree'])
            self.assertEqual(len(self.drive.calls), calls)

    def test_interrupted_or_tampered_journal_is_not_silently_replaced(self):
        with self.controller():
            pass
        path = self.sync_work / 'journal.json'
        envelope = json.loads(path.read_text())
        envelope['state']['phase'] = 'complete'
        path.write_bytes(t.encoded(envelope))
        with self.assertRaisesRegex(t.TransferBlocked, 'checksum'):
            with self.controller():
                pass
        interrupted = self.root / 'interrupted'
        interrupted.mkdir()
        (interrupted / '.journal.json.next').write_bytes(b'partial')
        with self.assertRaisesRegex(t.TransferBlocked, 'Interrupted local checkpoint'):
            with self.controller(interrupted):
                pass
        self.assertTrue((interrupted / '.journal.json.next').exists())

    def test_initial_budget_is_bounded_and_explicit_about_metadata_ids(self):
        budget = t.initial_mirror_budget(self.inventory, 33)
        self.assertEqual(budget['payloadUploadBytes'], sum(r['size'] for r in self.inventory['files']))
        self.assertEqual(budget['payloadReadbackBytes'], budget['payloadUploadBytes'])
        self.assertEqual(budget['manifestUpdates'], 1)
        self.assertEqual(budget['assumedRemoteIdBytes'], 33)
        self.assertGreater(budget['payloadAndManifestDownloadBytes'], budget['payloadReadbackBytes'])
        self.assertFalse(t.capabilities(True)['remoteExecutionBlocked'])
        self.assertFalse(t.capabilities(True)['atomicRemoteCAS'])


class TwoLaneTests(TransferFixture):
    def setUp(self):
        super().setUp()
        self.inventory = b.expected_tree(self.repo, self.commit)
        self.sync_work = self.root / 'sync-controller'
        self.drive = FakeDrive()
        self.drive.files['fixture_manifest'] = {'name': 'fixture_current.json',
            'parent': 'fixture_folder', 'raw': self.manifest_path.read_bytes()}
        self.counter = 0

    controller = SerializedSyncTests.controller
    stage_for = SerializedSyncTests.stage_for
    send = SerializedSyncTests.send
    flush = SerializedSyncTests.flush

    def controller2(self):
        raw = self.drive.files['fixture_manifest']['raw']
        return t.TwoLaneSync(self.sync_work, self.inventory, 'fixture_folder',
                             'fixture_manifest', raw, hashlib.sha256(raw).hexdigest(), exclusive_writer=True)

    def migrate(self):
        with self.controller() as sync:
            state = t.TwoLaneSync.migration_proposal(sync.state, self.inventory)
            t.atomic_local(self.sync_work / 'journal.json', t.encoded({
                'state': state, 'sha256': hashlib.sha256(t.encoded(state)).hexdigest()}))

    def wave(self, sync):
        prepared = [self.stage_for(sync, p) for p in sync.next_paths()]
        sync.reserve_wave(prepared)
        requests = sync.dispatch_wave()
        outcomes = []
        for item in requests:
            op = item['operationId']
            result = self.drive.mutate(item['request'])
            file_id = t.confirmed_upload(result)
            downloaded = self.root / ('wave-' + file_id)
            downloaded.write_bytes(self.drive.files[file_id]['raw'])
            job = sync.state['lanes'][op]['job']
            receipt = t.verify_readback(job, file_id, downloaded, self.drive.meta(file_id),
                self.drive.meta(file_id), '2026-01-02T03:04:05Z', exclusive_writer=True)
            outcomes.append({'operationId': op, 'result': result, 'receipt': receipt})
        return outcomes

    def test_two_reversed_waves_keep_one_batch_and_complete_all_mappings(self):
        self.migrate()
        with self.controller2() as sync:
            outcomes = self.wave(sync)
            self.assertEqual(len(outcomes), 2)
            self.assertFalse(sync.settle_wave(list(reversed(outcomes)))['halted'])
            self.assertEqual(len(self.drive.calls), 2)  # no flush per pair
            self.assertEqual(len(sync.state['batch']), 2)
            sync.settle_wave(self.wave(sync))
            self.assertTrue(self.flush(sync)['completeCurrentTree'])
            self.assertEqual(len(json.loads(self.drive.files['fixture_manifest']['raw'])['files']), 3)
            self.assertEqual(len(sync.state['done']), 0)
            self.assertEqual(sync.state['phase'], 'v2:complete')

    def test_two_timeout_drains_sibling_and_preserves_reservation_across_restart(self):
        self.migrate()
        with self.controller2() as sync:
            outcomes = self.wave(sync)  # both really executed in fake Drive
            unresolved = outcomes[0]
            outcome = {'operationId': unresolved['operationId'], 'error': 'timeout'}
            result = sync.settle_wave([outcome, outcomes[1]])
            self.assertTrue(result['halted'])
            self.assertEqual(len(sync.state['batch']), 1)
            self.assertEqual(len(sync.state['lanes']), 1)
            for action in (lambda: sync.manifest_intent(sync.state['current'].encode()), sync.next_paths):
                with self.assertRaises(t.TransferBlocked):
                    action()
        with self.controller2() as sync:
            op = unresolved['operationId']
            file_id = unresolved['receipt']['remote']['fileId']
            for candidates in ([], [self.drive.meta(file_id)] * 2):
                with self.assertRaises(t.TransferBlocked):
                    sync.lane_known(op, candidates=candidates)
            sync.lane_known(op, candidates=[self.drive.meta(file_id)])
            sync.lane_verified(op, unresolved['receipt'])
            sync.lane_verified(op, unresolved['receipt'])  # crash after persistence: idempotent
            sync.resume_reconciled(sync.state['current'].encode())
            self.assertEqual(len(sync.state['batch']), 2)
            self.assertEqual(len(self.drive.calls), 2)

    def test_two_async_rejection_drains_sibling_before_settlement(self):
        self.migrate()
        finished = []
        with self.controller2() as sync:
            sync.reserve_wave([self.stage_for(sync, p) for p in sync.next_paths()])
            async def worker(item):
                if item['operationId'] == next(iter(sync.state['lanes'])):
                    raise TimeoutError('unknown create')
                await asyncio.sleep(0)  # yield to the sibling, no real delay/network
                result = self.drive.mutate(item['request'])
                file_id = t.confirmed_upload(result)
                job = sync.state['lanes'][item['operationId']]['job']
                path = self.root / 'async-readback'
                path.write_bytes(self.drive.files[file_id]['raw'])
                receipt = t.verify_readback(job, file_id, path, self.drive.meta(file_id),
                    self.drive.meta(file_id), exclusive_writer=True)
                finished.append(file_id)
                return {'result': result, 'receipt': receipt}
            result = asyncio.run(t.run_payload_wave(sync, worker))
            self.assertTrue(result['halted'])
            self.assertEqual(len(finished), 1)
            self.assertEqual(len(sync.state['batch']), 1)
            self.assertEqual(len(sync.state['lanes']), 1)

    def test_two_crash_after_known_id_and_duplicate_content_mapping(self):
        self.inventory['files'].append(dict(next(r for r in self.inventory['files']
                                                if r['path'] == 'payload.bin'), path='z-alias.bin'))
        self.migrate()
        with self.controller2() as sync:
            outcomes = self.wave(sync)
            for outcome in outcomes:
                sync.lane_known(outcome['operationId'], result=outcome['result'])
        with self.controller2() as sync:
            sync.settle_wave(outcomes)
            sync.settle_wave(self.wave(sync))
            self.assertTrue(self.flush(sync)['completeCurrentTree'])
            rows = {r['path']: r for r in json.loads(sync.state['current'])['files']}
            self.assertEqual(rows['payload.bin']['remote'], rows['z-alias.bin']['remote'])
            self.assertEqual(sum(c['tool'] == 'google_drive.upload_file' for c in self.drive.calls), 3)

    def test_two_duplicate_reservation_and_aggregate_slot_byte_budget(self):
        self.migrate()
        with self.controller2() as sync:
            pair = [self.stage_for(sync, p) for p in sync.next_paths()]
            with self.assertRaises(t.TransferBlocked):
                sync.reserve_wave([pair[0], pair[0]])
            with patch.object(t, 'BATCH_FILES', 1):
                self.assertEqual(len(sync.next_paths()), 1)
                with self.assertRaises(t.TransferBlocked):
                    sync.reserve_wave(pair)
            with patch.object(t, 'BATCH_BYTES', pair[0][0]['size']):
                self.assertEqual(len(sync.next_paths()), 1)
                with self.assertRaises(t.TransferBlocked):
                    sync.reserve_wave(pair)
            sync.reserve_wave(pair)
            self.assertEqual(sync.status()['unresolvedUploadBudgetBytes'], sum(j['size'] for j, _ in pair))
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(sync.state['current'].encode())
        with self.controller2() as sync:  # crash before dispatch retains safe reserved wave
            requests = sync.dispatch_wave()
            self.assertEqual(len(requests), 2)
            with self.assertRaises(t.TransferBlocked):
                sync.dispatch_wave()

    def test_two_shared_remote_id_and_wrong_receipt_drain_good_sibling(self):
        self.migrate()
        with self.controller2() as sync:
            outcomes = self.wave(sync)
            outcomes[1]['result'] = outcomes[0]['result']
            result = sync.settle_wave(outcomes)
            self.assertTrue(result['halted'])
            self.assertEqual(len(sync.state['batch']), 1)
            self.assertEqual(len(sync.state['lanes']), 1)
            self.assertTrue(any('different operations' in e for e in result['errors']))
        # Correct known result may still be reconciled; no new upload is emitted.
        with self.controller2() as sync:
            op = outcomes[1]['operationId']
            candidate = self.drive.meta(outcomes[1]['receipt']['remote']['fileId'])
            sync.lane_known(op, candidates=[candidate])
            bad = dict(outcomes[1]['receipt'], size=999)
            with self.assertRaises(ValueError):
                sync.lane_verified(op, bad)
            sync.lane_verified(op, outcomes[1]['receipt'])
            sync.resume_reconciled(sync.state['current'].encode())
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(b'stale remote')
            self.assertEqual(sync.state['phase'], 'v2:conflict')

    def test_two_strict_loader_and_old_mutator_phase_fence(self):
        self.migrate()
        with self.controller2() as sync:
            state = dict(sync.state)
        # The old code ignores schemaVersion, but every old mutator rejects v2 phases.
        old = t.SerializedSync(self.sync_work, self.inventory, 'fixture_folder', exclusive_writer=True)
        old.fd, old.state = 123, state
        for action in (lambda: old._phase('idle'), lambda: old._phase('upload_unknown'),
                       lambda: old._phase('manifest_unknown')):
            with self.assertRaises(t.TransferBlocked):
                action()
        for changed in ({'extra': True}, {'phase': 'idle'}, {'schemaVersion': 3}):
            tampered = dict(state, **changed)
            t.atomic_local(self.sync_work / 'journal.json', t.encoded({
                'state': tampered, 'sha256': hashlib.sha256(t.encoded(tampered)).hexdigest()}))
            with self.assertRaises(t.TransferBlocked):
                with self.controller2():
                    pass

    def test_two_missing_outcome_and_backoff_stop_dispatch_and_manifest_retry(self):
        self.migrate()
        with self.controller2() as sync:
            outcomes = self.wave(sync)
            self.assertTrue(sync.settle_wave([outcomes[0]], retry_after_seconds=60)['halted'])
            op = outcomes[1]['operationId']
            sync.lane_known(op, result=outcomes[1]['result'])
            sync.lane_verified(op, outcomes[1]['receipt'])
            with self.assertRaises(t.TransferBlocked):
                sync.resume_reconciled(sync.state['current'].encode())
            with patch.object(t.time, 'time', return_value=sync.state['retryNotBefore'] + 1):
                sync.resume_reconciled(sync.state['current'].encode())
            old = sync.state['current'].encode()
            with self.assertRaises(t.TransferBlocked):
                sync.manifest_intent(old)
            with patch.object(t.time, 'time', return_value=sync.state['retryNotBefore'] + 1):
                request = sync.manifest_intent(old)
            with self.assertRaises(t.TransferBlocked):
                sync.observe_manifest('fixture_manifest', old)
            self.assertEqual(len(sync.state['done']), 2)
            self.drive.mutate(request)
            sync.observe_manifest('fixture_manifest', self.drive.files['fixture_manifest']['raw'])
            self.assertEqual(sync.state['done'], {})

    def test_two_migration_refuses_active_or_changed_source_without_dropping_receipts(self):
        with self.controller() as sync:
            self.send(sync, 'payload.bin')
            with self.assertRaises(t.TransferBlocked):
                t.TwoLaneSync.migration_proposal(sync.state, self.inventory)
            self.flush(sync)
            changed = dict(self.inventory, files=[dict(r, sha256='0' * 64) if r['path'] == 'payload.bin' else r
                                                 for r in self.inventory['files']])
            with self.assertRaisesRegex(t.TransferBlocked, 'conflicts'):
                t.TwoLaneSync.migration_proposal(sync.state, changed)
            target = dict(self.inventory, commit='a' * 40)
            with self.assertRaisesRegex(t.TransferBlocked, 'Source rebind required'):
                t.TwoLaneSync.migration_proposal(sync.state, target)
            rebound = t.TwoLaneSync.source_rebind_proposal(sync.state, target)
            proposed = t.TwoLaneSync.migration_proposal(sync.state, target, rebound)
            self.assertEqual(proposed['targetCommit'], 'a' * 40)
            self.assertEqual(json.loads(rebound)['staged'][0]['remote'],
                             json.loads(sync.state['current'])['staged'][0]['remote'])
            self.assertEqual(sync.state['schemaVersion'], 1)  # pure proposal, not installed



class PayloadPoolTests(TransferFixture):
    controller = SerializedSyncTests.controller
    stage_for = SerializedSyncTests.stage_for
    flush = SerializedSyncTests.flush
    wave = TwoLaneTests.wave

    def setUp(self):
        super().setUp()
        for i in range(8):
            data = f'pool fixture {i}'.encode()
            oid = self.git('hash-object', '-w', '--stdin', data=data).decode().strip()
            self.git('update-index', '--add', '--cacheinfo', '100644', oid, f'pool-{i}.txt')
        tree = self.git('write-tree').decode().strip()
        self.commit = self.git('commit-tree', tree, data=b'pool fixture\n').decode().strip()
        self.inventory = b.expected_tree(self.repo, self.commit)
        self.sync_work = self.root / 'pool-controller'
        self.drive = FakeDrive()
        self.drive.files['fixture_manifest'] = {'name': 'fixture_current.json',
            'parent': 'fixture_folder', 'raw': self.manifest_path.read_bytes()}
        self.counter = 0

    def migrate(self, maximum):
        with self.controller() as sync:
            v2 = t.TwoLaneSync.migration_proposal(sync.state, self.inventory)
            state = t.PayloadPoolSync.migration_proposal(v2, self.inventory, maximum)
            t.atomic_local(self.sync_work / 'journal.json', t.encoded({
                'state': state, 'sha256': hashlib.sha256(t.encoded(state)).hexdigest()}))

    def pool(self):
        return t.PayloadPoolSync(self.sync_work, self.inventory, 'fixture_folder', exclusive_writer=True)

    def test_pool_four_and_eight_reversed_completion_and_full_map(self):
        for maximum in (4, 8):
            with self.subTest(maximum=maximum):
                self.sync_work = self.root / ('pool-' + str(maximum))
                self.drive.files['fixture_manifest']['raw'] = self.manifest_path.read_bytes()
                self.migrate(maximum)
                with self.pool() as sync:
                    first = self.wave(sync)
                    self.assertEqual(len(first), maximum)
                    self.assertFalse(sync.settle_wave(list(reversed(first)))['halted'])
                    while sync.next_paths():
                        sync.settle_wave(list(reversed(self.wave(sync))))
                    self.assertTrue(self.flush(sync)['completeCurrentTree'])
                    self.assertEqual(sync.state['phase'], 'v3:complete')
                    self.assertEqual(len(json.loads(sync.state['current'])['files']), 11)
                    self.assertEqual(sync.status()['maxPayloadLanes'], maximum)

    def test_pool_failed_sibling_known_ids_duplicate_callback_and_restart(self):
        for maximum in (4, 8):
            with self.subTest(maximum=maximum):
                self.sync_work = self.root / ('failure-' + str(maximum))
                self.drive.files['fixture_manifest']['raw'] = self.manifest_path.read_bytes()
                self.migrate(maximum)
                with self.pool() as sync:
                    outcomes = self.wave(sync)
                    failed = outcomes[0]
                    bad = dict(failed, error='readback failed after known upload ID')
                    result = sync.settle_wave([bad] + list(reversed(outcomes[1:])) + [outcomes[1]])
                    self.assertTrue(result['halted'])
                    self.assertEqual(len(sync.state['batch']), maximum - 1)
                    self.assertEqual(sync.state['lanes'][failed['operationId']]['fileId'], failed['receipt']['remote']['fileId'])
                    with self.assertRaises(t.TransferBlocked):sync.manifest_intent(sync.state['current'].encode())
                with self.pool() as sync:
                    self.assertEqual(sync.state['phase'], 'v3:halted')
                    with self.assertRaises(t.TransferBlocked):sync.dispatch_wave()
                    sync.lane_verified(failed['operationId'], failed['receipt'])
                    sync.lane_verified(failed['operationId'], failed['receipt'])
                    sync.resume_reconciled(sync.state['current'].encode())
                    self.assertEqual(len(sync.state['batch']), maximum)

    def test_pool_shared_count_byte_caps_and_fewer_admitted_than_maximum(self):
        self.migrate(8)
        with self.pool() as sync:
            paths = sync.next_paths()
            self.assertEqual(len(paths), 8)
            prepared = [self.stage_for(sync, p) for p in paths]
            with patch.object(t, 'BATCH_FILES', 4):
                self.assertEqual(len(sync.next_paths()), 4)
                with self.assertRaises(t.TransferBlocked):sync.reserve_wave(prepared)
            cap = sum(j['size'] for j, _ in prepared[:4])
            with patch.object(t, 'BATCH_BYTES', cap):
                self.assertEqual(len(sync.next_paths()), 4)
                with self.assertRaises(t.TransferBlocked):sync.reserve_wave(prepared)
            sync.reserve_wave(prepared[:4])
            self.assertEqual(len(sync.dispatch_wave()), 4)
            self.assertEqual(sync.status()['activeOperations'], 4)
            self.assertEqual(sync.status()['maxPayloadLanes'], 8)

    def test_pool_duplicate_remote_id_drains_other_workers(self):
        self.migrate(8)
        with self.pool() as sync:
            outcomes = self.wave(sync)
            outcomes[1]['result'] = outcomes[0]['result']
            self.assertTrue(sync.settle_wave(outcomes)['halted'])
            self.assertEqual(len(sync.state['batch']), 7)
            self.assertEqual(len(sync.state['lanes']), 1)

    def test_pool_strict_downgrade_fence_and_idle_v2_migration_preserves_receipts(self):
        with self.controller() as sync:
            # Produce a real staged receipt through the reviewed v1 handshake.
            SerializedSyncTests.send(self, sync, 'payload.bin')
            self.flush(sync)
            v2 = t.TwoLaneSync.migration_proposal(sync.state, self.inventory)
            target = dict(self.inventory, commit='c' * 40)
            rebound = t.TwoLaneSync.source_rebind_proposal(v2, target)
            with self.assertRaises(t.TransferBlocked):t.PayloadPoolSync.migration_proposal(v2, target, 8)
            v3 = t.PayloadPoolSync.migration_proposal(v2, target, 8, rebound)
            self.assertEqual(json.loads(v3['current'])['staged'][0]['remote'], json.loads(v2['current'])['staged'][0]['remote'])
            self.assertEqual(v3['seenIds'], v2['seenIds'])
            self.assertEqual(v2['schemaVersion'], 2)
            for maximum in (0, 3, 16, True):
                with self.assertRaises(t.TransferBlocked):t.PayloadPoolSync.migration_proposal(v2, self.inventory, maximum)
            active = dict(v2, phase='v2:active')
            with self.assertRaises(t.TransferBlocked):t.PayloadPoolSync.migration_proposal(active, self.inventory)
        self.sync_work = self.root / 'strict-pool'
        self.drive.files['fixture_manifest']['raw'] = self.manifest_path.read_bytes()
        self.migrate(8)
        with self.pool() as sync: state = dict(sync.state)
        with self.assertRaisesRegex(t.TransferBlocked, 'Unsupported journal schema'):
            with t.TwoLaneSync(self.sync_work, self.inventory, 'fixture_folder', exclusive_writer=True):pass
        for changes in ({'maxPayloadLanes': 16}, {'maxPayloadLanes': True}, {'phase': 'v2:idle'}, {'extra': 1}):
            altered = dict(state, **changes)
            t.atomic_local(self.sync_work / 'journal.json', t.encoded({'state': altered, 'sha256': hashlib.sha256(t.encoded(altered)).hexdigest()}))
            with self.assertRaises(t.TransferBlocked):
                with self.pool():pass


if __name__ == '__main__':
    unittest.main()
