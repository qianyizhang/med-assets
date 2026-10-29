#!/usr/bin/env python3
"""Manually gated, exact FDI31 LFS-pointer draft PR. Never uploads or merges."""
import json
import os
from pathlib import Path
import sys
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from lfs_transport import Stop, require, validate_manifest, readback

DIGEST = 'ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118'
REPO = 'qianyizhang/med-assets'
BRANCH = 'delivery/fdi31-' + DIGEST[:12]
PREFIX = 'reviews/swirendo_fdi31/2026-10-27-interface-locked/media/'
NOTICE = '''# Retained FDI31 review media

Unapproved research candidate; no clinical, canonical or runtime approval.
These delivered media supersede the parent review's historical no-payload status.

Source: Benz, Leander; Heck, Katrin; Walter, Elias (2024), Data: Visualization
of Pulpal Structures by SWIR in Endodontic Access Preparation.
https://data.ub.uni-muenchen.de/477/ — CC BY-SA 4.0:
https://creativecommons.org/licenses/by-sa/4.0/

Derivative: protected interfaces, exterior-only simplification; source frame
and mm-to-m scale retained. Exact 5 identities: ci/fdi31-source/manifest.json.
LFS bytes were freshly verified before this pointer commit; future availability
and separate visual/anatomical/runtime acceptance are not guaranteed by hashes.
'''


def api(method, path, data=None):
    require(path.startswith('/repos/' + REPO + '/'), 'Unexpected API target')
    request = urllib.request.Request('https://api.github.com' + path,
        data=None if data is None else json.dumps(data).encode(), method=method,
        headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
    # API destinations are fixed; never forward token through a redirect.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise Stop('API redirect refused')
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            raw = response.read(2_000_001)
            require(len(raw) <= 2_000_000, 'API response too large')
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code == 404 and method == 'GET':
            return None
        raise Stop('GitHub API refused operation: HTTP ' + str(error.code)) from None


def prepare(manifest, base, request=api, verify=readback):
    """Fixed manifest validated by caller; refuse changed targets and branch collisions."""
    require(len(manifest['objects']) == 5 and manifest['totalBytes'] == 27593900, 'Unexpected batch')
    paths = [o['file'] for o in manifest['objects']]
    require(all(p.startswith(PREFIX) and '/' not in p[len(PREFIX):] for p in paths), 'Unexpected target')
    endpoint = '/repos/' + REPO
    current = request('GET', endpoint + '/git/ref/heads/main')
    require(current['object']['sha'] == base, 'Main moved; review new head before retry')
    commit = request('GET', endpoint + '/git/commits/' + base)
    tree = request('GET', endpoint + '/git/trees/' + commit['tree']['sha'] + '?recursive=1')
    require(not tree.get('truncated'), 'Truncated base tree')
    targets = set(paths + [PREFIX + 'README.md'])
    require(not targets.intersection(row['path'] for row in tree['tree']), 'Targets already exist; do not overwrite')
    entries = [{'path': o['file'], 'mode': '100644', 'type': 'blob',
                'content': f"version https://git-lfs.github.com/spec/v1\noid sha256:{o['sha256']}\nsize {o['bytes']}\n"}
               for o in manifest['objects']]
    entries.append({'path': PREFIX + 'README.md', 'mode': '100644', 'type': 'blob', 'content': NOTICE})
    branch = request('GET', endpoint + '/git/ref/heads/' + BRANCH)
    if branch:
        # Never update somebody's branch, even one with our expected name.
        prs = request('GET', endpoint + '/pulls?state=all&head=qianyizhang:' + BRANCH + '&base=main')
        require(len(prs) == 1, 'Branch exists without exactly one PR; inspect manually')
        return {'existingPr': prs[0]['html_url'], 'unchanged': True}
    # Fresh authenticated-independent public LFS readback, not a caller-provided receipt.
    rows = verify(manifest['objects'])
    expected = {(o['sha256'], o['bytes'], o['file']) for o in manifest['objects']}
    require(len(rows) == 5 and all(row.get('verified') is True for row in rows) and
            {(row.get('oid'), row.get('bytes'), row.get('file')) for row in rows} == expected, 'Incomplete readback')
    created = request('POST', endpoint + '/git/trees', {'base_tree': commit['tree']['sha'], 'tree': entries})
    head = request('POST', endpoint + '/git/commits', {'message': 'Deliver retained FDI31 review media pointers',
                   'tree': created['sha'], 'parents': [base]})
    request('POST', endpoint + '/git/refs', {'ref': 'refs/heads/' + BRANCH, 'sha': head['sha']})
    pr = request('POST', endpoint + '/pulls', {'title': 'WIP: deliver retained FDI31 review media',
        'head': BRANCH, 'base': 'main', 'draft': True,
        'body': 'Refs #96. Exact reviewed 5 LFS pointers + CC BY-SA 4.0 notice. Fresh readback passed before pointer commit. No clinical/canonical/runtime promotion. Required CI and independent checkout hydration remain to review. No auto-merge. Manifest: `' + DIGEST + '`.'})
    return {'pr': pr['html_url'], 'head': head['sha'], 'readbackObjects': len(rows)}


def main():
    env = os.environ
    require(env.get('GITHUB_REPOSITORY') == REPO and env.get('GITHUB_REF') == 'refs/heads/main', 'Main repository only')
    require(env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and env.get('CREATE_FDI31_PR') == 'true', 'Manual opt-in required')
    require(env.get('ZERO_COST_CONFIRMED') == 'true' and env.get('MANIFEST_SHA256') == DIGEST, 'Exact batch and cost confirmation required')
    manifest = validate_manifest((ROOT / 'transport/manifests' / (DIGEST + '.json')).read_bytes(), DIGEST)
    # Hash pins paths, OIDs, sizes and the reviewed CC BY-SA scope; this is not a license detector.
    print(json.dumps(prepare(manifest, env['GITHUB_SHA']), sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Stop as error:
        raise SystemExit('STOP: ' + str(error)) from None
    except Exception:
        raise SystemExit('STOP: unexpected failure; inspect run, do not retry blindly') from None
