#!/usr/bin/env python3
"""One fixed Balanced backup -> existing LFS primitives; dispatch-only upload."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import urllib.parse
import urllib.request
import zipfile
import lfs_transport as lfs

ID = '1K2ZNcqtQYuq5-Cu2iBpFkhgekxUx02xC'
URL = f'https://drive.google.com/uc?export=download&id={ID}'
ZIP_SIZE = 894568
ZIP_SHA = '02e00b74c40b26ff8eab0a59cb94565489d84a43398485fff8f773cd88da1588'
MEMBER = 'FDI31-balanced/FDI31-balanced.glb'
OBJECT = {'file': 'FDI31-balanced.glb', 'bytes': 2052220,
          'sha256': '90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7'}

def allowed(url):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == 'https' and p.netloc in ('drive.google.com', 'drive.usercontent.google.com')
            and p.path in ('/uc', '/download') and not p.fragment
            and urllib.parse.parse_qs(p.query) == {'export': ['download'], 'id': [ID]})

class FixedRedirect(urllib.request.HTTPRedirectHandler):
    count = 0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        lfs.require(self.count <= 3 and allowed(newurl), 'Unexpected Drive redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def decode(raw):
    lfs.require(len(raw) == ZIP_SIZE and hashlib.sha256(raw).hexdigest() == ZIP_SHA,
                'Backup ZIP size/hash mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        matches = [i for i in z.infolist() if i.filename == MEMBER]
        lfs.require(len(matches) == 1 and matches[0].file_size == OBJECT['bytes'], 'ZIP member mismatch')
        # Never extract paths or read other archive members.
        with z.open(matches[0]) as source:
            data = source.read(OBJECT['bytes'] + 1)
    lfs.verify_bytes(data, OBJECT)
    return data

def download():
    opener = urllib.request.build_opener(FixedRedirect())  # No cookies/auth handler.
    with opener.open(URL, timeout=45) as response:
        lfs.require(response.status == 200 and response.headers.get_content_type() in
                    ('application/zip', 'application/octet-stream'), 'Drive HTML/confirmation/quota response refused')
        raw = response.read(ZIP_SIZE + 1)
    return decode(raw)

def guard(root, env):
    lfs.require(env.get('GITHUB_ACTIONS') == 'true' and env.get('GITHUB_REPOSITORY') == lfs.REPOSITORY,
                'Wrong execution repository')
    lfs.require(env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and env.get('GITHUB_REF') == 'refs/heads/main',
                'Only explicit main dispatch may upload')
    lfs.require(env.get('CONFIRM_OID') == OBJECT['sha256'], 'Exact OID confirmation required')
    sha = env.get('GITHUB_SHA', '')
    lfs.require(lfs.HEX40.fullmatch(sha) is not None and
                lfs.git(root, 'rev-parse', 'HEAD').decode().strip() == sha, 'Checkout/trigger mismatch')

def transfer(root, data, work):
    lfs.verify_bytes(data, OBJECT)
    objects = [OBJECT]
    missing = lfs.missing_objects(objects, lfs.batch(objects))
    origin = lfs.git(root, 'remote', 'get-url', '--push', 'origin').decode().strip()
    lfs.require(origin in (f'https://github.com/{lfs.REPOSITORY}', f'https://github.com/{lfs.REPOSITORY}.git'),
                'Unexpected destination')
    storage = work / 'lfs'
    # Existing checkout's ephemeral Actions auth only; command-scoped LFS storage/URL.
    # No lfs install, persistent config, commits, branch pushes or main mutation.
    if OBJECT['sha256'] in missing:
        pointer = lfs.git(root, 'lfs', 'clean', 'approved-balanced', data=data, storage=storage)
        expected = ('version https://git-lfs.github.com/spec/v1\noid sha256:' + OBJECT['sha256'] +
                    '\nsize ' + str(OBJECT['bytes']) + '\n').encode()
        lfs.require(pointer == expected, 'LFS pointer mismatch')
        lfs.git(root, 'lfs', 'push', '--object-id', 'origin', OBJECT['sha256'], storage=storage)
    return {'uploadedObjects': len(missing), 'existingObjectsSkipped': 1-len(missing),
            'objects': lfs.readback(objects)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('source-check', 'upload'))
    mode = p.parse_args().mode
    root = Path(__file__).resolve().parents[1]
    try:
        if mode == 'upload':
            guard(root, os.environ)
        data = download()
        print('SOURCE VERIFIED', OBJECT['sha256'], len(data), flush=True)
        if mode == 'upload':
            with tempfile.TemporaryDirectory(prefix='balanced-lfs-', dir=os.environ['RUNNER_TEMP']) as temp:
                print('TRANSPORT RECEIPT', json.dumps(transfer(root, data, Path(temp)), sort_keys=True))
    except lfs.Stop as error:
        raise SystemExit('STOP: ' + str(error)) from None
    except Exception:
        raise SystemExit('STOP: source/transport failure; no retry, credentials or confirmation workaround') from None

if __name__ == '__main__':
    main()
