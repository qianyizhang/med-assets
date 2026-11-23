#!/usr/bin/env python3
"""Fetch one Git-pinned payload into a verified local cache, without Git writes."""
from __future__ import annotations

import argparse
import hashlib
import gzip
import io
import json
import shutil
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import urllib.parse
import urllib.request

from delivery_catalog import DELIVERY_INDEX, current_paths, source_path
from med_assets.artifacts import install_verified
from lfs_transport import parse_pointer

ROOT = Path(__file__).resolve().parents[2]
ASSET_ORIGIN = 'https://med-assets-model-survey.landy123007.chatgpt.site'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Asset redirects are refused')


def pinned_asset(root: Path, revision: str, name: str) -> tuple[str, int]:
    source_path(name)
    commit = subprocess.check_output(
        ['git', '--no-lazy-fetch', 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}'],
        cwd=root, text=True).strip()
    raw = subprocess.run(['git', '--no-lazy-fetch', 'show', commit + ':' + name],
                         cwd=root, capture_output=True)
    if raw.returncode:
        # Some package exports preserve their original identity in a tracked gzip member.
        if not name.endswith('.json'):
            raw.check_returncode()
        packed = subprocess.check_output(['git', '--no-lazy-fetch', 'show', commit + ':' + name + '.gz'], cwd=root)
        contract_name = str(PurePosixPath(name).with_name('EXPORT_CONTRACT.json'))
        contract = json.loads(subprocess.check_output(['git', '--no-lazy-fetch', 'show', commit + ':' + contract_name], cwd=root))
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
            decoded = stream.read(64_000_001)
        digest = hashlib.sha256(decoded).hexdigest()
        if len(decoded) > 64_000_000 or contract['sha256'].get(PurePosixPath(name).name) != digest:
            raise ValueError('Compressed export differs from the pinned export contract')
        return digest, len(decoded)
    pointer = raw.stdout
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
    manifest = json.loads((root / DELIVERY_INDEX).read_text())
    matches = [asset for asset in manifest['assets'] if (asset['sha256'], asset['bytes']) == (digest, size)]
    current = [asset for asset in matches if name in current_paths(asset)]
    historical = [asset for asset in matches if name in asset.get('historicalPaths', [])]
    preferred = current or historical or matches
    if len(preferred) > 1:
        preferred = [asset for asset in preferred if asset['name'] == PurePosixPath(name).name]
    if len(preferred) != 1:
        raise ValueError('Selected Git payload has no unambiguous published R2 delivery reference')
    filename = preferred[0]['name']
    if not filename or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in filename):
        raise ValueError('Invalid published asset filename')
    return filename


def working_pointer(target: Path, digest: str, size: int) -> bytes | None:
    """Return the replaceable pointer, or None when the payload is already exact."""
    if target.is_symlink() or target.parent.resolve() != target.parent.absolute():
        raise ValueError('Hydration path must not traverse symlinks')
    with target.open('rb') as stream:
        if os.fstat(stream.fileno()).st_size == size:
            if hashlib.file_digest(stream, 'sha256').hexdigest() == digest:
                return None
            stream.seek(0)
        before = stream.read(1024)
        if before.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            if parse_pointer(before) == (digest, size):
                return before
    raise ValueError('Working file differs from the selected revision; preserving local contents')


def hydrate(root: Path, name: str, cached: Path, digest: str, size: int) -> Path:
    target = root / name
    before = working_pointer(target, digest, size)
    if before is None:
        return target
    original_mode = stat.S_IMODE(target.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(prefix='.hydrate-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output, cached.open('rb') as source:
            shutil.copyfileobj(source, output, 1024*1024)
            output.flush(); os.fsync(output.fileno())
        if not verified_file(Path(temporary), digest, size):
            raise ValueError('Hydration copy failed verification')
        if target.is_symlink() or target.read_bytes() != before:
            raise ValueError('Working pointer changed during hydration; refusing overwrite')
        os.chmod(temporary, original_mode)
        os.replace(temporary, target)
        return target
    finally:
        Path(temporary).unlink(missing_ok=True)

def restore_compressed(target: Path, digest: str, size: int) -> bool:
    packed = target.with_suffix('.json.gz')
    if target.exists() or target.suffix != '.json' or not packed.is_file():
        return False
    if packed.absolute() != packed.resolve() or target.is_symlink():
        raise ValueError('Compressed hydration must not traverse symlinks')
    with gzip.open(packed, 'rb') as stream, tempfile.NamedTemporaryFile(dir=target.parent) as staged:
        staged.write(stream.read(size + 1))
        staged.flush()
        install_verified(Path(staged.name), target, {'path': target.name, 'sha256': digest, 'bytes': size})
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='Exact payload path at the selected Git commit')
    parser.add_argument('--hydrate', action='store_true', help='Restore the exact asset at its original path from a matching LFS pointer or its verified compressed source')
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.artifacts/asset-cache')
    args = parser.parse_args()
    try:
        digest, size = pinned_asset(ROOT, args.commit, args.path)
        target = ROOT / args.path
        if args.hydrate and restore_compressed(target, digest, size):
            print(target)
            return 0
        if args.hydrate:
            if working_pointer(target, digest, size) is None:
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
