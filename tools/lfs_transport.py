#!/usr/bin/env python3
"""Bounded, reviewed-manifest transport for qianyizhang/med-assets (stdlib only)."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zlib

REPOSITORY = 'qianyizhang/med-assets'
LFS_URL = f'https://github.com/{REPOSITORY}.git/info/lfs'
SOURCE_HOST = 'anatomy-verification.landy123007.chatgpt.site'
SOURCE_HOSTS = frozenset({SOURCE_HOST, 'anatomy-airway-review.landy123007.chatgpt.site',
                          'heart-anatomy-imaging-lab.landy123007.chatgpt.site',
                          'anatomy-dental-review.landy123007.chatgpt.site',
                          'anatomy-head-neck-review.landy123007.chatgpt.site'})
MAX_MANIFEST = 131_072
MAX_OBJECTS = 32
MAX_TOTAL = 40_000_000
MAX_OBJECT = 40_000_000
HEX64 = re.compile(r'[0-9a-f]{64}')
HEX40 = re.compile(r'[0-9a-f]{40}')
MANIFEST_PATH = re.compile(r'transport/manifests/([0-9a-f]{64})\.json')


class Stop(RuntimeError):
    """Safe, intentionally URL/header/credential-free error."""


def require(condition, message):
    if not condition:
        raise Stop(message)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def integer(value, maximum):
    return type(value) is int and 0 < value <= maximum


def https_url(url):
    require(isinstance(url, str) and not any(c.isspace() for c in url), 'Invalid HTTPS URL')
    try:
        parsed = urllib.parse.urlsplit(url)
        valid = parsed.scheme == 'https' and parsed.hostname and parsed.port in (None, 443)
        valid = valid and parsed.username is None and parsed.password is None
    except ValueError:
        valid = False
    require(valid, 'Invalid HTTPS URL')
    return parsed


def source_url(url):
    p = https_url(url)
    require(p.hostname in SOURCE_HOSTS and not p.query and not p.fragment, 'Source host/query not allowed')
    require(re.fullmatch(r'/review/[A-Za-z0-9_./-]+', p.path) is not None, 'Source path not allowed')
    require('//' not in p.path and not any(x in ('.', '..') for x in p.path.split('/')), 'Source path traversal')


def validate_manifest(raw, digest):
    require(HEX64.fullmatch(digest or '') is not None, 'Invalid manifest SHA-256')
    require(len(raw) <= MAX_MANIFEST and hashlib.sha256(raw).hexdigest() == digest, 'Manifest byte/hash mismatch')
    try:
        m = json.loads(raw, object_pairs_hook=unique_keys)
    except (ValueError, UnicodeError):
        raise Stop('Invalid manifest JSON') from None
    require(type(m) is dict and set(m) <= {'objects', 'totalBytes', 'objectCount', 'scope'}, 'Unexpected manifest fields')
    objects = m.get('objects')
    require(type(objects) is list and 0 < len(objects) <= MAX_OBJECTS, 'Object count outside fixed cap')
    require(integer(m.get('totalBytes'), MAX_TOTAL), 'Total outside fixed cap')
    if 'objectCount' in m:
        require(type(m['objectCount']) is int and m['objectCount'] == len(objects), 'Object count mismatch')
    if 'scope' in m:
        require(type(m['scope']) is str and len(m['scope']) <= 2000, 'Invalid scope text')
    seen, transfer_total = set(), 0
    for o in objects:
        required = {'file', 'sha256', 'bytes', 'url'}
        optional = {'encoding', 'transportSha256', 'transportBytes'}
        require(type(o) is dict and required <= set(o) <= required | optional, 'Unexpected object fields')
        require(type(o['sha256']) is str and HEX64.fullmatch(o['sha256']) is not None, 'Invalid object SHA-256')
        require(o['sha256'] not in seen, 'Duplicate object OID; deduplicate the manifest')
        seen.add(o['sha256'])
        require(integer(o['bytes'], MAX_OBJECT), 'Object outside fixed cap')
        file = o['file']
        require(type(file) is str and 0 < len(file) <= 240 and not file.startswith('/') and '\\' not in file, 'Invalid display path')
        require(re.fullmatch(r'[A-Za-z0-9_./-]+', file) is not None and all(part not in ('', '.', '..') for part in file.split('/')), 'Display path traversal/control characters')
        require(PurePosixPath(file).suffix in ('.glb', '.webp', '.png'), 'Unreviewed format')
        source_url(o['url'])
        encoding = o.get('encoding', 'identity')
        require(encoding in ('identity', 'gzip'), 'Unsupported encoding')
        if encoding == 'gzip':
            require(PurePosixPath(file).suffix == '.glb', 'Only reviewed GLB gzip transport is enabled')
            require(integer(o.get('transportBytes'), MAX_OBJECT), 'Gzip transport outside fixed cap')
            require(type(o.get('transportSha256')) is str and HEX64.fullmatch(o['transportSha256']) is not None, 'Missing gzip transport hash')
        else:
            require('transportBytes' not in o and 'transportSha256' not in o, 'Identity object must not have separate transport fields')
        transfer_total += o.get('transportBytes', o['bytes'])
    require(sum(o['bytes'] for o in objects) == m['totalBytes'], 'Total byte mismatch')
    require(transfer_total <= MAX_TOTAL, 'Aggregate transport cap exceeded')
    return m


def load_manifest(root, digest):
    require(HEX64.fullmatch(digest or '') is not None, 'Invalid manifest SHA-256')
    path = root / 'transport' / 'manifests' / (digest + '.json')
    require(all(not p.is_symlink() for p in (path, path.parent, path.parent.parent)), 'Manifest symlink refused')
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_MANIFEST + 1)
    except OSError:
        raise Stop('Committed manifest unavailable') from None
    return validate_manifest(raw, digest)


def git(root, *args, data=None, storage=None):
    command = ['git']
    if storage is not None:
        for key, value in [('lfs.url', LFS_URL), ('lfs.pushurl', LFS_URL),
                           ('remote.origin.lfsurl', LFS_URL), ('remote.origin.lfspushurl', LFS_URL),
                           ('lfs.remote.autodetect', 'false'), ('lfs.storage', str(storage))]:
            command += ['-c', key + '=' + value]
    try:
        result = subprocess.run(command + list(args), cwd=root, input=data, capture_output=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        raise Stop('Git command unavailable or timed out') from None
    if result.returncode:
        # Do not echo stderr: an LFS server can include signed URLs in diagnostics.
        billing = any(x in result.stderr.lower() for x in (b'quota', b'billing', b'budget', b'bandwidth', b'payment'))
        raise Stop('LFS quota/billing error; stop for review' if billing else 'Git/LFS command failed; stop without retry or permission changes')
    return result.stdout


def select_run_manifest(root, env):
    require(env.get('GITHUB_ACTIONS') == 'true' and env.get('GITHUB_REPOSITORY') == REPOSITORY, 'Wrong execution repository')
    require(env.get('GITHUB_REF') == 'refs/heads/main', 'Only main may upload')
    sha = env.get('GITHUB_SHA', '')
    require(HEX40.fullmatch(sha) is not None, 'Invalid main commit')
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == sha, 'Checkout does not match triggering commit')
    event = env.get('GITHUB_EVENT_NAME')
    if event == 'workflow_dispatch':
        digest = env.get('MANIFEST_SHA256', '')
        require(HEX64.fullmatch(digest) is not None, 'Invalid dispatch manifest SHA-256')
        return digest
    require(event == 'push', 'Untrusted trigger refused')
    before = env.get('PUSH_BEFORE', '')
    require(HEX40.fullmatch(before) is not None and before != '0' * 40, 'Invalid push base')
    # Exactly one manifest-only addition. No updates/deletions, mixed code edits or multi-batch pushes.
    changes = git(root, 'diff', '--name-status', '--no-renames', before, sha).decode().splitlines()
    require(len(changes) == 1 and changes[0].startswith('A\t'), 'Push must add exactly one manifest and no other files')
    match = MANIFEST_PATH.fullmatch(changes[0][2:])
    require(match is not None, 'Push did not add a content-addressed manifest')
    return match.group(1)


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = https_url(req.full_url), https_url(newurl)
        require((old.hostname, old.port or 443) == (new.hostname, new.port or 443), 'Cross-origin redirect refused')
        if old.hostname in SOURCE_HOSTS:
            source_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_bytes(url, limit, headers=None, data=None):
    https_url(url)
    opener = urllib.request.build_opener(SameOriginRedirect())
    request = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with opener.open(request, timeout=60) as response:
            body = response.read(limit + 1)
    except urllib.error.HTTPError as error:
        raise Stop(f'HTTP {error.code}; stop for source/auth/quota review') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise Stop('HTTPS request failed; no automatic retry') from None
    require(len(body) <= limit, 'Response exceeded exact byte cap')
    return body


def verify_bytes(data, o):
    require(len(data) == o['bytes'] and hashlib.sha256(data).hexdigest() == o['sha256'], 'Object size/SHA-256 mismatch')
    kind = PurePosixPath(o['file']).suffix
    if kind == '.glb':
        valid = len(data) >= 20 and data[:4] == b'glTF' and struct.unpack_from('<II', data, 4) == (2, len(data))
    elif kind == '.webp':
        valid = len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP' and struct.unpack_from('<I', data, 4)[0] + 8 == len(data)
    else:
        valid = len(data) >= 24 and data[:16] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' and all(struct.unpack_from('>II', data, 16))
    require(valid, 'Unmatched file signature/header')


def download_source(o):
    size, digest = o.get('transportBytes', o['bytes']), o.get('transportSha256', o['sha256'])
    data = http_bytes(o['url'], size, {'Accept-Encoding': 'identity', 'User-Agent': 'med-assets-bounded-lfs/1.0'})
    require(len(data) == size and hashlib.sha256(data).hexdigest() == digest, 'Source transport size/hash mismatch')
    if o.get('encoding') == 'gzip':
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as compressed:
                data = compressed.read(o['bytes'] + 1)
        except (OSError, EOFError, zlib.error):
            raise Stop('Invalid gzip transport') from None
    verify_bytes(data, o)
    return data


def batch(objects):
    payload = json.dumps({'operation': 'download', 'transfers': ['basic'],
                          'objects': [{'oid': o['sha256'], 'size': o['bytes']} for o in objects]}).encode()
    raw = http_bytes(LFS_URL + '/objects/batch', 262_144,
                     {'Accept': 'application/vnd.git-lfs+json', 'Content-Type': 'application/vnd.git-lfs+json'}, payload)
    try:
        result = json.loads(raw, object_pairs_hook=unique_keys)['objects']
        require(type(result) is list and len(result) == len(objects), 'Unexpected LFS Batch count')
        by_oid = {o['oid']: o for o in result}
        require(len(by_oid) == len(result) and set(by_oid) == {o['sha256'] for o in objects}, 'Unexpected LFS Batch OIDs')
        for o in objects:
            require(type(by_oid[o['sha256']]['size']) is int and by_oid[o['sha256']]['size'] == o['bytes'], 'LFS Batch size mismatch')
        return by_oid
    except (KeyError, TypeError, ValueError):
        raise Stop('Invalid LFS Batch response') from None


def missing_objects(objects, remote):
    missing = set()
    for o in objects:
        row = remote[o['sha256']]
        if 'error' in row:
            require(type(row['error']) is dict and row['error'].get('code') == 404, 'Non-missing LFS error; stop for quota/auth review')
            missing.add(o['sha256'])
        else:
            require(type(row.get('actions')) is dict and 'download' in row['actions'], 'LFS download action missing')
    return missing


def readback(objects):
    remote, rows = batch(objects), []
    for o in objects:
        row = remote[o['sha256']]
        require('error' not in row, 'GitHub readback object unavailable')
        try:
            action = row['actions']['download']
            url, headers = action['href'], action.get('header', {})
            https_url(url)  # Only fixed GitHub Batch responses supply this temporary URL.
            require(type(headers) is dict and all(type(k) is str and type(v) is str for k, v in headers.items()), 'Invalid LFS action headers')
        except (KeyError, TypeError):
            raise Stop('Invalid LFS download action') from None
        verify_bytes(http_bytes(url, o['bytes'], headers), o)
        rows.append({'oid': o['sha256'], 'bytes': o['bytes'], 'file': o['file'], 'verified': True})
        print('GITHUB READBACK VERIFIED', o['sha256'], o['bytes'], flush=True)
    return rows


def upload_and_readback(root, manifest, work):
    objects = manifest['objects']
    for o in objects:
        (work / o['sha256']).write_bytes(download_source(o))
        print('SOURCE VERIFIED', o['sha256'], o['bytes'], flush=True)
    # No upload before EVERY source and destination preflight check passes.
    missing = missing_objects(objects, batch(objects))
    storage = work / 'lfs'
    origin = git(root, 'remote', 'get-url', '--push', 'origin').decode().strip()
    require(origin in (f'https://github.com/{REPOSITORY}', f'https://github.com/{REPOSITORY}.git'), 'Unexpected Git destination')
    git(root, 'lfs', 'install', '--local', storage=storage)
    for o in objects:
        pointer = git(root, 'lfs', 'clean', 'approved-' + o['sha256'], data=(work / o['sha256']).read_bytes(), storage=storage)
        expected = f"version https://git-lfs.github.com/spec/v1\noid sha256:{o['sha256']}\nsize {o['bytes']}\n".encode()
        require(pointer == expected, 'Generated LFS pointer mismatch')
    for o in objects:
        if o['sha256'] in missing:
            git(root, 'lfs', 'push', '--object-id', 'origin', o['sha256'], storage=storage)
            print('UPLOAD COMMAND PASSED', o['sha256'], o['bytes'], flush=True)
        else:
            print('ALREADY PRESENT SKIPPED', o['sha256'], o['bytes'], flush=True)
    return {'uploadedObjects': len(missing), 'existingObjectsSkipped': len(objects) - len(missing), 'objects': readback(objects)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('validate', 'run', 'readback'))
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.mode == 'run':
            require(args.manifest_sha256 is None, 'Run identity must come from the checked event')
            digest = select_run_manifest(root, os.environ)
        else:
            digest = args.manifest_sha256
        manifest = load_manifest(root, digest)
        if args.mode == 'run':
            committed = git(root, 'show', os.environ['GITHUB_SHA'] + ':transport/manifests/' + digest + '.json')
            validate_manifest(committed, digest)
        if args.mode == 'validate':
            print('VALID MANIFEST', digest, len(manifest['objects']), manifest['totalBytes'])
            return
        if args.mode == 'run':
            with tempfile.TemporaryDirectory(prefix='bounded-lfs-', dir=os.environ['RUNNER_TEMP']) as temp:
                result = upload_and_readback(root, manifest, Path(temp))
        else:
            result = {'objects': readback(manifest['objects']), 'independentReadbackOnly': True}
        receipt = {'manifestSha256': digest, 'repository': REPOSITORY, 'totalBytes': manifest['totalBytes'],
                   'commit': os.environ.get('GITHUB_SHA'), 'runId': os.environ.get('GITHUB_RUN_ID'), **result}
        print('TRANSPORT RECEIPT', json.dumps(receipt, sort_keys=True), flush=True)
    except Stop as error:
        raise SystemExit('STOP: ' + str(error)) from None
    except Exception:
        # Unexpected library errors must not echo signed URLs or request headers.
        raise SystemExit('STOP: unexpected transport error; no automatic retry') from None


if __name__ == '__main__':
    main()
