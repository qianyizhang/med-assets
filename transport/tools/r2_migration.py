#!/usr/bin/env python3
"""Plan a bounded R2 upload of explicitly selected Git-pinned files."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import urllib.parse

from delivery_catalog import DELIVERY_INDEX, assets_by_path, current_paths, source_path
from lfs_transport import parse_pointer

ROOT = Path(__file__).resolve().parents[2]
MAX_SELECTION = 32
MAX_BYTES = 64_000_000
LFS_PREFIX = b'version https://git-lfs.github.com/spec/v1'
TYPES = {'.glb': 'model/gltf-binary', '.png': 'image/png', '.webp': 'image/webp',
         '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.blend': 'application/octet-stream',
         '.raw': 'application/octet-stream', '.nii': 'application/octet-stream',
         '.nrrd': 'application/octet-stream', '.npz': 'application/octet-stream',
         '.svg': 'application/octet-stream', '.json': 'application/octet-stream',
         '.wav': 'audio/wav', '.mp4': 'video/mp4', '.ttf': 'font/ttf',
         '.stl': 'model/stl', '.obj': 'model/obj', '.nii.gz': 'application/gzip',
         '.zip': 'application/zip'}


@dataclass(frozen=True)
class SelectedFile:
    name: str
    oid: str
    size: int
    pointer: str | None
    media_type: str


def git(root, *args) -> bytes:
    return subprocess.check_output(['git', '--no-lazy-fetch', *args], cwd=root)


def tree_entries(root: Path, revision: str, names: list[str]) -> dict[str, tuple[bytes, str, int]]:
    if not names:
        return {}
    entries = {}
    selected = set(names)
    for item in git(root, '--literal-pathspecs', 'ls-tree', '-lz', revision, '--', *names).split(b'\0'):
        if not item:
            continue
        metadata, raw_name = item.split(b'\t', 1)
        mode, kind, oid, size = metadata.split()
        name = raw_name.decode()
        if name in selected:
            entries[name] = (mode, oid.decode(), int(size) if kind == b'blob' else 0)
    return entries


def select_files(root: Path, revision: str, entries, names: list[str]) -> list[SelectedFile]:
    files = []
    total = 0
    for name in names:
        mode, oid, size = entries.get(name, (None, '', 0))
        if mode not in (b'100644', b'100755'):
            raise ValueError(f'Source is not a regular file at the selected Git revision: {name}')
        pointer = None
        if size <= 1024:
            committed = git(root, 'cat-file', 'blob', oid)
            if committed.startswith(LFS_PREFIX):
                pointer, size = parse_pointer(committed)
        total += size
        if not 0 < size <= MAX_BYTES or total > MAX_BYTES:
            raise ValueError('Selected sources exceed the byte bound')
        lower = name.lower()
        suffix = '.nii.gz' if lower.endswith('.nii.gz') else Path(lower).suffix
        if suffix not in TYPES:
            raise ValueError(f'Payload format needs review: {name}')
        if suffix == '.zip' and not name.endswith('.zip'):
            raise ValueError(f'ZIP assets need a .zip filename: {name}')
        files.append(SelectedFile(name, oid, size, pointer, TYPES[suffix]))
    return files


def verified_digest(root: Path, file: SelectedFile) -> str:
    path = root / file.name
    if path.resolve() != path or path.is_symlink():
        raise ValueError(f'Payload path traverses a link: {file.name}')
    sha256 = hashlib.sha256()
    blob_hash = hashlib.sha1(f'blob {file.size}\0'.encode())
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != file.size:
            raise ValueError(f'Missing, changed or unhydrated payload: {file.name}')
        count = 0
        while chunk := handle.read(1024 * 1024):
            if count == 0 and file.pointer is None and chunk.startswith(LFS_PREFIX):
                raise ValueError(f'Malformed Git LFS pointer: {file.name}')
            count += len(chunk)
            if count > file.size:
                raise ValueError(f'Payload changed during verification: {file.name}')
            sha256.update(chunk)
            if file.pointer is None:
                blob_hash.update(chunk)
    digest = sha256.hexdigest()
    expected = file.pointer or file.oid
    actual = digest if file.pointer else blob_hash.hexdigest()
    if count != file.size or actual != expected:
        raise ValueError(f'Payload differs from the selected Git commit: {file.name}')
    return digest


def remove_binding(asset: dict, name: str) -> None:
    remaining = [path for path in current_paths(asset) if path != name]
    asset['paths'] = remaining
    if asset.get('path') == name:
        asset.pop('path')
        if remaining:
            asset['path'] = remaining[0]
    asset['historicalPaths'] = sorted({*asset.get('historicalPaths', []), name})


def plan_upload(root: Path, commit: str, catalog: dict, names: list[str], retire: list[str]) -> tuple[dict, dict]:
    root = root.resolve()
    revision = git(root, 'rev-parse', '--verify', '--end-of-options', commit + '^{commit}').decode().strip()
    if revision != git(root, 'rev-parse', 'HEAD').decode().strip():
        raise ValueError('Selected Git revision differs from checkout HEAD')
    paths = [source_path(name) for name in names + retire]
    if not 0 < len(paths) <= MAX_SELECTION or len(set(paths)) != len(paths):
        raise ValueError('Select between 1 and 32 distinct upload or retirement paths')
    result = deepcopy(catalog)
    bindings = assets_by_path(result)
    entries = tree_entries(root, revision, paths)
    for name in retire:
        if name in entries or name not in bindings:
            raise ValueError(f'Retirement requires a declared path absent from Git HEAD: {name}')
        remove_binding(bindings.pop(name), name)

    files = select_files(root, revision, entries, sorted(names))
    by_digest = {}
    for asset in result['assets']:
        by_digest.setdefault(asset['sha256'], []).append(asset)
    objects = {}
    for file in files:
        digest = verified_digest(root, file)
        previous = bindings.get(file.name)
        addrs = by_digest.get(digest, [])
        if any((route['bytes'], route['mediaType']) != (file.size, file.media_type) for route in addrs):
            raise ValueError(f'Existing R2 object identity or type conflicts with source: {file.name}')
        if previous is not None and previous['sha256'] == digest:
            target = previous
        elif len(addrs) == 1:
            target = addrs[0]
        elif addrs:
            raise ValueError(f'Multiple existing addresses require an explicit catalog binding: {file.name}')
        else:
            filename = re.sub(r'[^A-Za-z0-9_.-]', '_', Path(file.name).name)
            target = {
                'path': file.name, 'name': filename, 'sha256': digest,
                'bytes': file.size, 'mediaType': file.media_type,
                'source': f"https://github.com/qianyizhang/med-assets/blob/{revision}/{urllib.parse.quote(file.name, safe='/')}",
                'attribution': 'Unmodified Git-pinned payload. Preserve the owning package licenses, provenance and review limits.',
            }
            result['assets'].append(target)
            by_digest[digest] = [target]

        if previous is not target:
            if previous is not None:
                remove_binding(previous, file.name)
            aliases = sorted({*current_paths(target), file.name})
            if 'path' not in target:
                target['path'] = file.name
            if aliases != current_paths(target):
                target['paths'] = aliases
        objects.setdefault(digest, {'sourcePath': file.name, 'sha256': digest, 'bytes': file.size,
                                    'name': target['name'], 'mediaType': target['mediaType']})
    plan = {'schemaVersion': 1, 'revision': revision, 'objectCount': len(objects),
            'totalBytes': sum(item['bytes'] for item in objects.values()), 'objects': list(objects.values())}
    return plan, result


def write_outputs(outputs) -> None:
    created = []
    try:
        for path, value in outputs:
            raw = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
            with path.open('x', encoding='utf-8') as stream:
                created.append(path)
                stream.write(raw)
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--catalog', type=Path, help='Reviewed delivery catalog; defaults to the checkout index')
    parser.add_argument('--path', action='append', default=[], help='Exact repository-relative upload source; repeat as needed')
    parser.add_argument('--retire-path', action='append', default=[], help='Drop a removed current alias while retaining its address')
    parser.add_argument('--plan-output', type=Path, help='Fresh upload-plan file')
    parser.add_argument('--catalog-output', type=Path, help='Fresh candidate catalog when admitting or changing paths')
    args = parser.parse_args()
    try:
        catalog = json.loads((args.catalog or args.root / DELIVERY_INDEX).read_text())
        plan, result = plan_upload(args.root, args.commit, catalog, args.path, args.retire_path)
        if bool(args.path) != bool(args.plan_output):
            raise ValueError('--path and --plan-output are required together')
        if result != catalog and not args.catalog_output:
            raise ValueError('A changed delivery catalog requires --catalog-output')
        outputs = [(path, value) for path, value in ((args.catalog_output, result), (args.plan_output, plan)) if path]
        write_outputs(outputs)
        print(json.dumps({'revision': plan['revision'], 'objects': plan['objectCount'],
                          'bytes': plan['totalBytes'], 'transferred': False}))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'R2 plan refused: {error}\n')


if __name__ == '__main__':
    main()
