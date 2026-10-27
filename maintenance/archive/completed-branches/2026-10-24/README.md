# Completed transport/test branch archive — 2026-10-24

23 completed pilot/test branches are preserved here without keeping 23 live branch names.

- `manifest.json`: original branch names, full commit SHAs, file hashes and run links.
  Its `archive_path` fields describe the former extracted copies, not current files.
- `completed-pilots.bundle.base64.txt`: 55,091-byte Git bundle encoded as text; preserves original unique commits and refs. Requires retained `main` history.
- The bundle is the single archived copy of the 24 pilot workflow/script files.
  Redundant branch-named folders and two retired cleanup-workflow copies were
  removed after exact restoration checks. No archived workflow is active.
- `jobs-evidence.json`: successful terminal job/step results from GitHub, not a claim that test success proves anatomical quality.

Bundle SHA-256: `0cbd5cf4b34c6a38b9e6ec098778ddc67b60282cd531d994d2fe4ddb1598cb27`.

## Restore

From a clone of this repository:

```sh
git fetch origin main
python3 - <<'PY'
import base64, hashlib, pathlib
root = pathlib.Path('maintenance/archive/completed-branches/2026-10-24')
data = base64.b64decode((root / 'completed-pilots.bundle.base64.txt').read_text())
assert hashlib.sha256(data).hexdigest() == '0cbd5cf4b34c6a38b9e6ec098778ddc67b60282cd531d994d2fe4ddb1598cb27'
pathlib.Path('/tmp/completed-pilots.bundle').write_bytes(data)
PY
git bundle verify /tmp/completed-pilots.bundle
git bundle list-heads /tmp/completed-pilots.bundle
# Substitute an exact branch from manifest.json:
git fetch /tmp/completed-pilots.bundle 'refs/heads/<branch>:refs/heads/<branch>'
```

Check the restored head against the manifest before publishing it. No LFS payloads are needed to restore these transport recipes. Existing model LFS objects are unchanged.

To inspect one file without checking out an archived branch, use
`git show '<restored-head-sha>:<original_path>'` with values from the manifest.
The two retired cleanup workflows are already in retained `main` history:

```sh
git show 8531699c2491b7949d30301bd3bad2498d5a2cd0:.github/workflows/merged-branch-cleanup-20261024.yml
git show 71a77433a5fa731506df880d897eb8d818f6ede0:.github/workflows/consolidate-completed-branches-20261024.yml
```

## Verification and limits

Independent bare-repository restoration from main plus this bundle reproduced all 23 heads and all 24 source files exactly. Latest successful jobs were terminal before archival. Historical failures remain linked in the manifest; success does not erase them. Source URLs inside old recipes may expire; the archive preserves what ran, not a promise that old transport URLs stay live.

Merged asset/review branch commits remain directly reachable from main and their PR head refs. This archive does not change models, purge LFS objects, rewrite history, alter repository permissions or clean local worktrees.

Retention: the bundle holds unique deleted-branch history needed for recovery;
keep it with its manifest and execution evidence. Review that recovery need by
2026-11-26. Regenerate extracted copies only in a temporary directory.
