#!/usr/bin/env python3
"""Offline, read-only current-tree backup inventory and copy planner."""
import argparse
from collections import Counter
from contextlib import contextmanager
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

from verify import parse_pointer

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ('One committed tree, with LFS payload bytes; excludes Git history, other '
         'branches, untracked/private masters and external assets. No remote verification.')
POINTER_MARKER = b'version https://git-lfs.github.com/spec/'
GIT_COMMAND = ('git', '--no-lazy-fetch', '--no-replace-objects')


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--commit', required=True, help='Exact full commit ID (not HEAD)')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--inventory', action='store_true', help='Print expected bytes only')
    source.add_argument('--backup-tree', type=Path, help='Local root with exact repository paths')
    source.add_argument('--backup-zip', type=Path, help='Local ZIP with exact repository paths')
    args = parser.parse_args(argv)
    try:
        inventory = expected_tree(args.repo, args.commit)
        if args.inventory:
            result, code = inventory, 0
        elif args.backup_tree:
            result = check(inventory, Tree(args.backup_tree))
            code = 0 if result['completeCurrentTree'] else 1
        else:
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
