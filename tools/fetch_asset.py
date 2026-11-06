#!/usr/bin/env python3
"""Fetch one Git-pinned payload into a verified local cache, without Git writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
    if pointer.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        return parse_pointer(pointer)
    return hashlib.sha256(pointer).hexdigest(), len(pointer)


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


def fetch_asset(cache: Path, name: str, digest: str, size: int, *, open_url=None, download_name=None) -> Path:
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest) or size < 1:
        raise ValueError('Invalid pinned asset identity')
    cache = cache.absolute()
    cache.mkdir(parents=True, exist_ok=True)
    if cache.resolve() != cache:
        raise ValueError('Asset cache must not traverse symlinks')
    target = cache / digest
    if verified_file(target, digest, size):
        return target
    filename = download_name or PurePosixPath(name).name
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
            if not verified_file(target, digest, size):
                raise ValueError('Concurrent cache entry disappeared before verification')
        return target
    finally:
        Path(temporary).unlink(missing_ok=True)



def route_name(root: Path, digest: str, size: int, name: str) -> str:
    manifest = json.loads((root / 'sites/model-survey/app/src/content/assets/r2-trial.json').read_text())
    for asset in manifest['assets']:
        if asset['sha256'] == digest and asset['bytes'] == size:
            filename = asset['name']
            if not filename or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in filename):
                raise ValueError('Invalid published asset filename')
            return filename
    raise ValueError('Selected Git payload has no published R2 delivery reference')


def hydrate(root: Path, name: str, cached: Path, digest: str, size: int) -> Path:
    target = root / name
    if target.is_symlink() or target.parent.resolve() != target.parent.absolute():
        raise ValueError('Hydration path must not traverse symlinks')
    before = target.read_bytes()
    if len(before) == size and hashlib.sha256(before).hexdigest() == digest:
        return target
    if parse_pointer(before) != (digest, size):
        raise ValueError('Working file differs from the selected pointer; refusing overwrite')
    descriptor, temporary = tempfile.mkstemp(prefix='.hydrate-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output, cached.open('rb') as source:
            shutil.copyfileobj(source, output, 1024*1024)
            output.flush(); os.fsync(output.fileno())
        if not verified_file(Path(temporary), digest, size):
            raise ValueError('Hydration copy failed verification')
        if target.is_symlink() or target.read_bytes() != before:
            raise ValueError('Working pointer changed during hydration; refusing overwrite')
        os.replace(temporary, target)
        return target
    finally:
        Path(temporary).unlink(missing_ok=True)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='Exact payload path at the selected Git commit')
    parser.add_argument('--hydrate', action='store_true', help='Restore only a matching LFS pointer at its original path')
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.artifacts/asset-cache')
    args = parser.parse_args()
    try:
        digest, size = pinned_asset(ROOT, args.commit, args.path)
        if args.hydrate:
            target = ROOT / args.path
            if target.is_file() and not target.is_symlink() and target.stat().st_size == size and not target.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1\n') and verified_file(target, digest, size):
                print(target)
                return 0
        filename = route_name(ROOT, digest, size, args.path)
        cached = fetch_asset(args.cache_dir, args.path, digest, size, download_name=filename)
        print(hydrate(ROOT, args.path, cached, digest, size) if args.hydrate else cached)
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Asset fetch failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
