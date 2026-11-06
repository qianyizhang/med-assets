#!/usr/bin/env python3
"""Fetch one Git-pinned LFS payload into a verified local cache, without Git writes."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import urllib.parse
import urllib.request

from lfs_transport import parse_pointer

ROOT = Path(__file__).resolve().parents[1]
ASSET_ORIGIN = 'https://med-assets-model-survey.landy123007.chatgpt.site'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Asset redirects are refused')


def pinned_asset(root: Path, revision: str, name: str) -> tuple[str, int]:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or str(path) != name
            or any(part in ('.', '..') for part in path.parts)
            or '\\' in name or any(ord(c) < 32 for c in name)):
        raise ValueError('Use an exact repository-relative file path')
    commit = subprocess.check_output(
        ['git', '--no-lazy-fetch', 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}'],
        cwd=root, text=True).strip()
    pointer = subprocess.check_output(
        ['git', '--no-lazy-fetch', 'show', commit + ':' + name], cwd=root)
    return parse_pointer(pointer)


def verified_file(path: Path, digest: str, size: int) -> bool:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return False
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != size:
            raise ValueError('Cached asset is not a matching regular file')
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != digest:
        raise ValueError('Cached asset checksum mismatch')
    return True


def fetch_asset(cache: Path, name: str, digest: str, size: int, *, open_url=None) -> Path:
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest) or size < 1:
        raise ValueError('Invalid pinned asset identity')
    cache = cache.absolute()
    cache.mkdir(parents=True, exist_ok=True)
    if cache.resolve() != cache:
        raise ValueError('Asset cache must not traverse symlinks')
    target = cache / digest
    if verified_file(target, digest, size):
        return target
    filename = PurePosixPath(name).name
    url = ASSET_ORIGIN + '/assets/' + digest + '/' + urllib.parse.quote(filename, safe='')
    opener = open_url or urllib.request.build_opener(NoRedirect()).open
    fd, temporary = tempfile.mkstemp(prefix='.asset-', dir=cache)
    try:
        with os.fdopen(fd, 'wb') as output:
            request = urllib.request.Request(url, headers={
                'Accept-Encoding': 'identity', 'User-Agent': 'med-assets-asset-fetch/1.0'})
            with opener(request, timeout=120) as response:
                if response.status != 200:
                    raise ValueError('Asset download did not return HTTP 200')
                if response.headers.get('Content-Encoding', 'identity') != 'identity':
                    raise ValueError('Asset download unexpectedly changed transport encoding')
                count = 0
                actual = hashlib.sha256()
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > size:
                        raise ValueError('Asset download exceeds its pinned size')
                    output.write(chunk)
                    actual.update(chunk)
                if count != size or actual.hexdigest() != digest:
                    raise ValueError('Downloaded asset size or checksum mismatch')
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, target)  # Never overwrite another caller's cache entry.
        except FileExistsError:
            verified_file(target, digest, size)
        return target
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='Exact LFS file path at the selected Git commit')
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.artifacts/asset-cache')
    args = parser.parse_args()
    try:
        digest, size = pinned_asset(ROOT, args.commit, args.path)
        print(fetch_asset(args.cache_dir, args.path, digest, size))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Asset fetch failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
