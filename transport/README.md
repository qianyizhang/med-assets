# Asset storage and delivery

| Need | Owner |
| --- | --- |
| Canonical bytes and recovery | Git / Git LFS. Recover the full checkout with `git lfs pull`, then verify [payload integrity](../docs/WORKFLOW.md#verification). |
| On-demand public bytes | [R2 asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json) and [Git-pinned fetcher](../tools/fetch_asset.py). |
| Entire committed tree | [Mirror planning and readback](../docs/BACKUP_CHECK.md). |

## Public R2 downloads

- **URL** · Public HTTPS through the survey Worker at `/assets/<sha256>/<name>`. The index lists downloadable aliases, hashes and sizes.
- **Acceptance** · Verify size and SHA-256. The fetcher checks Git-pinned identity, serves valid cached/local bytes and refuses corrupt caches, redirects, changed encodings, symlinks and concurrent edits. Hydration requires a matching pointer and preserves permissions.
- **Recorded coverage** · 694 objects / 976,485,579 bytes verified on 2026-11-06 at `503c33f1dadf403faaec373c1a11a8b40dc523d6`: 689 LFS and five Git blobs ≥1 MB. Index then held 1,001 routes including previews and the frozen framework backup. Upload authorization closed. [Site recovery](../sites/model-survey/README.md).

```sh
curl --fail -o kidney_left.glb \
  'https://med-assets-model-survey.landy123007.chatgpt.site/assets/d2139a88cf85b70bdd7981e6134841faff99fcf18d7a480f04224d7e74c73c28/kidney_left.glb'

python3.12 tools/fetch_asset.py models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb --hydrate
```

## Add or reverify R2 copies

### Upload acceptance

- **Routine local uploads** · On the user's Mac, record successful upload of the intended asset as verified. Use a separate download for an explicit remote byte or restore check, or when a guarded workflow requires one.
- **Consumer changes** · Exercise the affected consumer when the change is to a live route, download action or recovery flow.

| Goal | Acceptance |
| --- | --- |
| Reviewed candidate | [Planner](../tools/r2_migration.py) pins a commit and verifies local bytes for all LFS and Git blobs ≥1 MB. Review paths, rights and disclosure scope. |
| Valid public delivery | [Delivery manifest](../sites/model-survey/app/src/content/assets/r2-trial.json) owns declared routes. Handler enforces hash, size, MIME/extension, attachment safety and object bounds. |
| Bounded upload | [Uploader](../tools/r2_upload.mjs) uses short-lived hidden-stdin or in-memory authorization, verifies identities, keeps state ignored and includes anonymous byte readback in the run. |
| Failure and resume | HTTP, quota, permission or integrity failure stops after the active group. Explicit resume rechecks readback and preserves verified uploads. Budgets, providers and permissions require their own authority. |
| Closeout | Close asset-upload authorization and redeploy the same saved version with owner environment and audience intact. Confirm coverage and consumers before retiring any old copy. |

- **Provider limits** · [Workers request limits](https://developers.cloudflare.com/workers/platform/limits/) · [R2 upload methods](https://developers.cloudflare.com/r2/objects/upload-objects/).

## Git LFS delivery and recovery

- **Direct path** · Authorized exact OID, reviewed remote and executor authentication. Use `git lfs push --object-id origin <reviewed-oid>`. Keep sanitized auth/network/quota/integrity/permission results.
- **Completion** · Apply [upload acceptance](#upload-acceptance) to routine local uploads. For remote pointer delivery, verify size and SHA-256 from a fresh GitHub or empty-store download before merge. Retain authorized verified backups.
- **Fallback** · Only for unresolved technical failure with the same reviewed bytes and rights. Permission, quota, integrity and action denials require resolution at the owning boundary.

## Guarded CI fallback

| Outcome | Required evidence |
| --- | --- |
| Reviewed scope | Exact asset, source, privacy and licensing scope. One manifest-only PR adding `transport/manifests/<sha256-of-file>.json`. Corrected manifests use new hashes. |
| Guarded execution | [Main-only workflow](../.github/workflows/bounded-lfs-transport.yml) and [executor](../tools/lfs_transport.py) own event, repository, ref, origin, format, size, count and schema bounds. Fetch and verify all sources before upload. Manual dispatch uses a reviewed manifest SHA on main. |
| Byte proof | Job fetches all uploaded or existing OIDs from GitHub. Independently repeat readback from another executor. |
| Separate pointer delivery | Current CI, branch rules and exact head. Guarded merge with `expected_head_sha` and applicable authorization for readiness and merge. |
| Narrow exception | [Balanced-only Drive fallback](https://github.com/qianyizhang/med-assets/pull/142). Its approval is specific to that payload. |

```sh
python3.12 tools/lfs_transport.py validate --manifest-sha256 "$manifest_sha256"
python3.12 tools/lfs_transport.py readback --manifest-sha256 "$manifest_sha256"
```

- **Security** · Source and upload limits live in the executor. Extend allowlists or formats through code review. Preserve read-only ordinary PR CI and keep credentials, signed URLs and raw credential-bearing errors out of reports.
- **Review limits** · Transport proves byte identity. Asset quality, clinical/anatomical status, runtime, licensing and de-identification need independent evidence. [Historical executor recovery](../sources/recovery/completed-pilots/README.md).
