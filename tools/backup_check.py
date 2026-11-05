#!/usr/bin/env python3
"""Offline, read-only current-tree backup inventory and copy planner."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile
import zlib

from verify import parse_pointer, require
from lfs_transport import Stop, unique_keys

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ('One committed tree, with LFS payload bytes; excludes Git history, other '
         'branches, untracked/private masters and external assets. No remote verification.')
POINTER_MARKER = b'version https://git-lfs.github.com/spec/'
GIT_COMMAND = ('git', '--no-lazy-fetch', '--no-replace-objects')
HEX256 = re.compile(r'[0-9a-f]{64}')
COMMIT_ID = re.compile(r'[0-9a-f]{40}|[0-9a-f]{64}')
REMOTE_TOKEN = re.compile(r'[A-Za-z0-9_-]{1,200}')
MAX_MANIFEST_BYTES = 16 * 1024 * 1024


def safe_path(name):
    """Keep exact portable snapshot paths; never normalize traversal or aliases."""
    if (not name or '\\' in name or ':' in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError(f'Unsafe snapshot path: {name!r}')
    return name


def git_env():
    # The explicit option fails closed on Git versions that do not support it.
    # Deny every transport too, including locally configured external helpers.
    return dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_ALLOW_PROTOCOL='',
                GIT_OPTIONAL_LOCKS='0', GIT_ATTR_NOSYSTEM='1')


def git(root, *args):
    return subprocess.run([*GIT_COMMAND, *args], cwd=root, env=git_env(),
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def expected_tree(root, revision):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision):
        raise ValueError('--commit requires a full lowercase commit ID, not a moving ref')
    commit = git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    if commit != revision:
        raise ValueError('Expected an exact commit object')
    rows = []
    for row in git(root, 'ls-tree', '-rlz', '--full-tree', commit).split(b'\0'):
        if not row:
            continue
        metadata, name = row.split(b'\t', 1)
        mode, kind, oid, size = metadata.split()
        name = safe_path(name.decode('utf-8'))
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise ValueError('Unsupported symlink/submodule/tree entry: ' + name)
        rows.append((name, oid.decode(), int(size)))
    if not rows:
        raise ValueError('Empty commit tree')
    # Source attributes must come from this commit, not the worktree or index.
    # info/attributes overrides --source too, so refuse that local override.
    info = Path(os.fsdecode(git(root, 'rev-parse', '--git-path', 'info/attributes')).strip())
    if not info.is_absolute():
        info = root / info
    if info.exists() and info.read_bytes().strip():
        raise ValueError('Local info/attributes override prevents a commit-only inventory')
    names = b''.join(name.encode() + b'\0' for name, _, _ in rows)
    attrs = subprocess.run(
        [*GIT_COMMAND, '-c', 'core.attributesFile=/dev/null',
         'check-attr', '--source=' + commit, '-z', '--stdin', 'filter'], cwd=root,
        env=git_env(),
        input=names, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.split(b'\0')[:-1]
    if len(attrs) != 3 * len(rows):
        raise ValueError('Incomplete committed attribute inventory')
    lfs_paths = {os.fsdecode(attrs[i]) for i in range(0, len(attrs), 3) if attrs[i+2] == b'lfs'}
    # One local Git process, streaming blobs rather than loading media into RAM.
    with subprocess.Popen([*GIT_COMMAND, 'cat-file', '--batch'], cwd=root,
                          env=git_env(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as proc:
        files = []
        try:
            for name, oid, size in rows:
                proc.stdin.write((oid + '\n').encode())
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                if header != [oid.encode(), b'blob', str(size).encode()]:
                    raise ValueError('Missing or unexpected Git blob: ' + name)
                digest = hashlib.sha256()
                remaining, prefix = size, b''
                while remaining:
                    chunk = proc.stdout.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError('Incomplete Git blob: ' + name)
                    prefix += chunk[:max(0, 1025 - len(prefix))]
                    digest.update(chunk)
                    remaining -= len(chunk)
                if proc.stdout.read(1) != b'\n':
                    raise ValueError('Incomplete Git blob framing: ' + name)
                is_lfs = name in lfs_paths or prefix.startswith(POINTER_MARKER)
                if is_lfs:
                    sha256, size = parse_pointer(prefix)
                else:
                    sha256 = digest.hexdigest()
                files.append({'path': name, 'sha256': sha256, 'size': size,
                              'kind': 'lfs' if is_lfs else 'git'})
        finally:
            proc.stdin.close()
            if proc.poll() is None:
                proc.terminate()
            proc.wait()
    sizes = {}
    for row in files:
        if row['sha256'] in sizes and sizes[row['sha256']] != row['size']:
            raise ValueError('Conflicting sizes for one SHA-256')
        sizes[row['sha256']] = row['size']
    lfs = {r['sha256']: r['size'] for r in files if r['kind'] == 'lfs'}
    return {'schemaVersion': 1, 'commit': commit, 'scope': SCOPE,
            'fileCount': len(files), 'uniqueObjectCount': len(sizes),
            'uniqueObjectBytes': sum(sizes.values()),
            'lfsPathCount': sum(r['kind'] == 'lfs' for r in files),
            'lfsUniqueObjectCount': len(lfs), 'lfsUniqueObjectBytes': sum(lfs.values()),
            'files': files}


class Tree:
    def __init__(self, root):
        self.root = root.absolute()
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError('Backup root must be a real local directory')

    @contextmanager
    def open(self, name):
        # dir_fd and O_NOFOLLOW also prevent swapping a checked ancestor to a link.
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        fds = []
        try:
            fds.append(os.open(self.root, flags | os.O_DIRECTORY))
            parts = safe_path(name).split('/')
            for part in parts[:-1]:
                fds.append(os.open(part, flags | os.O_DIRECTORY, dir_fd=fds[-1]))
            fd = os.open(parts[-1], flags, dir_fd=fds[-1])
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError('Not a regular file')
                yield stream, info.st_size
        finally:
            for fd in reversed(fds):
                os.close(fd)


class Zip:
    def __init__(self, archive):
        self.archive = archive
        self.entries = {}
        for entry in archive.infolist():
            safe_path(entry.filename[:-1] if entry.is_dir() else entry.filename)
            if entry.filename in self.entries:
                raise ValueError('Duplicate ZIP member: ' + entry.filename)
            self.entries[entry.filename] = entry

    @contextmanager
    def open(self, name):
        if name not in self.entries:
            raise FileNotFoundError(name)
        entry = self.entries[name]
        mode = stat.S_IFMT(entry.external_attr >> 16)
        if entry.is_dir() or mode not in (0, stat.S_IFREG) or entry.flag_bits & 1:
            raise ValueError('Nonregular or encrypted ZIP member')
        with self.archive.open(entry) as stream:
            yield stream, entry.file_size


def inspect(source, expected):
    try:
        with source.open(expected['path']) as (stream, size):
            prefix = stream.read(min(size, 1025))
            if expected['kind'] == 'lfs' and (
                    prefix.startswith(POINTER_MARKER) or b'oid sha256:' in prefix):
                return 'pointer_only'
            if size != expected['size']:
                return 'mismatched'
            digest = hashlib.sha256(prefix)
            remaining = size - len(prefix)
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    return 'mismatched'
                digest.update(chunk)
                remaining -= len(chunk)
            if stream.read(1):
                return 'mismatched'
            return 'verified' if digest.hexdigest() == expected['sha256'] else 'mismatched'
    except FileNotFoundError:
        return 'missing'
    except (OSError, ValueError, RuntimeError, EOFError, zipfile.BadZipFile, zlib.error):
        return 'unverifiable'


def check(inventory, source):
    files = []
    for expected in inventory['files']:
        status = inspect(source, expected)
        files.append(dict(expected, status=status,
                          action='none' if status == 'verified' else 'needs_copy'))
    counts = dict(Counter(row['status'] for row in files))
    return dict(inventory, files=files, counts=counts,
                completeCurrentTree=counts.get('verified', 0) == len(files),
                plannedCopyBytes=sum(row['size'] for row in files if row['action'] == 'needs_copy'),
                planOnly=True)


def exact_keys(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), 'Invalid fields: ' + label)


def digest(value):
    require(type(value) is str and HEX256.fullmatch(value), 'Invalid SHA-256')


def byte_size(value):
    require(type(value) is int and 0 <= value <= 2**63 - 1, 'Invalid byte size')


def manifest_record(row, staged):
    fields = {'path', 'sha256', 'size', 'remote', 'verification'}
    exact_keys(row, fields | ({'forCommit'} if staged else set()), 'file record')
    require(type(row['path']) is str, 'Invalid file path')
    safe_path(row['path'])
    digest(row['sha256'])
    byte_size(row['size'])
    if staged:
        require(type(row['forCommit']) is str and COMMIT_ID.fullmatch(row['forCommit']),
                'Staged file needs an exact source commit')
    remote = row['remote']
    exact_keys(remote, ('fileId', 'version', 'sha256', 'size'), 'remote identity')
    for key in ('fileId',):
        require(type(remote[key]) is str and REMOTE_TOKEN.fullmatch(remote[key]),
                'Invalid remote identity/version')
    require(remote['version'] is None or type(remote['version']) is str and REMOTE_TOKEN.fullmatch(remote['version']),
            'Invalid remote version')
    byte_size(remote['size'])
    if remote['sha256'] is not None:
        digest(remote['sha256'])
    verification = row['verification']
    exact_keys(verification, ('status', 'method', 'at'), 'verification')
    require(verification['status'] in ('verified', 'unverified', 'failed'),
            'Invalid verification status')
    if verification['status'] == 'unverified':
        require(verification['method'] == 'none' and verification['at'] is None,
                'Unverified records cannot claim a byte check')
    else:
        require(verification['method'] in ('sha256-size-readback', 'exclusive-writer-sha256-size-readback'),
                'Byte readback method required')
        require((verification['method'] == 'exclusive-writer-sha256-size-readback') == (remote['version'] is None),
                'Version evidence and verification method disagree')
        timestamp = verification['at']
        require(type(timestamp) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', timestamp),
                'Exact UTC verification time required')
        datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    if verification['status'] == 'verified':
        require((remote['sha256'], remote['size']) == (row['sha256'], row['size']),
                'Verified record conflicts with remote byte identity')


def load_current_manifest(path, expected_sha256):
    """Validate one supplied checkpoint. This is not a remote freshness/CAS check."""
    digest(expected_sha256)
    with Tree(path.parent).open(path.name) as (stream, size):
        require(size <= MAX_MANIFEST_BYTES, 'Current manifest exceeds local size limit')
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    require(len(raw) == size and hashlib.sha256(raw).hexdigest() == expected_sha256,
            'Stale or changed manifest: expected SHA-256 does not match')
    try:
        manifest = json.loads(raw, object_pairs_hook=unique_keys)
    except Stop as error:
        raise ValueError(str(error)) from error
    return validate_current_manifest(manifest)


def validate_current_manifest(manifest):
    """Validate a decoded local proposal without writing or publishing it."""
    exact_keys(manifest, ('schemaVersion', 'revision', 'commit', 'files', 'staged'), 'current manifest')
    require(type(manifest['schemaVersion']) is int and manifest['schemaVersion'] == 1,
            'Unsupported current manifest schema')
    require(type(manifest['revision']) is int and manifest['revision'] >= 0, 'Invalid manifest revision')
    commit = manifest['commit']
    require(commit is None or type(commit) is str and COMMIT_ID.fullmatch(commit),
            'Invalid manifest commit')
    require(type(manifest['files']) is list and type(manifest['staged']) is list,
            'File and staged records must be arrays')
    require(commit is not None or not manifest['files'], 'Current files need a commit binding')
    identities, sections, sizes = {}, {}, {}
    for section in ('files', 'staged'):
        paths = set()
        for row in manifest[section]:
            manifest_record(row, section == 'staged')
            require(row['sha256'] not in sizes or sizes[row['sha256']] == row['size'],
                    'Conflicting sizes for one payload SHA-256')
            sizes[row['sha256']] = row['size']
            require(row['path'] not in paths, 'Duplicate path in ' + section)
            paths.add(row['path'])
            remote_id = row['remote']['fileId']
            # One remote object/version may serve identical content at several paths.
            identity = (row['sha256'], row['size'], row['remote'], row['verification'])
            require(remote_id not in identities or identities[remote_id] == identity,
                    'Conflicting records for one remote file')
            require(remote_id not in sections or sections[remote_id] == section,
                    'One remote file cannot be both current and staged')
            identities[remote_id], sections[remote_id] = identity, section
    return manifest


def incremental_plan(inventory, manifest, manifest_sha256):
    """Plan the latest tree only. Every remote identity still needs a freshness check."""
    groups, wanted = {}, {}
    for row in inventory['files']:
        identity = row['sha256'], row['size']
        wanted[row['path']] = identity
        groups.setdefault(identity, []).append(row['path'])
    current = {row['path']: row for row in manifest['files']}
    if manifest['commit'] == inventory['commit']:
        require(all(row['path'] in wanted and (row['sha256'], row['size']) == wanted[row['path']]
                    for row in manifest['files']), 'Manifest mapping conflicts with selected commit')
    by_content = {}
    physical = {'files': {}, 'staged': {}}
    for section in ('files', 'staged'):
        for row in manifest[section]:
            physical[section][row['remote']['fileId']] = row['remote']['size']
            # Failed, mismatched or unknown-size objects cannot avoid a planned upload.
            if (row['verification']['status'] != 'failed'
                    and row['remote']['size'] == row['size']
                    and row['remote']['sha256'] in (None, row['sha256'])):
                identity = row['sha256'], row['size']
                by_content.setdefault(identity, []).append(dict(row, state=section))
    objects = []
    for (sha256, size), paths in sorted(groups.items()):
        candidates = by_content.get((sha256, size), [])
        verified_current = any(r['state'] == 'files' and r['verification']['status'] == 'verified'
                               for r in candidates)
        action = 'reuse_candidate' if verified_current else 'verify_candidate' if candidates else 'upload'
        reason = 'unchanged_content' if candidates else (
            'changed' if any(path in current and (current[path]['sha256'], current[path]['size'])
                             != (sha256, size) for path in paths)
            else 'unusable_current' if any(path in current for path in paths) else 'missing')
        objects.append({'sha256': sha256, 'size': size, 'paths': sorted(paths),
                        'commit': inventory['commit'], 'action': action, 'reason': reason,
                        'needsRemoteValidation': bool(candidates),
                        'candidates': candidates})
    upload = [r for r in objects if r['action'] == 'upload']
    reuse = [r for r in objects if r['action'] == 'reuse_candidate']
    pending = [r for r in objects if r['action'] == 'verify_candidate']
    current_bytes = sum(physical['files'].values())
    staged_bytes = sum(physical['staged'].values())
    largest_upload = max((r['size'] for r in upload), default=0)
    # These are path/mapping review candidates, never remote deletion instructions.
    replaced = [row for row in manifest['files'] if row['path'] in wanted
                and ((row['sha256'], row['size']) != wanted[row['path']]
                     or row['verification']['status'] == 'failed'
                     or row['remote']['size'] != row['size']
                     or row['remote']['sha256'] not in (None, row['sha256']))]
    obsolete = [row for row in manifest['files'] if row['path'] not in wanted]
    return {'schemaVersion': 1, 'commit': inventory['commit'], 'scope': SCOPE,
            'manifestSha256': manifest_sha256, 'manifestRevision': manifest['revision'],
            'remoteManifestFreshnessChecked': False, 'atomicRemoteCAS': False,
            'planOnly': True, 'remoteCoverageVerified': False,
            'objects': objects, 'replacementCandidates': replaced, 'obsoleteCandidates': obsolete,
            'stagedReviewCandidates': manifest['staged'],
            'budget': {'trackedFiles': len(wanted), 'trackedPathBytes': sum(r['size'] for r in inventory['files']),
                       'uniquePayloadFiles': len(objects), 'desiredUniqueBytes': sum(r['size'] for r in objects),
                       'largestPayloadBytes': max((r['size'] for r in objects), default=0),
                       'uploadFiles': len(upload), 'uploadBytes': sum(r['size'] for r in upload),
                       'reuseCandidateFiles': len(reuse), 'reuseCandidateBytes': sum(r['size'] for r in reuse),
                       'verifyCandidateFiles': len(pending), 'verifyCandidateBytes': sum(r['size'] for r in pending),
                       'existingCurrentBytes': current_bytes, 'existingStagedBytes': staged_bytes,
                       'additionalStagingPeakBytes': largest_upload,
                       'temporaryStagingPeakBytes': staged_bytes + largest_upload,
                       'initialStepTotalPeakBytes': current_bytes + staged_bytes + largest_upload,
                       'additionalStagingPeakBytesIfCandidatesFail': max((r['size'] for r in objects), default=0),
                       'uploadBytesIfAllCandidatesFail': sum(r['size'] for r in objects)},
            'budgetConditions': 'Upload budget assumes candidates pass remote validation. Staging estimates '
                                'allow one upload at a time and include listed temporary objects; initial-step '
                                'total is not a full-run peak. Recalculate after each accepted file; stop '
                                'before an unresolved replacement/removal. No transfer or retirement is authorized.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--commit', help='Exact full commit ID (not HEAD)')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--inventory', action='store_true', help='Print expected bytes only')
    source.add_argument('--backup-tree', type=Path, help='Local root with exact repository paths')
    source.add_argument('--backup-zip', type=Path, help='Local ZIP with exact repository paths')
    source.add_argument('--plan-manifest', type=Path, help='Dry-run incremental current-mirror plan')
    source.add_argument('--validate-manifest', type=Path, help='Validate current-state metadata only')
    parser.add_argument('--expected-manifest-sha256', help='Required local manifest checkpoint for plan/validation')
    args = parser.parse_args(argv)
    try:
        manifest_path = args.plan_manifest or args.validate_manifest
        if manifest_path:
            manifest = load_current_manifest(manifest_path, args.expected_manifest_sha256)
        elif args.expected_manifest_sha256 is not None:
            raise ValueError('Manifest checkpoint is only valid with a manifest mode')
        if args.validate_manifest:
            result, code = {'validCurrentManifest': True, 'revision': manifest['revision'],
                            'manifestSha256': args.expected_manifest_sha256,
                            'remoteManifestFreshnessChecked': False, 'atomicRemoteCAS': False}, 0
        else:
            require(args.commit is not None, '--commit is required for inventory, checks and planning')
            inventory = expected_tree(args.repo, args.commit)
        if args.plan_manifest:
            result, code = incremental_plan(inventory, manifest, args.expected_manifest_sha256), 0
        elif args.inventory:
            result, code = inventory, 0
        elif args.backup_tree:
            result = check(inventory, Tree(args.backup_tree))
            code = 0 if result['completeCurrentTree'] else 1
        elif args.backup_zip:
            with zipfile.ZipFile(args.backup_zip) as archive:
                result = check(inventory, Zip(archive))
            code = 0 if result['completeCurrentTree'] else 1
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return code
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print('Backup check failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
