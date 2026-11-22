---
description: Establish which asset copies and recovery routes to keep before changing storage.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-007
work_status: done
work_kind: research
added: 2026-11-20
tags: transport, repository
depends_on: AG-GAL-003
residual_of: none
residual_items: none
---

# AG-GAL-007 — Plan R2 delivery, backup and pull-down changes

## Intent

For one collection, identify the storage and recovery complexity through an exact account of canonical exports, delivered copies, retained archives and real consumers.

## Acceptance Criteria

- [x] Reconcile Git/LFS, Site R2, the public Object Library, private or mirror recovery where applicable, and legacy file endpoints. Identify shared bytes, path aliases, rights, consumers and gaps using size and SHA-256.
- [x] Prove an on-demand pull-down in a fresh checkout and restore a representative retained archive with member checks. Exercise unavailable or corrupt copies and an existing local edit. Record which paths and revisions can actually be recovered.
- [x] Select the first set of assets for [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md). Specify which copies to keep, consolidate or retire, affected consumers, cost and recovery evidence. Record a retention decision if every copy in the examined set has a distinct use.

## Context and Trade-offs

The local Head & Neck milestone satisfies the dependency for this proof. Choose a collection with an identifiable delivered asset and retained archive. Report the bytes or maintenance steps a proposed retirement would save. Bring the recommendation back for review before changing storage.

The [transport policy](../../../transport/README.md) owns public and private delivery boundaries. [Mirror planning](../../../docs/BACKUP_CHECK.md) owns exact-tree checks. A storage change can use a smaller verified tranche before attempting broad retirement.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Captured delivery and recovery rework for Wave 3 |
| 2026-11-21 | Maintainer | deferred | ready | Approved a one-collection recovery proof alongside the editorial trial. |
| 2026-11-21 | Codex | ready | done | Verified the One Breath asset set and submitted a two-file recommendation for review. |

## Implementation Ledger

### Finding · One Breath airway-r01 inputs

Scope is the five [pinned lesson inputs](../../../lessons/one-breath/assets.json) and the editable airway route scene. Size and hash identify each copy, regardless of filename. The lung exports use `metadata-cleanup-r01`, the trachea exports use `open-airway-r06` (V7), and the authored airway route uses `airway-r01`. The checked Site entries use each canonical export path and basename. The legacy Airway Review serves the two trachea basenames at `/review/trachea-r06/models/`, and lesson preparation stages all five using the filenames in its manifest.

| Export or source | Bytes | SHA-256 | Verified recovery copies |
| --- | ---: | --- | --- |
| `lung_left.glb` | 2,524,996 | `6d3a6150dc47dba0d16162738caabc1bef3fcd8cf5ab4af492dd1121c1cb8533` | GitHub LFS and Site R2 |
| `lung_right.glb` | 2,653,664 | `3f8476ddd9d04448f4c1f63e85408860d7957f099e87170e8099efe635c16a78` | GitHub LFS and Site R2 |
| `trachea-open.glb` | 962,440 | `eb3ce52962aacc4d109a9840685aa172ca1d97bfc835367f4e36fd32de6b6cbb` | GitHub LFS, Site R2 and legacy Airway Review |
| `trachea-cutaway.glb` | 1,564,740 | `42b25a9e3de950db1a083da3802d4bb982c9084c425f768824c8973dc08be283` | GitHub LFS, Site R2 and legacy Airway Review |
| `airway-route.glb` | 2,083,460 | `92fd447bad48b03489041e16d0de8750b550034ec4f158219b8352571e0e6091` | Public Object Library archive and retained local ZIP |
| `airway-route.blend` | 2,019,816 | `e6290f086a75aa79bc26b5d983994f8911f66cce7b46abc594e6309255e2f545` | Public Object Library archive and retained local ZIP |

The [teaching ZIP and restore instructions](../../../sites/body-systems-survey/README.md#restore-the-media) pin source `c803735865f4f14d6baf939c13b10f112445fe48` and a 127,459,034-byte archive with SHA-256 `ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014`. The archive covers its listed teaching members and excludes the four Git/LFS model hashes. It restores the GLB and editable scene to `lessons/one-breath/airway-r01/`. Both are archive-only at the tested revision. Private and full-tree mirror recovery remain unverified for these inputs. [Mirror scope](../../../docs/BACKUP_CHECK.md#scope-and-older-source-archives)

The [lesson manifest](../../../lessons/one-breath/assets.json) and preparation consume all five models. The Gallery and legacy Airway Review expose the two trachea exports separately. Body Systems and the airway-route recipe consume the cutaway. The route GLB also supplies Body Systems' refinement and the [terminal study comparison](../../../lessons/one-breath/terminal-study-r02/compare.py). The editable scene supports airway-route replay and authoring. The [lesson credits](../../../lessons/one-breath/licenses/ATTRIBUTION.md) retain TotalSegmentator CC BY 4.0 and its separate original label notice, with additional Workshop and BodyParts3D credits for the route. Existing public delivery and recorded attribution cover this readback. The package declares no blanket license on authored material.

### Verification · Fresh fetch, restore and consumer

The commands below use the paths from the tested revision. For a current checkout, see the [transport commands](../../../transport/README.md#public-r2-downloads).

1. Cloned the local Git source with `--no-hardlinks --no-checkout` and checked out `a1e97473efeff251d823e32c94efda6422fc5c7f` with `GIT_LFS_SKIP_SMUDGE=1`. The four tracked models started as pointers. With an empty fetch cache, `python3.12 tools/fetch_asset.py <exact-path> --hydrate` retrieved all four from the public Site and preserved the working files' permissions. An independent GitHub LFS fetch into an explicitly empty LFS store matched the same four size and hash pairs.
2. Downloaded the public teaching ZIP into a new location, matched it to the pinned archive identity and extracted it with the documented non-overwrite command. The archive path list and all 327 member hashes matched the tracked [member manifest](../../../sites/body-systems-survey/backup-sha256.txt). The retained local ZIP matched independently. The two legacy trachea URLs returned HTTP 200, exact bodies and `application/octet-stream`. Their metadata remains distinct from the Gallery delivery routes.
3. Ran the pinned One Breath preparation from the recovered checkout. The five model bindings and five pinned Three.js files passed verification, along with 37 lesson tests and the five-lobe phase sweep in Node. The earlier lesson browser review remains the latest WebGL evidence.
4. Injected an unavailable response (HTTP 404) and equal-length corrupt bytes at the fetch CLI's response boundary. Both failed with the original pointer intact and an empty cache. An existing edit stayed byte-for-byte intact, although the CLI described it as a malformed LFS pointer. The archive checksum gate stopped missing and corrupt ZIPs before extraction. With a pre-existing edited route export, `unzip -n` kept the edit and the final check flagged that member while the other 326 passed.

### Handoff · First candidate for AG-GAL-014

Keep the four canonical Git/LFS exports, four Site R2 deliveries, both copies of the teaching ZIP, and the derived lesson staging while its local consumer needs those files. The Site R2 delivers the exact models to Gallery visitors and supports selective hydration. The teaching ZIP covers independent recovery for the authored route and editable scene. The legacy review still links both of its trachea files, so keep those two URLs and their original-host response contract.

Select only `trachea-open.glb` and `trachea-cutaway.glb` on the legacy Airway Review host for the first consolidation. If that host can serve the same successful response from a verified Site R2 backing source, retire its two separately managed payload copies while preserving the exact public URLs. That would eliminate 2,527,180 bytes of duplicate payload per legacy deployment and two files from its deployment inputs. Actual billed savings depend on how the host stores past deployments. Before removing either legacy copy, verify original-host delivery, bytes, media type, and the review's download links through the candidate and then in production under separate authority. Keep both copies if the compatibility response cannot be reproduced. The maintainer deferred this proposal until public cutover in [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md).

### Follow-up · Recovery diagnostics

Review of the retained local ZIP confirmed the archive digest and all 327 member identities. The five local lesson models matched their manifest. The original edited-file check exposed two misleading messages in the fetch CLI. Hydration now checks working contents before looking up delivery or fetching bytes. An edited model of either the original size or a different size reports that its contents were preserved. The CLI tests cover both cases.
