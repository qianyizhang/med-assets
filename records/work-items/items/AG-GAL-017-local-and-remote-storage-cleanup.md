---
description: Retire reproducible local build output and identify recoverable storage savings across Git LFS, Gallery delivery and remote backups.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-017
work_status: done
work_kind: build
added: 2026-11-21
tags: repository, transport
depends_on: AG-GAL-012, AG-GAL-016
residual_of: none
residual_items: none
---

# AG-GAL-017 — Clean up local builds and reconcile remote storage

Start after the remaining teaching stills have a verified local Gallery destination in [AG-GAL-016](AG-GAL-016-integrate-retained-teaching.md). Its deferred interactive journeys have their own [dispositions](AG-GAL-013-reconcile-gallery-coverage.md#deferred-specialist-journeys).

## Acceptance Criteria

- [x] Check preview readers, commands, symlinks, and unique restore inputs. Retire superseded rebuildable local outputs after confirming the retained walkthrough and its recovery work. Record actual disk space recovered.
- [x] Reconcile local LFS prune candidates with retained revisions and available remote objects. Keep the working checkout, unpublished work and independent recovery intact. Report local cache savings separately from hosted LFS storage.
- [x] Compare read-only inventories for hosted LFS, Gallery R2 delivery and the Object Library backups with current consumers, public aliases, retained revisions and archive members. Record inventory coverage and access gaps. Approve any subsequent retirement only after identifying its exact object or version, size, consumers and tested independent restore.
- [x] Verify the Gallery, on-demand fetch and any affected archive restore after cleanup. Record which copies still serve different delivery or recovery needs. The [Airway retention decision](AG-GAL-014-compact-delivery-and-recovery.md#decision--retain-the-public-airway-downloads) keeps the consumed original downloads after public cutover.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-21 | Maintainer and Codex | — | ready | Prioritize hygiene after static placement. Interactive rework is deferred. |
| 2026-11-21 | Codex | ready | done | Verified local retirement, exact recovery and the bounded remote inventory. No remote retirement qualifies in this batch. |

## Starting measurements

At `6f3cf47`, the local LFS dry run selected 393 cached objects (198 MB). The Gallery delivery index declared 1,243 distinct SHA-256 values across 1,243 entries. That index describes downloads. Remote object versions, unlisted keys, backup copies and billed usage require provider evidence.

The largest local leads were the 612 MiB transport verification directory under `.artifacts/` and several 113–115 MiB assembled Gallery builds under the Site's `.local/`. These are directory sizes. Measure recovered space after accounting for shared files and retained inputs. [Repository retention](../../../docs/WORKFLOW.md#retention) · [Delivery and recovery](../../../transport/README.md)

At baseline, `gallery-guides` and `gallery-systems` had identical rendered HTML, as did `gallery-be9be24` and `gallery-work`. The retirement table records which builds survived. The `publication` directory also contains framework recovery inputs, so matching its HTML to another build is insufficient grounds for removal. Keep one documented current preview command and link historical verification to its source revision and retained evidence.

## Local retirement

| Retired | Recovery and retained readers |
| --- | --- |
| Gallery `.local/gallery-guides` and `.local/gallery-be9be24` | Retained the byte-identical HTML in `gallery-systems` and `gallery-work`. The only candidate-exclusive test file matched the Git blob from `be9be24`. Relative dependency symlinks resolved to the retained `.local/app/node_modules`. |
| Gallery `.local/static-placement` | Stopped its interim preview after the final `.local/teaching-stills` build passed. Preserved the original walkthrough and the running migration and Compare previews. |
| Transport scratch `fetch.GCgZTF` and `final-checkout.zJGvL6` | Recovered both exact Git trees in a disposable clone from `a334773` and the retained bundle for candidate `6ce2139`. The modified cutaway in the fetch clone was the hydrated 1,564,740-byte Git-pinned object. The candidate bundle and original test logs are retained. |
| Transport scratch `teaching.XRxTXH` and `framework.370KAQ/gallery` | The two teaching extracts contained only the 327 approved members and the deliberate 23-byte local-edit fixture. The independent teaching ZIP restored all member identities. The pinned framework bundle restored the approved framework, and the new local walkthrough rebuilt from it. The remaining framework scratch records, seed and frozen recovery files are retained. |

The seven directories contained 749,068,288 bytes of regular-file blocks after excluding hardlinks with surviving occurrences. The volume reported 765,235,200 bytes more available after directory retirement. Removing the verified LFS files released 29,151,232 bytes of allocated file blocks and the volume gained a further 28,966,912 bytes. The total observed gain during the deletions was **794,202,112 bytes (757.4 MiB)**. This measures the deletion window and includes the superseded build made during this batch. File-block accounting and concurrent volume activity can affect the difference. The final walkthrough build, captures and compact recovery receipts occupy separate local space.

The 393 dry-run LFS candidates totalled 197,813,568 logical bytes. Comparing 84 retained tree revisions, including 57 local-only revisions, held every candidate still used there. The 175 eligible objects totalled 28,783,473 logical bytes. Each had an owning pointer in published history and passed full-byte GitHub readback into an empty LFS store before its cache copy was removed. They shared no identities with the current Gallery index or teaching ZIP. The remaining 218 candidates total 169,030,095 bytes. GitHub reported them unavailable, including 160 present in protected trees. Keep all 218. The post-cleanup dry run retained 1,000 other objects.

The receipt and exact identities are under `.artifacts/gallery-storage-cleanup/`. The local deletion receipt is SHA-256 `3e45740061f168c620660454fa21a58db16a914250f30acb58f1a253fe37ab40`. The 175 verified identities are in `lfs-verified.json`, SHA-256 `eddf0c3ae23a88caf710b6576181d4cfaf6adacc0d0db25db3de4abfd92e9454`. The retained candidate bundle is SHA-256 `65072efff8bc97f94db6975a808337eb80c2dcdba4da2b68202d39e9203692d4` and requires `b461f8f`.

## Remote inventory and recommendation

| Surface | Observed inventory and conditions for retirement |
| --- | --- |
| Hosted Git LFS | GitHub advertised downloads for all 939 distinct pointers in published `main` history at `9d70d2646ec2642f0312ab7ca6d17dc9e7dbd4ef`, declaring 993,939,610 bytes. Only the 175 retired local copies received full-byte readback in this batch. The Batch endpoint only answers known OIDs. It exposes neither retained unreferenced server objects nor billed storage. Historical checkouts still read these pointers. |
| Gallery R2 | The live index declared 1,001 aliases with distinct hashes totalling 995,630,117 bytes. The local index contains those aliases and 242 more, for 1,243 declarations and 1,025,125,643 bytes. The Worker maps a declared alias to `assets/sha256/<digest>`. Cloudflare's bucket-list API returned HTTP 403 and error 10042 for the connected account. Unlisted keys, provider versions, storage usage and billed savings remain unavailable. The 689 objects shared with published LFS still have public Gallery routes. The two legacy Airway files remain under [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md). |
| Object Library | The public `med-assets/teaching/` catalogue lists one 127,459,034-byte object, `library/med-assets/teaching/afa6ed28-1fa4-40d5-af01-643460a53471--med-assets-teaching-c803735.zip`. The ZIP holds 327 distinct member hashes and 141,588,243 uncompressed bytes. It is a single physical object anchoring teaching recovery and six Image 2.6 film routes in the local preview. The neighbouring `med-assets-sample/` has four public objects totalling 483,890 bytes, including its source and license record. The scoped listing exposes current public keys without provider billing or object history. |

Keep the teaching ZIP, the known Gallery delivery objects, published LFS and the public samples. Archive members are recovery inputs. A common digest in GitHub LFS and Gallery R2 still serves independent checkout and visitor paths. A later remote proposal needs the provider's full physical inventory, exact object or version, an accounted reader path and an independently verified restore. No billed savings were established. No remote change or Git history rewrite is included.

## Verification after cleanup

The [placement](AG-GAL-016-integrate-retained-teaching.md#specialist-stills) at `6abbadd` passed the pinned build, 12 Site tests, preview recovery regression, 19 Compare entries and the full ordinary Chrome journey. On ports 8893 and 8895, the earlier and new walkthroughs still served their exact HTML after retirement. The new preview returned the original heart plate at its exact SHA-256. The on-demand fetcher recovered the 2,527,704-byte Git-pinned kidney GLB into an empty cache. A live Object Library download matched the complete ZIP and all 327 member digests. FFmpeg decoded the freshly restored gum-disease film. The UFF viewer route returned HTTP 200.

An isolated hydrated checkout of `6abbadd` passed the combined repository gate after cleanup. The initial shared-checkout check encountered a concurrent edit to the pinned `body/breathing/README.md`. The file subsequently matched its recorded import identity again. The final Gallery follow-up at `3bbb5f4` passed the complete browser and Site suites and the combined repository gate, with 440 offline tests, 998 indexed LFS files, 25 foundation records and 11 package checks.


## Gallery display replay

The follow-up from `276f825` retires 70 display WebPs totaling **17,572,300 current-tree LFS bytes** and adds no LFS objects. The [display derivative declarations](../../../sources/display-derivatives.json) retains the canonical PNGs and the existing download bindings. A clean assembly reproduced the encoded size, SHA-256 and decoded RGBA of all 70 WebPs, plus the eight previously retired contact-review displays.

The [r14 first-fork comparison](../../../reviews/bronchial_tree/2026-11-21-distal-simplification-trial/evidence/close.webp) remains loose for its Gallery reader. Its eight supplementary sheets are retained in the [verified bronchial archive](../../../transport/README.md#restore-an-archived-collection). The trachea r06 and spinal roots r04 comparison plates lack matching canonical PNGs. The legacy dental tool and prepared-incisor originals come from the separate [recovery cache](../../../sites/anatomy-gallery/README.md#legacy-dental-review-media). Their tracked displays keep that dependency optional. Historical snapshot thumbnails and the independently maintained Body Systems and adrenal displays retain their existing bindings.

This was a reduction in current Git LFS references. Generated local files and historical objects still occupied storage. Public cutover was deferred at this checkpoint and later passed the [November 22 release readback](AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback). This cleanup authorized no remote retirement or Git history changes.

## 2026-11-22 collection cleanup

Retired the `node_modules` directories in `sites/anatomy-gallery/.local/static-verification`, `static-body` and `static-reviews`. Their sources, package locks and unique historical HTML remain. Checked tracked and ignored readers, active processes, and inbound and relative symlinks. The three dependency trees matched the retained `static-reviews-final/node_modules` across 10,793 paths each, with one empty generated Vite directory omitted per tree. A disposable copy of that retained dependency tree rebuilt all three pages. The HTML matched except for the local Codex thread marker. An offline install encountered a cache miss, so the verified recovery for these copies is the retained dependency tree and identical lockfiles.

The removed directories contained 327,327,744 bytes of allocated regular-file blocks after accounting for surviving hardlinks. The volume reported **0 additional available bytes** at the measurement resolution during and after removal. The 936 tracked LFS identities matched before and after, with a **0-byte current-tree change**. The local LFS prune dry run still selected the 218 previously held objects. Keep them and the independent recovery inputs.

After cleanup, the two retained walkthroughs and the protected release candidate served their exact HTML. Both preview regressions passed. The pinned on-demand fetch filled an empty disposable cache with the kidney GLB, and the existing teaching ZIP and its gum-disease film matched their recorded digests. The earlier full recovery and decoded film checks remain applicable. Local cleanup measurements and check output are under `.artifacts/gallery-collection-readback/`.

The published Gallery index still listed 1,001 routes. The 63 exact public reads in [AG-GAL-015](AG-GAL-015-verify-static-reviews.md#2026-11-22-collection-checks) include live legacy consumers of original evidence. Keep the current delivery and recovery objects. The [Airway backing review](AG-GAL-014-compact-delivery-and-recovery.md) remains deferred until a compatible same-origin replacement is available. Physical object versions and provider billing data were unavailable. This batch identified no additional remote retirement or billed savings.

## Release closeout cleanup

Retired the duplicate dependency installs from six ignored Gallery builds
under `sites/anatomy-gallery/.local/`:
`wave-1`, `migration-pathways`, `migration-arch`, `migration-arch-final`,
`migration-batch` and `retained-supplements`. Each lockfile and all 10,066
non-directory entries matched the retained `app/node_modules`. Paired builds
from the same saved sources produced byte-identical output with either
installation. The historical HTML and build inputs stay available. The
migration and supplement walkthroughs still served their original HTML after
cleanup, as did the specialist-still walkthrough and the protected release
candidate. Both preview media-recovery tests passed.

The closed `static-reviews-final`, `teaching-stills`, and `wave-2-walkthrough`
builds now resolve dependencies through relative links to
`../app/node_modules`. Their locks and all 10,795 directory entries per install
matched the retained tree. Rebuilds through the new links reproduced the exact
saved HTML for all three builds and two dependent walkthroughs. Their previews
and the older collection replay still work. The three copies accounted for
30,180 regular files, 234,065,181 logical bytes, and 327,327,744 allocated
regular-file bytes. Available volume space increased by 342,540,288 bytes during
removal. The two canonical physical installs remain in `app` and
`authoring-candidate`.

For an independent install in a linked build, confirm that its `node_modules`
is the relative link above, then remove just that link with
`unlink "$build/node_modules"` before running `npm --prefix "$build" ci`.
The saved source, lockfile, and `dist` stay in each build directory.

Retired the disposable bronchial trial checkout and duplicate replay under
`.artifacts/AG-GAL-021-bronchial-distal/`. The retained base and patch recreated
the complete staged index. All 1,010 cached LFS objects matched the shared
store by SHA-256. The replay GLB and build receipt matched the inspected
`build/` copies. Keep the trial receipts and the [adopted r14 export and
recipe](../../../models/bronchial_tree/exports/distal-sampling-r14/README.md).

Process and symlink checks passed for the eight directories. They held
1,531,790,123 logical bytes and 1,729,368,064 allocated regular-file bytes
after accounting for surviving hardlinks. Available volume space increased
by **1,211,764,736 bytes (1.13 GiB)** during deletion. The staging and candidate
archives, Airway rollback, and teaching ZIP retained their exact hashes.
A fresh extraction verified all 327 teaching members. The LFS dry run still
selected the 218 held objects. Commit `ac9324b` moved the three original
Body Systems concept prompts into the [dated study brief](../../../sites/body-systems-survey/study-brief.md#imagegen-concept-prompts)
and retired their standalone document. The 936 current-tree LFS bindings
and 26 historical transport manifests were unchanged.

The public Gallery readback still listed 1,001 distinct hashes declaring
995,630,117 bytes. The legacy Airway r06 evidence still pins both original
download paths, and full GETs matched both GLBs. Keep the two live backing
copies under [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md) through
cutover and rollback. Revisit them only after exact same-origin delivery
from a retained backing source passes public readback. Bucket inventory
remains unavailable to the connected Cloudflare account. No remote object
qualified for deletion, and no remote storage savings were measured.

### After public cutover

After the three public Sites passed readback, the disposable release checkout at `5f8fddf` and the dependency installs in `production-prep` and `rehearsal-prep` retired. The checkout was clean, its 89 ignored non-bytecode files matched the main checkout, and both dependency trees matched the retained qualification install across 10,066 file and symlink entries each. Available volume space rose by 1,096,986,624 bytes (1.02 GiB) during removal. The shared LFS store, live release archives and per-host rollback inputs remain. The [Airway file disposition](AG-GAL-014-compact-delivery-and-recovery.md#decision--retain-the-public-airway-downloads) keeps the two original downloads with active readers.

### Compact source publication

The [maintained family register](../../../docs/gallery/maintained-models.md) selects 79 teaching families. Ten source GLBs and eight supplementary review plates moved from LFS to two independently restored collection ZIPs. Checkout LFS payloads decreased from 936 files (987,328,919 bytes) to 918 (955,579,041 bytes). These are current-tree savings. The [archive index](../../../transport/collection-archives.json) records the two ZIPs. Historical LFS objects and the live Gallery's 1,246 exact routes have separate readers.

Published history through `9d70d26` and the three subsequent commits through `be9be24` retain their identities. The source URLs embedded in the public v10 client and delivery index use that third commit. The remaining work is grouped into three commits for assets and retention, Gallery implementation, and release and recovery records. In earlier dated records, a campaign SHA identifies the original execution; preserve that evidence under its original SHA. The local rescue branch `codex/rescue-gallery-93` and the verified private Git/LFS rescue ZIP retain those commits. Copy the rescue to independent private storage before retiring that branch. The [snapshot reference](../../../sites/anatomy-gallery/snapshot-reference.json) distinguishes the actual v10 release revision from the compact source revision that reproduces its compiled client.

### Workshop and Cardiac Atlas embedded textures

The 17 Workshop mesh GLBs supply 34 base-color and normal maps. The Cardiac wall PBR GLB supplies two more. Removing those loose PNGs took the current tree from 918 LFS paths (955,579,041 bytes) to 882 (926,631,634 bytes). The [restore command](../../../tools/restore_textures.py) checks the embedded bytes against the original import pins before writing files. The 132 Body Systems display WebPs keep their original identities.

In a clean clone hydrated with only the 882 tracked payloads, Blender opened the Workshop scene and its external-texture build with all 34 maps, and ran the cardiac normal diagnostic. The model-only cardiac ZIP contained both original wall PNGs. The payload gate now checks the embedded PNGs even when no loose files have been restored. This retirement changes checkout requirements; existing hosted objects and historical Git/LFS revisions retain their separate lifecycles.
