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
| 2. Move and compact | Reuse existing views and evidence, starting with Head & Neck. Move files to their owners and prune redundant copies in the same slice. Sunset replaced visitor interfaces after authorized cutover. Bring possible reshoots and interaction rebuilds to the end-of-wave review. | [Migrate Head & Neck](../work-items/items/AG-GAL-003-migrate-head-and-neck.md) · [Account for remaining experiences](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md) · [Consolidate legacy repository packages](../work-items/items/AG-GAL-004-consolidate-legacy-packages.md) · [Separate Body Systems replay](../work-items/items/AG-GAL-005-separate-body-systems-replay.md) · [Co-locate diagram sources](../work-items/items/AG-GAL-009-colocate-diagram-sources.md) · [Re-home verification](../work-items/items/AG-GAL-010-rehome-verification.md) |
| 3. Rework and retire by collection | Use the direction agreed at the review below to rework selected views and interactions one collection at a time. Deprecate superseded variants and tools after their replacements and recovery pass. Simplify R2 delivery, on-demand retrieval and backup by applying and testing changes to one set of assets at a time. | [Refresh a legacy comparison](../work-items/items/AG-GAL-006-refresh-legacy-comparison.md) · [Plan R2 delivery and recovery](../work-items/items/AG-GAL-007-plan-r2-and-recovery.md) · [Apply the first storage change](../work-items/items/AG-GAL-014-compact-delivery-and-recovery.md) · [Re-home import records](../work-items/items/AG-GAL-011-rehome-import-records.md) · [Consolidate transport tools](../work-items/items/AG-GAL-012-consolidate-transport-tools.md) · [Evaluate full Head & Neck host shutdown](../work-items/items/AG-GAL-008-retire-head-and-neck-host.md) |

### Between Waves 2 and 3 — feel the vibe

The maintainer accepted the [trachea r06 presentation trial](../work-items/items/AG-GAL-006-refresh-legacy-comparison.md) on November 21. The [whole-Gallery release assessment](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#whole-gallery-release-assessment) records the accepted walkthrough limits and specialist deferrals. Future editorial rework starts from a named teaching question and a matched trial under the [design guide](../../docs/gallery/design.md).

## Learning ledger

- A declared R2 entry proves a recorded identity match. [Live file checks](../../transport/README.md#legacy-file-addresses) establish the response returned to a consumer.
- [The Site build](../../sites/anatomy-gallery/tools/gallery_runtime.py) reads the maintained Body Systems display export and restores Three.js independently from its own lock. The dated reports and backup member paths have their own replay package.

## Closeout

The November 22 release met the agreed migration scope with the collection dispositions and verified journeys linked above. Deferred specialist rebuilds, retained external tools and original file services keep their named owners. The [cleanup ledger](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md) records removals, recovery and tested limits. The deferred [Airway backing review](../work-items/items/AG-GAL-014-compact-delivery-and-recovery.md) and [Head & Neck host shutdown](../work-items/items/AG-GAL-008-retire-head-and-neck-host.md) reopen when their consumer and recovery conditions can be satisfied.
