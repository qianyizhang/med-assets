# Offline backup check and copy plan

`tools/backup_check.py` compares the **contents of one exact committed tree**
against an explicitly supplied local snapshot directory or ZIP, using SHA-256
and size. It streams actual backup bytes, including LFS media; matching pointer
files do not count as retained media. It prints JSON to stdout and never copies,
uploads, deletes, overwrites, downloads, extracts ZIPs, schedules work or changes
Git configuration. No Drive credentials, network service or Python packages are
needed. Requirements: Python 3.11+, [Git 2.45+](https://git-scm.com/docs/git/2.45.0)
(`--no-lazy-fetch`) and Linux
(`dir_fd` / `O_NOFOLLOW`). Git LFS itself is not needed.

Resolve the intended revision first, then pass its full commit ID explicitly:

```sh
commit=$(git rev-parse HEAD)
python3 tools/backup_check.py --commit "$commit" --inventory > /tmp/expected-tree.json
python3 tools/backup_check.py --commit "$commit" \
  --backup-tree /path/to/local-downloaded-snapshot > /tmp/backup-check.json
# Alternatively, a local ZIP whose member paths start at the repository root:
python3 tools/backup_check.py --commit "$commit" \
  --backup-zip /path/to/local-snapshot.zip > /tmp/backup-check.json
```

Use a stable, fully downloaded local snapshot. A mounted provider that fetches
files on demand can itself cause network reads; this tool cannot control that
provider. A ZIP with a wrapper directory must be prepared separately; the tool
never guesses roots, renames paths or accepts a metadata-only inventory as proof.
Keep reports outside the checkout: they may contain private operational paths
or names, and are not intended for Git commits. Shell redirection overwrites an
existing report; choose a fresh report path when preserving prior evidence.

`--inventory` exports every tracked regular file's exact expected path, SHA-256,
size and kind (`git` or `lfs`), with the resolved commit and unique-object totals.
Git files are hashed directly from committed blobs. LFS identity and size come
from committed pointers, checked against that commit's attributes. Dirty working
files and staged changes are excluded. Every Git command uses the explicit
`--no-lazy-fetch` option and denies all transport protocols with
`GIT_ALLOW_PROTOCOL=''`. Older Git versions that lack the option fail before
reading repository objects; the tool never retries without it. This avoids
relying on an environment variable that older Git may ignore. Missing Git objects
fail without lazy fetching. Local `info/attributes` overrides are refused because
they could change the interpretation of the committed tree. No backup has been
verified by exporting an inventory alone.

Check results contain one status per expected path:

| Status | Meaning |
| --- | --- |
| `verified` | Actual local bytes match both expected SHA-256 and size. |
| `missing` | The expected path is absent. |
| `mismatched` | Size or SHA-256 differs, including truncated/corrupt content. |
| `pointer_only` | An LFS pointer was retained instead of its media payload. |
| `unverifiable` | Cannot safely read the payload, e.g. symlink, nonregular file, permission failure, encrypted member or bad ZIP CRC. |

Every gap receives `action: "needs_copy"`; `plannedCopyBytes` sums expected bytes
at those paths, counting repeated paths separately. This is a **plan only**. It
does not establish that a good source copy is locally available or authorize
replacing the target. Preserve questionable existing files and obtain exact
verified source bytes before a separate transfer. Rerun the check on the resulting
downloaded snapshot to verify it. Extra backup files are ignored and never deleted.

Exit codes: **0** = all expected contents verified (or inventory exported),
**1** = backup has gaps, **2** = invalid input or inventory/check failure.
Only check mode can return `completeCurrentTree: true`; inspect that field as well
as the exit code. Unsafe or duplicate ZIP paths fail the entire check. ZIPs are
read in place, never extracted; member reads are bounded by expected sizes.

## Scope and older source archives

`completeCurrentTree` means byte coverage of this one committed tree at exact
repository paths. It does **not** establish full Git history, a Git clone, other
branches, untracked/private masters, external assets, executable permissions,
licensing/clinical review, Drive upload success, remote availability or restore
testing. Symlinks and submodules in the Git tree are unsupported and fail closed.

The historical `SHA256SUMS` and `metadata/asset-manifest.json` describe the initial
591-member import, not today's full tree. Preserve them unchanged. Original source
ZIPs use different member paths: this checker does not map those archives through
the import manifest or search their members by hash. Checking an old source ZIP
directly therefore reports exact-path gaps; it cannot decide whether differently
named members retain equivalent bytes. Such archives require a separate member
SHA-256/size audit and path mapping, or a future explicit snapshot with current
repository paths. A matching archive filename, timestamp, saved checksum or ZIP
CRC alone does not establish current-tree coverage.

Focused tests: `python3 -m unittest discover -s tests -p test_backup_check.py`.
The normal `python3 tools/verify.py offline` command discovers these tests too.
Screenshots are not applicable to this command-line, nonvisual change.
