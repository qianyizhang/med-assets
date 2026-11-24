---
description: Consolidate the public Anatomy Gallery, its legacy experiences, and their repository and delivery dependencies.
scope: multi-session gallery consolidation
status: stable
last_update: 2026-11-24
document_class: coordination
---

# Anatomy Gallery consolidation campaign

## Destination

Anatomy Gallery is the canonical public home for every retained med-assets viewing experience. A visitor can find an exact model, follow a lesson, inspect its evidence and reopen a shared 3D view without navigating between specialist sites. Each former experience has a Gallery destination or a documented retirement.

Consolidate the files behind those views as well. Keep one maintained home for each source, export, lesson, review and replay. Remove duplicate viewers, generated copies and obsolete variants once their readers have moved and unique evidence is recoverable. Keep original file delivery where a bookmark, download or pinned consumer still depends on it.

## Model relationship

The [glossary](../../GLOSSARY.md#gallery-and-surfaces) owns names. The [gallery requirements](../../docs/gallery/README.md) own the four surfaces. The [collection ledger](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) owns implemented destinations and exceptions. The [route guide](../../docs/gallery/routes-and-api.md#legacy-page-handoffs) owns page handoffs. [Repository workflow](../../docs/WORKFLOW.md#ownership) owns the target layout and verification. [Transport](../../transport/README.md) owns delivery and recovery. Linked work items own slice acceptance and implementation state.

## Current release

The agreed Gallery migration rollout is complete. The [collection ledger](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) records the destinations and accepted exceptions. Keep the verified UFF inspector bridge and the [static placements for deferred specialist journeys](../work-items/items/AG-GAL-016-integrate-retained-teaching.md#specialist-stills). Revisit the historical FDI31 r03, spinal raster and adipose searches when new sources appear.

[Gallery v10](https://med-assets-model-survey.landy123007.chatgpt.site/), [Head & Neck v2](https://anatomy-head-neck-review.landy123007.chatgpt.site/) and [Airway v8](https://anatomy-airway-review.landy123007.chatgpt.site/) passed public readback on 2026-11-22. The [release record](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) binds the integrated revision, preserved state, exact-file checks and separate rollback points. The authoring and local pruning slices landed. The legacy hosts continue to serve their consumed original files.

### Parallel release and cleanup work

The November 22 rollout is complete. The [authoring scaffold](../../docs/gallery/README.md#author-a-gallery-entry) uses the maintained s1233 study to add and exercise content across all four surfaces. The duplicate Survey browser retired. Its used bookmarks now open the corresponding Library or planning entry. The Body Systems study brief owns its concept prompts.

The [cleanup ledger](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md) records the retired local artifacts and measured storage changes. The original Head & Neck and Airway files still serve pinned downloads, and each live Site retains its independent rollback point. Host shutdown, history rewrites and deletion of a last source copy remain outside this rollout.

The [compact source publication](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md#compact-source-publication) records the maintained model families, cold archives and history recovery.

## Work

The waves below record the delivery sequence. The deferred host and storage follow-ups retain their own acceptance criteria.

| Wave | Exit condition | Work |
| --- | --- | --- |
| 1. Establish the clean gallery | From a clean checkout and documented inputs, one ordinary Site runs the four surfaces and both adrenal journeys. The duplicate pilot can retire. Check existing bookmarks and exact downloads. | [Name and verify the gallery](../work-items/items/AG-GAL-001-name-and-verify-gallery.md) · [Absorb the adrenal pilot](../work-items/items/AG-GAL-002-absorb-adrenal-pilot.md) |
| 2. Move and compact | Moved retained views and their inputs to the maintaining packages. Verified Gallery consumers, replay, source identities and failure paths. | [Migrate Head & Neck](../work-items/items/AG-GAL-003-migrate-head-and-neck.md) · [Account for remaining experiences](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md) · [Completed package moves](#completed-package-moves) |
| 3. Rework and retire by collection | Accepted the trachea presentation trial and completed the import and transport moves. Retained original file services under the separate host and backing decisions. | [Refresh a legacy comparison](../work-items/items/AG-GAL-006-refresh-legacy-comparison.md) · [Plan R2 delivery and recovery](../work-items/items/AG-GAL-007-plan-r2-and-recovery.md) · [Completed package moves](#completed-package-moves) · [Airway backing review](../work-items/items/AG-GAL-014-compact-delivery-and-recovery.md) · [Head & Neck host shutdown](../work-items/items/AG-GAL-008-retire-head-and-neck-host.md) |

### Between Waves 2 and 3 — feel the vibe

The maintainer accepted the [trachea r06 presentation trial](../work-items/items/AG-GAL-006-refresh-legacy-comparison.md) on November 21. The [whole-Gallery release assessment](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#whole-gallery-release-assessment) records the accepted walkthrough limits and specialist deferrals. Future editorial rework starts from a named teaching question and a matched trial under the [design guide](../../docs/gallery/design.md).

## Completed package moves

These six items are done. Their original acceptance criteria, status histories and detailed receipts remain in Git at `20abbe7` under `records/work-items/items/`. The summaries below preserve the outcomes, tested failures and delivery limits. Current commands and policy live with the linked package owners.

### AG-GAL-004

Completed November 20. Moved v50 viewer fixtures to [the test package](../../tests/viewer/README.md), eye and knee witnesses to their reviews, and the abdomen label replay to [the 2D atlas recipe](../../body/2d-v4/whole-body-anatomy-v4-spatial/recipes/abdomen-label-clarity-r01/README.md). The abdomen SVG replay matched byte for byte and refused a mismatched input before writing. Both local PNGs matched the transport record. All four historical URLs returned cross-origin 307s whose targets matched the exact PNGs. Guarded transport still refuses those redirects. Viewer, CPU camera, Gallery renderer and historical pharynx patcher checks passed. The unincorporated pharynx patch has since retired. Its [review](../../reviews/pharynx_larynx/2026-10-30-visibility/README.md#checks-and-delivery) identifies the historical replay checkout. Hosted routing was outside the move.

Original record `AG-GAL-004-consolidate-legacy-packages.md`.

### AG-GAL-005

Completed November 20. The [Body Systems lesson](../../lessons/body-systems/README.md) owns the display index and 132 WebPs. The [dated survey](../../sites/body-systems-survey/README.md) owns report replay, optional 3D controls and teaching recovery. All image, model and route identities survived the move. The ordinary Site built from its own viewer lock, Chrome checked all eleven systems, and all 132 exact displays passed delivery and exporter replay. Missing and same-size corrupt images returned 503 while other views and source links remained usable. Restoring the image recovered its exact 200 response. The 127,459,034-byte teaching ZIP and all 327 members passed fresh extraction, and the historical report and browser suite passed. Removed three byte-identical loose generated copies while retaining unique inputs and receipts.

Original record `AG-GAL-005-separate-body-systems-replay.md`.

### AG-GAL-009

Completed November 20. Moved editable inputs and builders for the biliary, oral, testis and urinary figures into [their diagram packages](../../diagrams/). Public export paths and bytes stayed fixed. Inkscape 1.4 reproduced all eight r01 decoded PNGs. Three generators reproduced their six editable SVGs, and both oral inputs matched their pins. Testis r02 reproduced both editable and both outlined SVGs byte for byte and all four reviewed pixel hashes at native and 800 px sizes. The original record pins the temporary Noto fonts and Inkscape distribution identity. Font binaries were outside the delivery.

Original record `AG-GAL-009-colocate-diagram-sources.md`.

### AG-GAL-010

Completed November 20. Moved guarded browser probes to [tests/runtime](../../tests/runtime/) and the FDI31 download checks to [tests/source_checks](../../tests/source_checks/), updating workflow commands, sparse inputs and local readers. The byte-identical fixture preserved 38,076 served bytes, 228 node tracks, 912 samples and 232 render primitives. Offline checks rejected missing, corrupt and wrong-scope inputs. Direct guarded execution outside Actions refused before browser or network work. FDI31 source checks passed and rejected an existing output directory before transfer. The ordinary Gallery built independently from its own lock. Hosted Actions were outside this local delivery. The FDI31 source workflow now uses manual dispatch.

Original record `AG-GAL-010-rehome-verification.md`.

### AG-GAL-011

Completed November 21 from parent `519645d`. Moved six byte-identical import records to [sources/imports](../../sources/imports/). The original 591-path snapshot, 430 then-retained paths and seven overrides preserved their identities. The other 161 paths stayed historical provenance. Before and after offline runs passed 439 tests, 26 transport manifests, 25 foundation records and 998 pointer identities. Payload integrity verified all 998 hydrated files and 11 package checks. Disposable-checkout failures distinguished changed immutable checksums or manifests, a missing imported file and an invalid original-hash override. The imported atlas README's historical `metadata/` link remains part of the immutable import. The [sources guide](../../sources/README.md#sources-and-scoped-uses) and [import contract](../../docs/WORKFLOW.md#import-and-source-integrity) lead to current records.

Original record `AG-GAL-011-rehome-import-records.md`.

### AG-GAL-012

Completed November 21 after `b461f8f`. [Transport tools](../../transport/tools/) own fetch, upload, backup, restore and guarded fallback. The canonical `delivery-index.json` matched the preceding index byte for byte, preserving all 1,243 routes and 26 manifests. The frozen framework still reads `r2-trial.json`, which the assembler generates from that canonical index in its output. Repository and local readers needed no old command shim.

Fresh empty-cache fetch and hydration matched the kidney and trachea GLBs. Missing or same-size corrupt remote bytes left the pointer and cache intact, and local edits were preserved. Teaching ZIP restore verified all 327 members, rejected bad archive identities and preserved an edited local member. Framework, seed and ten legacy dental payload checks passed, including seed overwrite refusal. Preview checks exercised exact GLB, PNG and MP4 responses, ranges, conditional reads and restored films. Workflow sparse-checkout fixtures, guarded manifest validation, six uploader tests, read-only mirror planning and 12 Site tests passed. Offline covered 440 tests and payload integrity covered 998 files and 11 package checks. Hosted jobs, uploads, remote mirror restore and storage retirement were outside this delivery.

Original record `AG-GAL-012-consolidate-transport-tools.md`.

## Learning ledger

- A declared R2 entry proves a recorded identity match. [Live file checks](../../transport/README.md#legacy-file-addresses) establish the response returned to a consumer.
- [The Site build](../../sites/anatomy-gallery/tools/gallery_runtime.py) reads the maintained Body Systems display export and restores Three.js independently from its own lock. The dated reports and backup member paths have their own replay package.

## Closeout

The November 22 release met the agreed migration scope with the collection dispositions and verified journeys linked above. Deferred specialist rebuilds, retained external tools and original file services keep their named owners. The [cleanup ledger](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md) records removals, recovery and tested limits. The deferred [Airway backing review](../work-items/items/AG-GAL-014-compact-delivery-and-recovery.md) and [Head & Neck host shutdown](../work-items/items/AG-GAL-008-retire-head-and-neck-host.md) reopen when their consumer and recovery conditions can be satisfied.
