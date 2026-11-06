# Asset storage and delivery

R2 provides public, on-demand reads. Git/LFS remains the canonical source and
recovery path. Neither transport changes asset licenses, coordinates, review
status or historical identities.

## Public R2 downloads

[Asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json)
contains each object's `sha256`, `bytes` and download `name`. Public HTTPS reads
need no Codex/ChatGPT login or token. URLs use the Site's Worker/domain:
`https://med-assets-model-survey.landy123007.chatgpt.site/assets/<sha256>/<name>`.
`/assets/` itself is not a directory listing.

```sh
curl --fail -o kidney_left.glb \
  'https://med-assets-model-survey.landy123007.chatgpt.site/assets/d2139a88cf85b70bdd7981e6134841faff99fcf18d7a480f04224d7e74c73c28/kidney_left.glb'

# Verified ignored cache; --commit defaults to HEAD:
python3.12 tools/fetch_asset.py models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb

# Restore only an unchanged matching pointer at its original path:
python3.12 tools/fetch_asset.py models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb --hydrate
```

For manual downloads, compare the file size and SHA-256 with the index.
The fetcher does this automatically: it binds bytes to the selected Git revision,
resolves published aliases,
and checks size/SHA-256. It refuses redirects, encoding changes, corrupt caches,
symlinks and concurrent edits. Hydration preserves permissions; correct local
bytes avoid network work. Unpublished objects fail explicitly. Large ordinary
Git data blobs are identified by their committed content rather than LFS pointers.

On 2026-11-06, all 689 LFS payloads plus five Git data/evidence blobs >=1 MB were
copied and fully read back: **694 objects / 976,485,579 bytes**, source revision
`503c33f1dadf403faaec373c1a11a8b40dc523d6`. The index has 1,001 routes including
retained previews and the frozen framework backup. Upload authorization was
closed after verification. Original Git/LFS copies remain; history and existing
storage have not been pruned. [Site build/recovery](../sites/model-survey/README.md)
and its structured references own deployment and backup details.

## Add or reverify R2 copies

- `tools/r2_migration.py` plans every LFS payload plus Git blobs >=1 MB at a fixed
  commit. It verifies local bytes and produces a fresh candidate without network
  or Git writes. Review selected paths, rights and disclosure scope first.
- The Site's [delivery manifest](../sites/model-survey/app/src/content/assets/r2-trial.json)
  is the delivery-reference owner; the historical name
  remains part of the pinned framework import. Declarations alone do not prove
  remote availability. The handler admits only named hash/size/type routes,
  checks MIME/extension pairs and caps one object at 64 MB. Source, volume,
  SVG/JSON and ZIP bytes are attachments with no sniffing; HTML/JS are excluded.
- `tools/r2_upload.mjs` takes short-lived authorization through hidden stdin or an
  in-memory caller. It rechecks Git/local identities, streams <=32 objects / 64 MB
  per batch with <=4 active requests, and verifies complete fresh anonymous reads.
  Resume state stays ignored; linked or existing temporary-state paths are refused.
- Any HTTP, quota, permission or integrity failure stops after the current group.
  No automatic retry, provider fallback or spending-limit adjustment occurs.
  Explicit resume repeats readback and avoids reuploading previously verified
  objects. Close the asset-upload environment and redeploy the same saved version
  when done; preserve the owner environment and audience.

The selected maximum is 42,497,262 bytes. See [Workers request limits](https://developers.cloudflare.com/workers/platform/limits/)
and [R2 upload methods](https://developers.cloudflare.com/r2/objects/upload-objects/).
Retiring a provider or old copy requires complete coverage and consumer checks.

## Git LFS delivery and recovery

For authorized canonical uploads, try the exact bounded direct operation first,
for example `git lfs push --object-id origin <reviewed-oid>`. Verify the current
executor, remote and existing authentication; connector access does not establish
shell access. Record sanitized results and distinguish authentication, network,
quota, integrity and action-denial failures.

Verify size/SHA-256 through a fresh GitHub download or empty LFS store before
merging matching asset pointers. Keep authorized verified backups. A Drive/Site
fallback is allowed only for an unresolved technical failure of direct transport
and the same reviewed bytes/rights. Never route around a permission, quota,
integrity or action denial using another tool, credential or provider.

## Guarded CI fallback

[`bounded-lfs-transport.yml`](../.github/workflows/bounded-lfs-transport.yml) and
[`tools/lfs_transport.py`](../tools/lfs_transport.py) own the executable gates:

1. Review the exact asset/source/privacy/licensing scope. Save unchanged manifest
   bytes as `transport/manifests/<sha256-of-file>.json`.
2. Merge a manifest-only PR adding exactly one file. Mixed edits, deletions or
   multiple files do not authorize execution. Keep executor changes separate.
3. The main-only job validates event/repository/ref, source bytes and fixed bounds;
   downloads every source before upload; uploads missing OIDs; then freshly reads
   every object from GitHub. Independently repeat readback from another executor.
4. Merge matching pointers/evidence only after those checks. Review current CI,
   branch rules and exact PR head; use guarded `expected_head_sha` merges. Mark a
   draft ready only within applicable user authorization. Merge success alone
   does not prove transfer or asset approval.

CI manifests use `objects`, `totalBytes` and optional `objectCount`/`scope`.
Each object binds `file`, `sha256`, `bytes` and `url`; `file` is metadata, never
an output path. Gzip also binds encoded hash/size. Hash-named manifests are
immutable: corrections need a newly reviewed file. Duplicate/unknown fields fail.

This CI flow permits GLB/PNG/WebP from code-pinned Site `/review/` origins only.
Limits are 32 OIDs, 40,000,000 bytes per object and batch (raw and encoded), and
128 KiB per manifest. Source/format additions require code review. These limits
are separate from direct R2 delivery and are not standing upload authorization.

```sh
python3.12 tools/lfs_transport.py validate --manifest-sha256 <sha256>
python3.12 tools/lfs_transport.py readback --manifest-sha256 <sha256>
python3.12 -m unittest discover -s tests -p test_lfs_transport.py
```

Manual dispatch accepts only a reviewed manifest SHA on main. The executor uses
one serialized, 10-minute job with pinned checkout and the existing ephemeral
GitHub token. It never commits, pushes refs, merges PRs, changes settings or executes
downloaded content. Ordinary PRs stay read-only and never trigger uploads. Existing
[Balanced-only Drive fallback](https://github.com/qianyizhang/med-assets/pull/142)
is separately scoped; it does not provide general Drive support.

Keep tokens, signed URLs and raw credential-bearing errors out of logs/source.
Existing budgets/quotas govern all flows; checks do not establish billing headroom
or authorize new spend. Byte identity does not establish geometry, visual,
clinical/anatomical, licensing, de-identification or runtime approval.
Historical executor recovery remains in [completed pilots](../sources/recovery/completed-pilots/README.md).
