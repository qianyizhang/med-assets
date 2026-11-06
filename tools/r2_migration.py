#!/usr/bin/env python3
"""Plan a byte-preserving R2 copy of Git-pinned payloads; no network or Git writes."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import subprocess
import urllib.parse

from lfs_transport import parse_pointer

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path('sites/model-survey/app/src/content/assets/r2-trial.json')
TYPES = {'.glb': 'model/gltf-binary', '.png': 'image/png', '.webp': 'image/webp',
         '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.blend': 'application/octet-stream',
         '.raw': 'application/octet-stream', '.nii': 'application/octet-stream',
         '.nrrd': 'application/octet-stream', '.npz': 'application/octet-stream',
         '.svg': 'application/octet-stream', '.json': 'application/octet-stream',
         '.wav': 'audio/wav', '.mp4': 'video/mp4', '.ttf': 'font/ttf',
         '.stl': 'model/stl', '.obj': 'model/obj', '.gz': 'application/gzip'}


@dataclass(frozen=True)
class Payload:
    path: str
    sha256: str
    bytes: int
    name: str
    mediaType: str


def git(root, *args, data=None):
    return subprocess.check_output(['git', '--no-lazy-fetch', *args], cwd=root, input=data)


def inventory(root: Path, revision: str) -> tuple[str, list[Payload]]:
    revision = git(root, 'rev-parse', '--verify', '--end-of-options', revision+'^{commit}').decode().strip()
    blobs = []
    for item in git(root, 'ls-tree', '-rlz', revision).split(b'\0'):
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        mode, kind, oid, size = metadata.split()
        if kind == b'blob' and mode in (b'100644', b'100755'):
            blobs.append((name.decode(), oid.decode(), int(size)))
    small = {oid for _, oid, size in blobs if size <= 1024}
    stream = io.BytesIO(git(root, 'cat-file', '--batch', data=''.join(x+'\n' for x in sorted(small)).encode()))
    pointers = {}
    for _ in small:
        oid, kind, length = stream.readline().split()
        body = stream.read(int(length)); stream.read(1)
        if body.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            pointers[oid.decode()] = parse_pointer(body)
    payloads = []
    for name, oid, blob_size in blobs:
        pinned = pointers.get(oid)
        if pinned is None and blob_size < 1_000_000:
            continue
        path = root / name
        if path.is_symlink() or path.resolve() != path.absolute():
            raise ValueError(f'Payload path traverses a link: {name}')
        info = path.stat()
        expected_size = pinned[1] if pinned else blob_size
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValueError(f'Missing, changed or unhydrated payload: {name}')
        sha256 = hashlib.sha256(); blob_hash = hashlib.sha1(f'blob {info.st_size}\0'.encode())
        with path.open('rb') as handle:
            while chunk := handle.read(1024*1024):
                sha256.update(chunk); blob_hash.update(chunk)
        digest = sha256.hexdigest()
        if (pinned and digest != pinned[0]) or (not pinned and blob_hash.hexdigest() != oid):
            raise ValueError(f'Payload differs from the selected Git commit: {name}')
        suffix = path.suffix.lower()
        if suffix not in TYPES:
            raise ValueError(f'Payload format needs review: {name}')
        filename = re.sub(r'[^A-Za-z0-9_.-]', '_', path.name)
        payloads.append(Payload(name, digest, info.st_size, filename, TYPES[suffix]))
    return revision, payloads


def extend_manifest(existing: dict, revision: str, payloads: list[Payload]) -> dict:
    result = json.loads(json.dumps(existing))
    assets = result['assets']; by_hash = {x['sha256']: x for x in assets}
    for payload in payloads:
        previous = by_hash.get(payload.sha256)
        if previous:
            if previous['bytes'] != payload.bytes or previous['mediaType'] != payload.mediaType:
                raise ValueError('Existing R2 object identity/type conflicts with Git payload')
            aliases = set(previous.get('paths', [])) | {payload.path}
            if 'path' in previous:
                aliases.add(previous['path'])
            previous['paths'] = sorted(aliases)
        else:
            entry = asdict(payload)
            entry['source'] = f"https://github.com/qianyizhang/med-assets/blob/{revision}/{urllib.parse.quote(payload.path, safe='/')}"
            entry['attribution'] = 'Unmodified Git-pinned payload; preserve owning asset/source licenses, coordinates, provenance and review limits. No new blanket license.'
            assets.append(entry); by_hash[payload.sha256] = entry
    unique = {item.sha256: item for item in payloads}
    result['repositoryPayloads'] = {'revision': revision, 'count': len(unique),
                                   'paths': len(payloads), 'bytes': sum(x.bytes for x in unique.values())}
    result['scope'] = 'Git-pinned repository payloads, retained survey previews and frozen framework backup; transport replication does not promote review gates.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--manifest-output', type=Path, required=True, help='Fresh candidate file; existing files are refused')
    args = parser.parse_args()
    try:
        revision, payloads = inventory(ROOT, args.commit)
        result = extend_manifest(json.loads((ROOT/MANIFEST).read_text()), revision, payloads)
        with args.manifest_output.open('x') as handle:
            json.dump(result, handle, indent=2); handle.write('\n')
        print(json.dumps({'revision': revision, 'objects': len(payloads),
                          'bytes': sum(x.bytes for x in payloads),
                          'transferred': False}))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'R2 plan refused: {error}\n')


if __name__ == '__main__':
    main()
