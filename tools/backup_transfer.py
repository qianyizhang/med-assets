#!/usr/bin/env python3
"""Local one-file staging and Drive connector request/receipt boundary. No network."""
import argparse
import asyncio
import copy
import fcntl
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time

import backup_check as check

MAX_TRANSFER_BYTES = 100 * 1024 * 1024
BATCH_FILES = 64
BATCH_BYTES = 64 * 1024 * 1024
CONCURRENCY_BLOCKER = ('Drive update_file supports raw-byte replacement but exposes no '
                       'expected-version/If-Match precondition. Remote manifest publication '
                       'cannot safely compare-and-swap; stop before any real upload.')


class TransferBlocked(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise TransferBlocked(message)


def capabilities(exclusive_writer=False):
    return {'createFile': True, 'fetchRawFile': True, 'replaceRawFileInPlace': True,
            'conditionalManifestWrite': False, 'idempotentCreateToken': False,
            'stableVersionInNormalizedMetadata': False, 'normalizedProviderChecksums': False,
            'exclusiveWriterAccepted': exclusive_writer, 'atomicRemoteCAS': False,
            'remoteExecutionBlocked': not exclusive_writer,
            'blocker': None if exclusive_writer else CONCURRENCY_BLOCKER}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()


def object_name(job):
    return 'med-' + job['operationId'] + '.bin'


def verify_stream(stream, expected, target=None):
    digest, count = hashlib.sha256(), 0
    while True:
        chunk = stream.read(min(1024 * 1024, expected['size'] + 1 - count))
        if not chunk:
            break
        count += len(chunk)
        need(count <= expected['size'], 'Payload exceeds exact byte budget')
        digest.update(chunk)
        if target is not None:
            target.write(chunk)
    need(count == expected['size'] and digest.hexdigest() == expected['sha256'],
         'Payload size/SHA-256 mismatch; preserve the job for inspection')


def request_set(job, work):
    name = object_name(job)
    return {'executionBlocked': True, 'blocker': CONCURRENCY_BLOCKER,
            'upload': {'tool': 'google_drive.upload_file', 'arguments': {
                'file_uri': str((work / 'payload.bin').absolute()), 'file_name': name,
                'mime_type': 'application/octet-stream', 'parent_folder_id': job['folderId']}},
            'reconcile': {'tool': 'google_drive.search', 'arguments': {
                'special_filter_query_str': "'" + job['folderId'] + "' in parents and name = '" + name
                                            + "' and trashed = false",
                'best_effort_fetch': False, 'topn': 2}}}


def prepare_one(root, commit, path, manifest_path, expected_manifest, work, folder_id, max_bytes,
                exclusive_writer=False):
    """Only committed source bytes. Exclusive local writes; restart never retries an upload."""
    manifest = check.load_current_manifest(manifest_path, expected_manifest)
    need(root.resolve() not in (work.resolve(), *work.resolve().parents),
         'Keep private job metadata outside the repository checkout')
    need(type(folder_id) is str and check.REMOTE_TOKEN.fullmatch(folder_id), 'Invalid destination folder ID')
    need(type(max_bytes) is int and 0 <= max_bytes <= MAX_TRANSFER_BYTES, 'Explicit connector byte budget required')
    inventory = check.expected_tree(root, commit)
    rows = [r for r in inventory['files'] if r['path'] == path]
    need(len(rows) == 1, 'Path is not a regular file in the selected committed tree')
    row = rows[0]
    need(row['size'] <= max_bytes, 'Selected file exceeds the explicit byte budget')
    job = {**row, 'schemaVersion': 1, 'commit': commit, 'manifestSha256': expected_manifest,
           'folderId': folder_id, 'maxBytes': max_bytes}
    job['operationId'] = hashlib.sha256(encoded(job)).hexdigest()
    if work.exists():
        need(not work.is_symlink() and work.is_dir(), 'Unsafe job directory')
        with check.Tree(work).open('prepared.json') as (stream, size):
            need(size <= 4096, 'Invalid prepared receipt')
            need(stream.read() == encoded(job), 'Existing job differs; reconcile before preparing another')
        with check.Tree(work).open('payload.bin') as (stream, _):
            verify_stream(stream, row)
        return {'job': job, 'restart': True, 'next': 'reconcile_only_no_upload_retry',
                'requests': {'reconcile': request_set(job, work)['reconcile']},
                'executionBlocked': True, 'blocker': CONCURRENCY_BLOCKER}
    need(not manifest['staged'] or exclusive_writer and all(
        r['forCommit'] == commit and r['verification']['status'] == 'verified' for r in manifest['staged']),
        'Unresolved staged objects; do not accumulate another copy')
    plan = check.incremental_plan(inventory, manifest, expected_manifest)
    planned = next(obj for obj in plan['objects'] if path in obj['paths'])
    need(planned['action'] == 'upload', 'Existing content is a reuse/readback candidate; do not stage another upload')
    work.mkdir(mode=0o700)
    with (work / 'prepared.json').open('xb') as target:
        target.write(encoded(job))
    # A failed/interrupted stage is deliberately retained, never overwritten or retried.
    if row['kind'] == 'git':
        context = io.BytesIO(check.git(root, 'cat-file', 'blob', commit + ':' + path))
    else:
        context = check.Tree(root).open(path)
    with context as value, (work / 'payload.bin').open('xb') as target:
        stream = value if row['kind'] == 'git' else value[0]
        verify_stream(stream, row, target)
    check.load_current_manifest(manifest_path, expected_manifest)
    return {'job': job, 'restart': False, 'next': 'blocked_before_external_transfer',
            'requests': request_set(job, work)}


def unpack(result):
    need(type(result) is dict and not result.get('isError'), 'Unconfirmed outcome; reconcile before retrying')
    data = result.get('structuredContent', result)
    need(type(data) is dict, 'Malformed connector result')
    return data


def confirmed_upload(result):
    data = unpack(result)
    need(data.get('success') is True, 'Upload outcome uncertain; reconcile, do not retry')
    need(type(data.get('id')) is str and check.REMOTE_TOKEN.fullmatch(data['id']), 'No confirmed Drive file ID')
    return data['id']


def metadata(job, data, file_id):
    data = unpack(data)
    need(data.get('id') == file_id, 'Readback file ID mismatch')
    need(data.get('title', data.get('name')) == object_name(job), 'Unexpected remote name')
    parents = data.get('parent_ids', data.get('parents'))
    need(type(parents) is list and job['folderId'] in parents, 'Unexpected remote parent')
    size = data.get('size')
    need(type(size) is int or type(size) is str and size.isdecimal(), 'Remote size unavailable')
    need(int(size) == job['size'], 'Remote size mismatch')
    return data


def reconcile_one(job, candidates, next_page_token=None):
    """Consume a complete exact-name/folder search; never silently choose or retry."""
    need(not next_page_token, 'Incomplete reconciliation search; stop')
    need(type(candidates) is list and len(candidates) == 1,
         'Zero or multiple candidates: upload remains uncertain; no automatic retry')
    candidate = unpack(candidates[0])
    file_id = candidate.get('id')
    need(type(file_id) is str and check.REMOTE_TOKEN.fullmatch(file_id), 'Invalid candidate ID')
    metadata(job, candidate, file_id)
    return {'fileId': file_id, 'next': 'readback_required', 'verified': False}


def readback_requests(job, file_id, observed_url):
    need(type(file_id) is str and check.REMOTE_TOKEN.fullmatch(file_id), 'Invalid remote file ID')
    need(type(observed_url) is str and observed_url.startswith('https://drive.google.com/file/d/' + file_id + '/'),
         'Use the completed connector result URL for this exact file')
    return {'metadata': {'tool': 'google_drive.get_file_metadata', 'arguments': {
                'fileId': file_id, 'fields': 'id,name,mimeType,parents,size,version,sha256Checksum'}},
            'fetch': {'tool': 'google_drive.fetch', 'arguments': {
                'url': observed_url, 'download_raw_file': True, 'include_base64': False}},
            'order': 'metadata before, raw fetch/materialization, metadata after; verify stable version and bytes'}


def verify_readback(job, file_id, downloaded, before, after, verified_at=None, exclusive_writer=False):
    before, after = metadata(job, before, file_id), metadata(job, after, file_id)
    version = before.get('version')
    if not exclusive_writer:
        need(type(version) is str and check.REMOTE_TOKEN.fullmatch(version),
             'Stable Drive version unavailable; cannot bind byte readback to a version')
    need(after.get('version') == version, 'Concurrent remote change during readback')
    for data in (before, after):
        need(data.get('sha256Checksum') in (None, job['sha256']), 'Provider checksum mismatch')
    with check.Tree(downloaded.parent).open(downloaded.name) as (stream, _):
        verify_stream(stream, job)
    receipt = {key: job[key] for key in ('path', 'sha256', 'size')}
    receipt.update(forCommit=job['commit'], remote={'fileId': file_id, 'version': None if exclusive_writer else version,
                   'sha256': job['sha256'], 'size': job['size']},
                   verification={'status': 'verified', 'method': 'exclusive-writer-sha256-size-readback'
                                 if exclusive_writer else 'sha256-size-readback',
                                 'at': verified_at or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})
    check.manifest_record(receipt, True)
    return receipt


def draft_staged_manifest(path, expected_sha256, job, receipt):
    """Return a validated local proposal, never accept/publish current state."""
    need(job['manifestSha256'] == expected_sha256, 'Job belongs to another manifest checkpoint')
    manifest = check.load_current_manifest(path, expected_sha256)
    check.manifest_record(receipt, True)
    need(all(receipt[k] == job[k] for k in ('path', 'sha256', 'size'))
         and receipt['forCommit'] == job['commit'], 'Receipt differs from prepared committed payload')
    need(receipt['verification']['status'] == 'verified', 'Readback required before drafting a staged receipt')
    need(not manifest['staged'], 'Resolve existing staging before another manifest proposal')
    proposal = copy.deepcopy(manifest)
    proposal['staged'] = [copy.deepcopy(receipt)]
    proposal['revision'] += 1
    check.validate_current_manifest(proposal)
    return {'proposedManifest': proposal, 'expectedManifestSha256': expected_sha256,
            'adoptedAsCurrent': False, 'remotePublicationBlocked': True,
            'blocker': CONCURRENCY_BLOCKER,
            'retirementPolicy': 'Stop for explicit replacement/cleanup authorization before another payload; no deletion implemented.'}


def atomic_local(path, raw):
    """Durable local checkpoint, not a remote lock/CAS or a payload history."""
    need(not path.is_symlink(), 'Unsafe local checkpoint')
    temporary = path.with_name('.' + path.name + '.next')
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def decoded_manifest(raw):
    need(type(raw) is bytes and len(raw) <= check.MAX_MANIFEST_BYTES, 'Invalid manifest bytes')
    try:
        return check.validate_current_manifest(json.loads(raw, object_pairs_hook=check.unique_keys))
    except (ValueError, check.Stop) as error:
        raise TransferBlocked('Invalid current manifest') from error


class SerializedSync:
    """Single-writer connector handshake. All network calls belong to the host.

    Each returned mutation request follows an fsynced intent. The fixed work
    directory is the local lock domain; it does not lock Drive or other machines.
    """
    JOURNAL_SCHEMA = 1

    def __init__(self, work, inventory, folder_id, manifest_id=None, current=None,
                 expected_sha256=None, exclusive_writer=False):
        need(exclusive_writer is True, 'Explicit exclusive-writer agreement required')
        need(type(folder_id) is str and check.REMOTE_TOKEN.fullmatch(folder_id), 'Invalid mirror folder')
        need(manifest_id is None or type(manifest_id) is str and check.REMOTE_TOKEN.fullmatch(manifest_id),
             'Invalid manifest ID')
        self.work, self.inventory, self.folder_id = work, inventory, folder_id
        self.initial_id, self.initial_raw, self.initial_sha = manifest_id, current, expected_sha256
        self.fd = None

    def __enter__(self):
        self.work.mkdir(mode=0o700, exist_ok=True)
        need(self.work.is_dir() and not self.work.is_symlink(), 'Unsafe sync directory')
        self.fd = os.open(self.work / 'writer.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise TransferBlocked('Another local writer holds this sync directory') from error
            need(not list(self.work.glob('.*.next')), 'Interrupted local checkpoint; inspect before continuing')
            path = self.work / 'journal.json'
            if path.exists():
                with check.Tree(self.work).open(path.name) as (stream, size):
                    need(size <= 3 * check.MAX_MANIFEST_BYTES, 'Oversized journal')
                    envelope = json.loads(stream.read(), object_pairs_hook=check.unique_keys)
                self.state = envelope['state']
                need(self.state.get('schemaVersion') == self.JOURNAL_SCHEMA, 'Unsupported journal schema')
                need(hashlib.sha256(encoded(self.state)).hexdigest() == envelope['sha256'], 'Journal checksum mismatch')
                need(self.state['targetCommit'] == self.inventory['commit']
                     and self.state['folderId'] == self.folder_id, 'Journal belongs to another sync target')
                need(self.initial_id in (None, self.state['manifestId']), 'Journal manifest ID mismatch')
                need(hashlib.sha256(self.state['current'].encode()).hexdigest() == self.state['checkpoint'],
                     'Journal checkpoint mismatch')
                decoded_manifest(self.state['current'].encode())
            else:
                raw = self.initial_raw
                if self.initial_id is None:
                    raw = encoded({'schemaVersion': 1, 'revision': 0, 'commit': None, 'files': [], 'staged': []})
                else:
                    check.digest(self.initial_sha)
                    need(type(raw) is bytes and hashlib.sha256(raw).hexdigest() == self.initial_sha,
                         'Initial manifest checkpoint mismatch')
                decoded_manifest(raw)
                self.state = {'schemaVersion': 1, 'targetCommit': self.inventory['commit'],
                              'folderId': self.folder_id, 'manifestId': self.initial_id,
                              'current': raw.decode(), 'checkpoint': hashlib.sha256(raw).hexdigest(),
                              'phase': 'idle' if self.initial_id else 'bootstrap_ready',
                              'pending': None, 'batch': [], 'seenIds': [], 'cleanup': []}
                self._save()
            return self
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def __exit__(self, *_):
        os.close(self.fd)
        self.fd = None

    def _save(self):
        need(self.fd is not None, 'Hold the local writer lock')
        envelope = {'state': self.state, 'sha256': hashlib.sha256(encoded(self.state)).hexdigest()}
        atomic_local(self.work / 'journal.json', encoded(envelope))

    def _phase(self, *phases):
        need(self.fd is not None and self.state['phase'] in phases,
             'Unresolved operation or cleanup: no new mutation/retry is allowed')

    def bootstrap_intent(self, candidates, next_page_token=None):
        self._phase('bootstrap_ready')
        need(type(candidates) is list and not candidates and not next_page_token,
             'Complete empty bootstrap search required for a new mirror')
        name = 'med-assets-current-' + hashlib.sha256(encoded([self.folder_id, self.inventory['commit']])).hexdigest() + '.json'
        atomic_local(self.work / 'bootstrap.json', self.state['current'].encode())
        self.state.update(phase='bootstrap_unknown', pending={'name': name})
        self._save()
        return {'tool': 'google_drive.upload_file', 'arguments': {
            'file_uri': str((self.work / 'bootstrap.json').absolute()), 'file_name': name,
            'mime_type': 'application/json', 'parent_folder_id': self.folder_id}}

    def bootstrap_known(self, result=None, candidates=None, next_page_token=None):
        self._phase('bootstrap_unknown')
        if result is not None:
            file_id = confirmed_upload(result)
        else:
            need(not next_page_token and type(candidates) is list and len(candidates) == 1,
                 'Bootstrap outcome uncertain/ambiguous; no retry')
            data = unpack(candidates[0])
            need(data.get('title', data.get('name')) == self.state['pending']['name']
                 and self.folder_id in (data.get('parent_ids') or data.get('parents') or [])
                 and str(data.get('size')) == str(len(self.state['current'].encode())),
                 'Bootstrap reconciliation mismatch')
            file_id = data.get('id')
        need(type(file_id) is str and check.REMOTE_TOKEN.fullmatch(file_id), 'Confirmed/reconciled manifest ID required')
        self.state.update(manifestId=file_id, phase='bootstrap_known')
        self._save()

    def observe_bootstrap(self, file_id, raw):
        self._phase('bootstrap_known')
        need(file_id == self.state['manifestId'] and raw == self.state['current'].encode(),
             'Bootstrap readback mismatch')
        self.state.update(phase='idle', pending=None)
        self._save()

    def upload_intent(self, job, payload_work):
        self._phase('idle')
        need(job['commit'] == self.inventory['commit'] and job['folderId'] == self.folder_id
             and job['manifestSha256'] == self.state['checkpoint'], 'Prepared job checkpoint/target differs')
        matches = [r for r in self.inventory['files'] if r['path'] == job['path']]
        need(len(matches) == 1 and all(job[k] == matches[0][k] for k in ('sha256', 'size', 'kind')),
             'Prepared job differs from selected committed source')
        need(job['size'] <= job['maxBytes'] <= MAX_TRANSFER_BYTES, 'One-file budget exceeded')
        batch = self.state['batch']
        need(not batch or not self._proposal()[2], 'Publish the batch and resolve cleanup before another payload')
        need(not any(r['sha256'] == job['sha256'] for r in batch), 'Payload already verified in this batch')
        need(len(batch) < BATCH_FILES and (not batch or sum(r['size'] for r in batch) + job['size'] <= BATCH_BYTES),
             'Publish the bounded verified batch before another payload')
        manifest = decoded_manifest(self.state['current'].encode())
        plan = check.incremental_plan(self.inventory, manifest, self.state['checkpoint'])
        need(next(o for o in plan['objects'] if job['path'] in o['paths'])['action'] == 'upload',
             'Reuse/readback existing content instead of another upload')
        with check.Tree(payload_work).open('payload.bin') as (stream, _):
            verify_stream(stream, job)
        self.state.update(phase='upload_unknown', pending={'job': job})
        self._save()
        return request_set(job, payload_work)['upload']

    def upload_known(self, result=None, candidates=None, next_page_token=None):
        self._phase('upload_unknown')
        file_id = (confirmed_upload(result) if result is not None else
                   reconcile_one(self.state['pending']['job'], candidates, next_page_token)['fileId'])
        need(file_id != self.state['manifestId'], 'Manifest cannot be a payload object')
        self.state['pending']['fileId'] = file_id
        self.state['phase'] = 'payload_known'
        self._save()
        return file_id

    def payload_verified(self, receipt):
        self._phase('payload_known')
        check.manifest_record(receipt, True)
        pending, job = self.state['pending'], self.state['pending']['job']
        need(receipt['verification']['status'] == 'verified'
             and receipt['remote']['fileId'] == pending['fileId'] and receipt['forCommit'] == job['commit']
             and all(receipt[k] == job[k] for k in ('path', 'sha256', 'size')), 'Readback receipt differs from pending upload')
        self.state['batch'].append(copy.deepcopy(receipt))
        self.state['seenIds'].append(pending['fileId'])
        self.state.update(phase='idle', pending=None)
        self._save()

    def observe_reuse(self, file_id, observation):
        self._phase('idle')
        manifest = decoded_manifest(self.state['current'].encode())
        records = [r for r in manifest['files'] + manifest['staged'] if r['remote']['fileId'] == file_id]
        need(records and all(r['verification']['status'] == 'verified' for r in records), 'No trusted verified immutable object')
        data = unpack(observation)
        need(data.get('id') == file_id and self.folder_id in (data.get('parent_ids') or data.get('parents') or [])
             and str(data.get('size')) == str(records[0]['size']), 'Immutable reuse identity/availability mismatch')
        need(data.get('sha256Checksum') in (None, records[0]['sha256']), 'Reuse checksum mismatch')
        self.state['seenIds'] = sorted(set(self.state['seenIds']) | {file_id})
        self._save()

    def _proposal(self):
        current = decoded_manifest(self.state['current'].encode())
        staged = {r['path']: r for r in current['staged']}
        for receipt in self.state['batch']:
            for row in self.inventory['files']:
                if (row['sha256'], row['size']) == (receipt['sha256'], receipt['size']):
                    staged[row['path']] = dict(copy.deepcopy(receipt), path=row['path'])
        files = {r['path']: r for r in current['files']}
        chosen = {}
        for row in self.inventory['files']:
            for candidate in (staged.get(row['path']), files.get(row['path'])):
                if (candidate and candidate['verification']['status'] == 'verified'
                        and (candidate['sha256'], candidate['size']) == (row['sha256'], row['size'])
                        and candidate['remote']['fileId'] in self.state['seenIds']):
                    chosen[row['path']] = candidate
                    break
        used = {r['remote']['fileId'] for r in chosen.values()}
        wanted = {r['path'] for r in self.inventory['files']}
        cleanup = [dict(r, reason='obsolete_path' if r['path'] not in wanted else 'replaced_object',
                        physicalRetirementNeeded=r['remote']['fileId'] not in used)
                   for r in current['files'] if r['path'] not in wanted
                   or r['path'] in staged and r['remote']['fileId'] != staged[r['path']]['remote']['fileId']]
        complete = len(chosen) == len(wanted) and not cleanup
        proposal = copy.deepcopy(current)
        proposal['revision'] += 1
        proposal['staged'] = [staged[p] for p in sorted(staged)]
        if complete:
            proposal['commit'] = self.inventory['commit']
            proposal['files'] = [{k: v for k, v in chosen[p].items() if k != 'forCommit'} for p in sorted(chosen)]
            proposal['staged'] = []
        check.validate_current_manifest(proposal)
        return proposal, complete, cleanup

    def manifest_intent(self, observed_current):
        self._phase('idle')
        if observed_current != self.state['current'].encode():
            self.state['phase'] = 'conflict'
            self._save()
            raise TransferBlocked('Unexpected remote manifest checkpoint; stop')
        proposal, complete, cleanup = self._proposal()
        need(self.state['batch'] or complete, 'No verified batch/finalization to publish')
        raw = encoded(proposal)
        atomic_local(self.work / 'proposal.json', raw)
        self.state.update(phase='manifest_unknown', pending={'proposed': raw.decode(), 'complete': complete, 'cleanup': cleanup})
        self._save()
        return {'tool': 'google_drive.update_file', 'arguments': {
            'fileId': self.state['manifestId'], 'file_uri': str((self.work / 'proposal.json').absolute()),
            'mime_type': 'application/json'}, 'guarantee': 'exclusive single writer; NOT atomic remote CAS'}

    def observe_manifest(self, file_id, raw):
        if (self.fd is not None and self.state['phase'] in ('idle', 'complete', 'cleanup_required')
                and self.state['pending'] is None and file_id == self.state['manifestId']
                and raw == self.state['current'].encode()):
            return self.status()
        self._phase('manifest_unknown')
        pending = self.state['pending']
        need(file_id == self.state['manifestId'], 'Wrong manifest file ID')
        need(raw == pending['proposed'].encode(),
             'Manifest update unresolved: old/other bytes are not proof the in-flight write did not execute; do not retry')
        decoded_manifest(raw)
        self.state.update(current=raw.decode(), checkpoint=hashlib.sha256(raw).hexdigest(),
                          phase='cleanup_required' if pending['cleanup'] else 'complete' if pending['complete'] else 'idle',
                          cleanup=pending['cleanup'], pending=None, batch=[])
        self._save()
        return self.status()

    def finish_unchanged(self):
        self._phase('idle')
        current = decoded_manifest(self.state['current'].encode())
        _, complete, cleanup = self._proposal()
        need(not self.state['batch'] and not current['staged'] and complete and not cleanup
             and current['commit'] == self.inventory['commit'], 'Current mirror still needs verified progress')
        self.state['phase'] = 'complete'
        self._save()
        return self.status()

    def status(self):
        current = decoded_manifest(self.state['current'].encode())
        objects = {r['remote']['fileId']: r['size'] for r in current['files'] + current['staged'] + self.state['batch']}
        unresolved = self.state['pending'] or {}
        pending_bytes = unresolved.get('job', {}).get('size', 0)
        return {'phase': self.state['phase'], 'completeCurrentTree': self.state['phase'] == 'complete',
                'checkpointSha256': self.state['checkpoint'], 'cleanupProposal': copy.deepcopy(self.state['cleanup']),
                'listedPayloadBytes': sum(objects.values()), 'unresolvedUploadBudgetBytes': pending_bytes,
                'unpublishedVerifiedBatchBytes': sum(r['size'] for r in self.state['batch']),
                'manifestCheckpointBytes': len(self.state['current'].encode()),
                'guarantee': 'exclusive single writer; local lock only; NOT atomic remote CAS'}


class TwoLaneSync(SerializedSync):
    """One coordinator, fixed waves of at most two host payload operations.

    No network is performed here. Hosts must drain all dispatched operations,
    including siblings of a failed call, before requesting another wave.
    """
    JOURNAL_SCHEMA = 2
    EXTRA = {'lanes', 'done', 'halted', 'retryNotBefore'}
    BASE = {'schemaVersion', 'targetCommit', 'folderId', 'manifestId', 'current',
            'checkpoint', 'phase', 'pending', 'batch', 'seenIds', 'cleanup'}
    PHASES = {'v2:idle', 'v2:reserved', 'v2:active', 'v2:halted',
              'v2:manifest_unknown', 'v2:complete', 'v2:cleanup_required', 'v2:conflict'}

    @staticmethod
    def migration_proposal(old, inventory, verified_rebound=None):
        """Pure proposal; install only while holding the existing idle v1 lock.

        A source change requires exact readback of source_rebind_proposal().
        The host must pre-read the old checkpoint before that separate write.
        """
        need(set(old) == TwoLaneSync.BASE and old['schemaVersion'] == 1
             and old['phase'] == 'idle' and old['pending'] is None
             and not old['batch'] and not old['cleanup'], 'Migration requires positively idle v1 journal')
        need(hashlib.sha256(old['current'].encode()).hexdigest() == old['checkpoint'], 'Migration checkpoint mismatch')
        current = decoded_manifest(old['current'].encode())
        expected = {r['path']: r for r in inventory['files']}
        for row in current['files'] + current['staged']:
            need(row['path'] in expected and row['verification']['status'] == 'verified'
                 and all(row[k] == expected[row['path']][k] for k in ('sha256', 'size')),
                 'Source migration conflicts with retained receipt: ' + row['path'])
        state = copy.deepcopy(old)
        if old['targetCommit'] != inventory['commit']:
            expected = TwoLaneSync.source_rebind_proposal(old, inventory)
            need(type(verified_rebound) is bytes and verified_rebound == expected,
                 'Source rebind required: verify and publish the new manifest checkpoint before migration')
            state.update(current=expected.decode(), checkpoint=hashlib.sha256(expected).hexdigest(),
                         targetCommit=inventory['commit'])
        state.update(schemaVersion=2, phase='v2:idle', lanes={}, done={}, halted=False, retryNotBefore=0)
        return state

    @staticmethod
    def source_rebind_proposal(old, inventory):
        """Pure bytes for a separately journaled, checkpoint-guarded rebind.

        No mutation is returned/performed. Preserve accepted commit/files and
        every ID; only partial staged target bindings and revision change.
        """
        current = decoded_manifest(old['current'].encode())
        expected = {r['path']: r for r in inventory['files']}
        for row in current['files'] + current['staged']:
            need(row['path'] in expected and row['verification']['status'] == 'verified'
                 and all(row[k] == expected[row['path']][k] for k in ('sha256', 'size')),
                 'Source migration conflicts with retained receipt: ' + row['path'])
        for row in current['staged']:
            row['forCommit'] = inventory['commit']
        current['revision'] += 1
        check.validate_current_manifest(current)
        return encoded(current)

    def __enter__(self):
        # Bootstrap uses the reviewed v1 handshake first, then explicit idle migration.
        need((self.work / 'journal.json').is_file(), 'Explicit idle-v1 migration required before two-lane use')
        super().__enter__()
        try:
            self._validate()
            return self
        except BaseException:
            self.__exit__()
            raise

    def _validate(self):
        s = self.state
        need(set(s) == self.BASE | self.EXTRA and type(s['schemaVersion']) is int
             and s['schemaVersion'] == 2 and s['phase'] in self.PHASES, 'Invalid v2 journal schema/phase')
        need(type(s['lanes']) is dict and len(s['lanes']) <= 2 and type(s['done']) is dict
             and type(s['halted']) is bool and type(s['retryNotBefore']) is int
             and s['retryNotBefore'] >= 0 and type(s['batch']) is list
             and type(s['seenIds']) is list and len(set(s['seenIds'])) == len(s['seenIds']), 'Invalid v2 reservations')
        need(s['targetCommit'] == self.inventory['commit'], 'Invalid target commit')
        need(type(s['cleanup']) is list and type(s['current']) is str
             and s['manifestId'] is not None and type(s['seenIds']) is list
             and all(type(x) is str and check.REMOTE_TOKEN.fullmatch(x) for x in s['seenIds']), 'Invalid journal fields')
        need(s['halted'] == (s['phase'] == 'v2:halted'), 'Invalid halted phase')
        need(all(type(l) is dict for l in s['lanes'].values()), 'Invalid lane object')
        need(s['phase'] != 'v2:reserved' or bool(s['lanes']) and all(
             l.get('phase') == 'reserved' for l in s['lanes'].values()), 'Invalid reserved phase')
        check.digest(s['checkpoint'])
        current = decoded_manifest(s['current'].encode())
        ids = {}
        for row in current['files'] + current['staged'] + s['batch']:
            check.manifest_record(row, 'forCommit' in row)
            file_id, identity = row['remote']['fileId'], (row['sha256'], row['size'])
            need(file_id not in ids or ids[file_id] == identity, 'Remote ID assigned to different content')
            ids[file_id] = identity
        identities = {(r['sha256'], r['size']) for r in s['batch']}
        need(len(identities) == len(s['batch']) and len(s['done']) == len(s['batch']), 'Invalid completed operations')
        for op, file_id in s['done'].items():
            check.digest(op)
            need(file_id in {r['remote']['fileId'] for r in s['batch']}, 'Completed operation missing receipt')
        need(len(set(s['done'].values())) == len(s['done']), 'Remote ID assigned to different operations')
        for op, lane in s['lanes'].items():
            need(set(lane) == {'job', 'work', 'phase', 'fileId'}
                 and lane['phase'] in ('reserved', 'unknown', 'known')
                 and type(lane['work']) is str and op not in s['done'], 'Invalid lane schema')
            self._validate_job(lane['job'])
            job = lane['job']
            need(op == job['operationId'] and (job['sha256'], job['size']) not in identities, 'Duplicate reservation')
            identities.add((job['sha256'], job['size']))
            file_id = lane['fileId']
            need((lane['phase'] == 'known') == (file_id is not None), 'Invalid known lane')
            if file_id is not None:
                need(type(file_id) is str and check.REMOTE_TOKEN.fullmatch(file_id)
                     and file_id != s['manifestId'] and file_id not in ids, 'Remote ID assigned to different operations')
                ids[file_id] = (job['sha256'], job['size'])
        sizes = [r['size'] for r in s['batch']] + [r['job']['size'] for r in s['lanes'].values()]
        need(len(sizes) <= BATCH_FILES and (sum(sizes) <= BATCH_BYTES or len(sizes) == 1), 'Aggregate batch budget exceeded')
        need(not s['lanes'] or s['phase'] in ('v2:reserved', 'v2:active', 'v2:halted'), 'Unresolved lane at publication barrier')
        need((s['pending'] is not None) == (s['phase'] == 'v2:manifest_unknown'), 'Invalid manifest pending state')
        if s['pending'] is not None:
            need(set(s['pending']) == {'proposed', 'complete', 'cleanup'}
                 and type(s['pending']['complete']) is bool and type(s['pending']['cleanup']) is list,
                 'Invalid manifest intent')
            decoded_manifest(s['pending']['proposed'].encode())
            proposal, complete, cleanup = self._proposal()
            need(s['pending']['proposed'].encode() == encoded(proposal)
                 and s['pending']['complete'] == complete and s['pending']['cleanup'] == cleanup,
                 'Manifest intent differs from verified batch')
        if s['phase'] == 'v2:complete':
            rows = {r['path']: r for r in current['files']}
            need(current['commit'] == self.inventory['commit'] and not current['staged']
                 and not s['batch'] and not s['cleanup'] and len(rows) == len(self.inventory['files'])
                 and all(r['path'] in rows and all(rows[r['path']][k] == r[k] for k in ('sha256', 'size'))
                         for r in self.inventory['files']), 'Incomplete tree marked complete')

    def _validate_job(self, job):
        need(type(job) is dict and set(job) == {'path', 'sha256', 'size', 'kind', 'schemaVersion',
             'commit', 'manifestSha256', 'folderId', 'maxBytes', 'operationId'}, 'Invalid job schema')
        check.digest(job['operationId'])
        unsigned = {k: v for k, v in job.items() if k != 'operationId'}
        need(hashlib.sha256(encoded(unsigned)).hexdigest() == job['operationId'], 'Operation identity mismatch')
        rows = [r for r in self.inventory['files'] if r['path'] == job['path']]
        need(len(rows) == 1 and all(rows[0][k] == job[k] for k in ('sha256', 'size', 'kind'))
             and job['schemaVersion'] == 1 and job['commit'] == self.inventory['commit']
             and job['folderId'] == self.folder_id and job['manifestSha256'] == self.state['checkpoint']
             and type(job['maxBytes']) is int and 0 <= job['size'] <= job['maxBytes'] <= MAX_TRANSFER_BYTES,
             'Prepared job checkpoint/source/budget differs')

    def _save(self):
        if not self.state['phase'].startswith('v2:'):
            self.state['phase'] = 'v2:' + self.state['phase']
        self._validate()
        super()._save()

    def _phase(self, *phases):
        super()._phase(*('v2:' + p for p in phases))

    def upload_intent(self, *args, **kwargs):
        raise TransferBlocked('Two-lane mode requires reserve_wave/dispatch_wave')

    upload_known = payload_verified = bootstrap_intent = bootstrap_known = observe_bootstrap = upload_intent

    def next_paths(self):
        """Next fixed wave within the original sorted 64-object/byte partition."""
        self._phase('idle')
        need(not self.state['halted'] and not self.state['lanes']
             and time.time() >= self.state['retryNotBefore'], 'Halted/backoff: reconcile before dispatch')
        plan = check.incremental_plan(self.inventory, decoded_manifest(self.state['current'].encode()), self.state['checkpoint'])
        done = {(r['sha256'], r['size']) for r in self.state['batch']}
        count, size, paths = len(done), sum(r['size'] for r in self.state['batch']), []
        for obj in sorted(plan['objects'], key=lambda r: (r['sha256'], r['size'])):
            if obj['action'] != 'upload' or (obj['sha256'], obj['size']) in done:
                continue
            if count and (count >= BATCH_FILES or size + obj['size'] > BATCH_BYTES):
                break
            paths.append(sorted(obj['paths'])[0])
            count, size = count + 1, size + obj['size']
            if len(paths) == 2 or size > BATCH_BYTES:
                break
        return paths

    def reserve_wave(self, prepared):
        paths = self.next_paths()
        need(type(prepared) is list and 1 <= len(prepared) <= 2
             and [j['path'] for j, _ in prepared] == paths[:len(prepared)], 'Reserve next distinct ordered payloads only')
        need(not self.state['batch'] or not self._proposal()[2], 'Publish batch and resolve cleanup first')
        lanes = {}
        for job, work in prepared:
            self._validate_job(job)
            with check.Tree(work).open('payload.bin') as (stream, _):
                verify_stream(stream, job)
            need(job['operationId'] not in lanes, 'Duplicate operation reservation')
            lanes[job['operationId']] = {'job': copy.deepcopy(job), 'work': str(work.absolute()),
                                         'phase': 'reserved', 'fileId': None}
        self.state.update(lanes=lanes, phase='v2:reserved')
        self._save()  # BOTH reservations durable before either request can escape.

    def dispatch_wave(self):
        self._phase('reserved')
        need(not self.state['halted'], 'Halted coordinator')
        for lane in self.state['lanes'].values():
            need(lane['phase'] == 'reserved', 'Wave was already dispatched; reconcile, never retry')
            with check.Tree(Path(lane['work'])).open('payload.bin') as (stream, _):
                verify_stream(stream, lane['job'])
            lane['phase'] = 'unknown'
        self.state['phase'] = 'v2:active'
        self._save()
        return [{'operationId': op, 'request': request_set(l['job'], Path(l['work']))['upload']}
                for op, l in self.state['lanes'].items()]

    def lane_known(self, operation, result=None, candidates=None, next_page_token=None):
        self._phase('active', 'halted')
        lane = self.state['lanes'][operation]
        need(lane['phase'] in ('unknown', 'known'), 'Lane not dispatched')
        file_id = (confirmed_upload(result) if result is not None else
                   reconcile_one(lane['job'], candidates, next_page_token)['fileId'])
        need(lane['fileId'] in (None, file_id), 'Operation returned conflicting IDs')
        current = decoded_manifest(self.state['current'].encode())
        used = {r['remote']['fileId'] for r in current['files'] + current['staged'] + self.state['batch']}
        used |= {l['fileId'] for op, l in self.state['lanes'].items() if op != operation}
        need(file_id != self.state['manifestId'] and file_id not in used, 'Remote ID assigned to different operations')
        lane.update(fileId=file_id, phase='known')
        self._save()
        return file_id

    def lane_verified(self, operation, receipt):
        self._phase('active', 'halted')
        if operation in self.state['done']:
            need(any(r == receipt for r in self.state['batch'])
                 and self.state['done'][operation] == receipt['remote']['fileId'], 'Conflicting repeated receipt')
            return
        lane = self.state['lanes'][operation]
        check.manifest_record(receipt, True)
        job = lane['job']
        need(lane['phase'] == 'known' and receipt['remote']['fileId'] == lane['fileId']
             and receipt['verification']['status'] == 'verified' and receipt['forCommit'] == job['commit']
             and all(receipt[k] == job[k] for k in ('path', 'sha256', 'size')), 'Wrong lane readback receipt')
        self.state['batch'].append(copy.deepcopy(receipt))
        self.state['seenIds'] = sorted(set(self.state['seenIds']) | {lane['fileId']})
        self.state['done'][operation] = lane['fileId']
        del self.state['lanes'][operation]
        self._save()

    def settle_wave(self, outcomes, retry_after_seconds=0):
        """Drain ALL settled sibling outcomes; never short-circuit on a rejection.

        The host must await allSettled (or equivalent) before passing outcomes.
        Missing/failed outcomes retain reservations and block every new mutation.
        """
        self._phase('active', 'halted')
        need(type(outcomes) is list and type(retry_after_seconds) is int and retry_after_seconds >= 0,
             'Invalid settled outcomes/backoff')
        expected, seen, errors = set(self.state['lanes']), set(), []
        for outcome in outcomes:
            try:
                op = outcome['operationId']
                need(op in expected and op not in seen, 'Duplicate/unknown outcome')
                seen.add(op)
                if 'result' in outcome:
                    self.lane_known(op, result=outcome['result'])
                need(not outcome.get('error'), 'Payload outcome uncertain; reconcile before continuing')
                self.lane_verified(op, outcome['receipt'])
            except (ValueError, KeyError, TypeError) as error:
                errors.append(str(error))
        halted = bool(errors or expected != seen or self.state['lanes'])
        self.state.update(halted=halted, phase='v2:halted' if halted else 'v2:idle',
                          retryNotBefore=max(self.state['retryNotBefore'], int(time.time()) + retry_after_seconds))
        self._save()
        return {'halted': halted, 'errors': errors, 'unresolved': sorted(self.state['lanes'])}

    def resume_reconciled(self, observed_current):
        self._phase('halted')
        need(not self.state['lanes'] and observed_current == self.state['current'].encode()
             and time.time() >= self.state['retryNotBefore'], 'Unresolved lane/checkpoint/backoff')
        self.state.update(halted=False, phase='v2:idle')
        self._save()

    def manifest_intent(self, observed_current):
        need(not self.state['lanes'] and not self.state['halted']
             and time.time() >= self.state['retryNotBefore'], 'No manifest publication with unresolved lanes/backoff')
        return super().manifest_intent(observed_current)

    def observe_manifest(self, file_id, raw):
        if (self.state['phase'] in ('v2:idle', 'v2:complete', 'v2:cleanup_required')
                and self.state['pending'] is None and file_id == self.state['manifestId']
                and raw == self.state['current'].encode()):
            return self.status()
        # Clear replay cache only when the exact proposed bytes have been observed.
        self._phase('manifest_unknown')
        need(file_id == self.state['manifestId'] and raw == self.state['pending']['proposed'].encode(),
             'Manifest update unresolved; do not retry')
        self.state['done'] = {}
        return super().observe_manifest(file_id, raw)

    def status(self):
        status = super().status()
        status.update(completeCurrentTree=self.state['phase'] == 'v2:complete',
                      activeOperations=len(self.state['lanes']), halted=self.state['halted'],
                      unresolvedUploadBudgetBytes=sum(l['job']['size'] for l in self.state['lanes'].values()))
        return status


async def run_payload_wave(controller, worker):
    """Drain both host workers before one coordinator records settled results.

    worker(item) returns result/receipt or result/error fields; after an unknown
    mutation it must report uncertainty, never retry. No manifest writes here.
    """
    requests = controller.dispatch_wave()
    settled = await asyncio.gather(*(worker(item) for item in requests), return_exceptions=True)
    outcomes = []
    for item, value in zip(requests, settled):
        if isinstance(value, BaseException):
            value = {'error': type(value).__name__ + ': ' + str(value)}
        if type(value) is not dict:
            value = {'error': 'Worker returned incomplete evidence'}
        outcomes.append(dict(value, operationId=item['operationId']))
    delays = [o.get('retryAfterSeconds', 0) for o in outcomes]
    delay = max([d for d in delays if type(d) is int and d >= 0], default=0)
    return controller.settle_wave(outcomes, retry_after_seconds=delay)


def initial_mirror_budget(inventory, remote_id_bytes=33):
    """Exact payload budget; conditional serialized metadata estimate for an empty mirror."""
    need(type(remote_id_bytes) is int and 5 <= remote_id_bytes <= 200, 'Invalid estimated ID length')
    groups = {}
    for row in inventory['files']:
        groups.setdefault((row['sha256'], row['size']), []).append(row['path'])
    batches, batch, count = [], [], 0
    for identity, paths in sorted(groups.items()):
        if batch and (len(batch) >= BATCH_FILES or count + identity[1] > BATCH_BYTES):
            batches.append(batch)
            batch, count = [], 0
        batch.append((identity, sorted(paths)))
        count += identity[1]
    if batch:
        batches.append(batch)
    current = {'schemaVersion': 1, 'revision': 0, 'commit': None, 'files': [], 'staged': []}
    initial = len(encoded(current))
    lengths, index = [], 0
    for batch in batches:
        for (sha, size), paths in batch:
            index += 1
            for path in paths:
                current['staged'].append({'path': path, 'sha256': sha, 'size': size,
                    'forCommit': inventory['commit'],
                    'remote': {'fileId': 'r' * (remote_id_bytes - 5) + f'{index:05d}',
                               'version': None, 'sha256': sha, 'size': size},
                    'verification': {'status': 'verified', 'method': 'exclusive-writer-sha256-size-readback',
                                     'at': '2000-01-01T00:00:00Z'}})
        current['revision'] += 1
        if index == len(groups):
            current['files'] = [{k: v for k, v in r.items() if k != 'forCommit'} for r in current['staged']]
            current['staged'], current['commit'] = [], inventory['commit']
        lengths.append(len(encoded(current)))
    payload = sum(size for _, size in groups)
    uploads = initial + sum(lengths)
    downloads = initial + sum([initial] + lengths[:-1]) + sum(lengths)
    return {'uniquePayloadFiles': len(groups), 'payloadUploadBytes': payload, 'payloadReadbackBytes': payload,
            'assumedRemoteIdBytes': remote_id_bytes, 'bootstrapManifestBytes': initial,
            'manifestUpdates': len(batches), 'finalManifestBytes': lengths[-1],
            'largestManifestCheckpointBytes': max(lengths), 'manifestUploadBytes': uploads,
            'manifestReadbackAndPrereadBytes': downloads,
            'payloadAndManifestUploadBytes': payload + uploads,
            'payloadAndManifestDownloadBytes': payload + downloads,
            'newLiveContentBytesCeiling': payload + max(lengths),
            'newBytesIfAllWrittenManifestRevisionsWereRetained': payload + uploads,
            'maxUnpublishedBatchPayloadBytes': max(sum(size for (_, size), _ in batch) for batch in batches)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capabilities', action='store_true')
    parser.add_argument('--exclusive-writer', action='store_true')
    parser.add_argument('--repo', type=Path, default=check.ROOT)
    parser.add_argument('--commit')
    parser.add_argument('--path')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--expected-manifest-sha256')
    parser.add_argument('--work', type=Path)
    parser.add_argument('--folder-id')
    parser.add_argument('--max-bytes', type=int)
    args = parser.parse_args(argv)
    try:
        if args.capabilities:
            result = capabilities(args.exclusive_writer)
        else:
            need(all(getattr(args, key) is not None for key in ('commit', 'path', 'manifest',
                     'expected_manifest_sha256', 'work', 'folder_id', 'max_bytes')), 'All one-file preparation arguments are required')
            result = prepare_one(args.repo, args.commit, args.path, args.manifest,
                                 args.expected_manifest_sha256, args.work, args.folder_id, args.max_bytes,
                                 exclusive_writer=args.exclusive_writer)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, check.subprocess.CalledProcessError) as error:
        print('Transfer preparation blocked: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
