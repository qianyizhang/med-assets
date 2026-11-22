# Asset storage and delivery

| Need | Owner |
| --- | --- |
| Canonical bytes and recovery | Git / Git LFS for maintained exports; pinned collection archives for the cold inputs listed below. Recover the full checkout with `git lfs pull`, then verify [payload integrity](../docs/WORKFLOW.md#verification). |
| Live gallery 3D exports | [Anatomy Gallery Site R2](#public-r2-downloads) for on-demand viewing and downloads. |
| Other important retained artifacts | [R2 Object Library](#artifact-backups) for recovery. |
| Entire committed tree | [Mirror planning and readback](../docs/BACKUP_CHECK.md). |

## Public R2 downloads

- **Gallery release** · Put an exact copy of every 3D export selected for an active gallery entry or published for viewing or download in the Anatomy Gallery Site's R2 bucket before the entry goes live. The gallery references the hash-addressed copy and Git / Git LFS retains the canonical export.
- **URL** · Public HTTPS through the existing Site Worker at `/assets/<sha256>/<name>`. The [asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json) lists downloadable aliases, hashes and sizes. The [Git-pinned fetcher](tools/fetch_asset.py) retrieves and verifies these objects.
- **Acceptance** · Verify size and SHA-256. The fetcher checks Git-pinned identity, serves valid cached/local bytes and refuses corrupt caches, redirects, changed encodings, symlinks and concurrent edits. Hydration requires a matching pointer and preserves permissions.
- **Recorded coverage** · 694 objects / 976,485,579 bytes verified on 2026-11-06 at `503c33f1dadf403faaec373c1a11a8b40dc523d6`: 689 LFS and five Git blobs ≥1 MB. Index then held 1,001 routes including previews and the frozen framework backup. Upload authorization closed. [Site recovery](../sites/anatomy-gallery/README.md).

```sh
curl --fail -o kidney_left.glb \
  'https://med-assets-model-survey.landy123007.chatgpt.site/assets/d2139a88cf85b70bdd7981e6134841faff99fcf18d7a480f04224d7e74c73c28/kidney_left.glb'

python3.12 transport/tools/fetch_asset.py models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb --hydrate
```

For the two archived trachea r06 SVG projections, use `fetch_asset.py` with
`--commit 503c33f1dadf403faaec373c1a11a8b40dc523d6` and either original repository
path under `reviews/trachea/2026-10-29-open-airway-r06/`. The delivery manifest
still pins that revision and the original digest routes. Restore the exact paths
from [their local Brotli copies](../reviews/trachea/2026-10-29-open-airway-r06/README.md#restore-the-exact-svgs-offline)
before local checks against the historical migration manifest.

## Artifact backups

Back up other important retained artifacts with the [R2 Object Library](https://r2-object-library.landy123007.chatgpt.site/). Examples include unique build and recovery bundles, release archives and evidence that would be costly to recreate. Use this public service only for artifacts cleared for public access. Use approved private storage for restricted material.

Record the source revision, object key, byte size, SHA-256 and restore steps with the owning package. Verify a fresh download before counting the backup as recoverable. For multi-file archives, record and check member hashes on restore. [Teaching media backup example](../sites/body-systems-survey/README.md#restore-the-media)

### Restore an archived collection

The [archive index](collection-archives.json) pins each ZIP by immutable Object Library key, size and SHA-256. Each ZIP includes a member manifest, original repository paths and attribution. The original Gallery downloads keep their exact addresses. The teaching-media archive has its [own restore guide](../sites/body-systems-survey/README.md#restore-the-media).

| Collection | Contents | When to restore |
| --- | --- | --- |
| `hra-replay-sources` | Ten HRA source GLBs and their credit records | Before running the derivative packages' source replay or source-byte audit |
| `bronchial-trial-plates` | Eight r13/r14 comparison plates, attribution and measurement records | To inspect the full simplification trial; the first-fork plate remains in Git |

From the repository root, run `python3.12 transport/tools/restore_collection.py hra-replay-sources` or substitute the other collection name. For an offline restore, pass `--from-zip PATH`. Use `--output DIRECTORY` to restore into an empty tree. The command verifies the ZIP and member digests, installs missing payloads at their original paths, and refuses conflicting bytes.

The Workshop and Cardiac Atlas base-color and normal PNGs restore directly from their retained GLBs. Run `python3.12 tools/restore_textures.py workshop` or `python3.12 tools/restore_textures.py cardiac` from a hydrated checkout. These exact bytes are verified against the [original import checksums](../sources/imports/SHA256SUMS).

## Add or reverify R2 copies

### Upload acceptance

- **Routine local uploads** · On the user's Mac, record successful upload of the intended asset as verified. Use a separate download for an explicit remote byte or restore check, or when a guarded workflow requires one.
- **Consumer changes** · Exercise the affected consumer when the change is to a live route, download action or recovery flow.

| Goal | Acceptance |
| --- | --- |
| Reviewed candidate | [Planner](tools/r2_migration.py) pins a commit and verifies local bytes for all LFS and Git blobs ≥1 MB. Review paths, rights and disclosure scope. |
| Valid public delivery | [Delivery manifest](../sites/anatomy-gallery/app/src/content/assets/delivery-index.json) owns declared routes. Handler enforces hash, size, MIME/extension, attachment safety and object bounds. |
| Bounded upload | [Uploader](tools/r2_upload.mjs) uses short-lived hidden-stdin or in-memory authorization, verifies identities, keeps state ignored and includes anonymous byte readback in the run. |
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
| Guarded execution | [Main-only workflow](../.github/workflows/bounded-lfs-transport.yml) and [executor](tools/lfs_transport.py) own event, repository, ref, origin, format, size, count and schema bounds. Fetch and verify all sources before upload. Manual dispatch uses a reviewed manifest SHA on main. |
| Byte proof | Job fetches all uploaded or existing OIDs from GitHub. Independently repeat readback from another executor. |
| Separate pointer delivery | Current CI, branch rules and exact head. Guarded merge with `expected_head_sha` and applicable authorization for readiness and merge. |
| Narrow exception | [Balanced-only Drive fallback](https://github.com/qianyizhang/med-assets/pull/142). Its approval is specific to that payload. |

```sh
python3.12 transport/tools/lfs_transport.py validate --manifest-sha256 "$manifest_sha256"
python3.12 transport/tools/lfs_transport.py readback --manifest-sha256 "$manifest_sha256"
```

- **Security** · Source and upload limits live in the executor. Extend allowlists or formats through code review. Preserve read-only ordinary PR CI and keep credentials, signed URLs and raw credential-bearing errors out of reports.
- **Review limits** · Transport proves byte identity. Asset quality, clinical/anatomical status, runtime, licensing and de-identification need independent evidence. [Historical executor recovery](../sources/recovery/completed-pilots/README.md).
