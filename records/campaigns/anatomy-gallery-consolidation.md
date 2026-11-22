---
description: Consolidate the public Anatomy Gallery, its legacy experiences, and their repository and delivery dependencies.
scope: multi-session gallery consolidation
status: stable
last_update: 2026-11-22
document_class: coordination
---

# Anatomy Gallery consolidation campaign

## Destination

Anatomy Gallery is the canonical public home for every retained med-assets viewing experience. A visitor can find an exact model, follow a lesson, inspect its evidence and reopen a shared 3D view without navigating between specialist sites. Each former experience has a Gallery destination or a documented retirement.

Consolidate the files behind those views as well. Keep one maintained home for each source, export, lesson, review and replay. Remove duplicate viewers, generated copies and obsolete variants once their readers have moved and unique evidence is recoverable. Keep original file delivery where a bookmark, download or pinned consumer still depends on it.

## Model relationship

The [glossary](../../GLOSSARY.md#gallery-and-surfaces) owns names. The [gallery requirements](../../docs/gallery/README.md) own the four surfaces. The [migration contract](../../docs/gallery/migration.md) owns collection destinations and compatibility. [Repository workflow](../../docs/WORKFLOW.md#ownership) owns the target layout and verification. [Transport](../../transport/README.md) owns delivery and recovery. Linked work items own slice acceptance and implementation state.

## Current release

The retained collections have local Gallery destinations. The [collection ledger](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) owns the mappings and known exceptions. Keep the verified UFF inspector bridge and the [static placements for deferred specialist journeys](../work-items/items/AG-GAL-016-integrate-retained-teaching.md#specialist-stills). Revisit the historical FDI31 r03, spinal raster and adipose searches when new sources appear.

[Gallery v10](https://med-assets-model-survey.landy123007.chatgpt.site/), [Head & Neck v2](https://anatomy-head-neck-review.landy123007.chatgpt.site/) and [Airway v8](https://anatomy-airway-review.landy123007.chatgpt.site/) passed public readback on 2026-11-22. The [release record](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) binds the integrated revision, preserved state, exact-file checks and separate rollback points. The authoring and local pruning slices landed. The legacy hosts continue to serve their consumed original files.

### Parallel release and cleanup work

The November 22 rollout is complete. The [authoring scaffold](../../docs/gallery/README.md#author-a-gallery-entry) uses the maintained s1233 study to add and exercise content across all four surfaces. The duplicate Survey browser retired. Its used bookmarks now open the corresponding Library or planning entry. The Body Systems study brief owns its concept prompts.

The [cleanup ledger](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md) records the retired local artifacts and measured storage changes. The original Head & Neck and Airway files still serve pinned downloads, and each live Site retains its independent rollback point. Host shutdown, history rewrites and deletion of a last source copy remain outside this rollout.

The [compact source publication](../work-items/items/AG-GAL-017-local-and-remote-storage-cleanup.md#compact-source-publication) records the maintained model families, cold archives and history recovery.

## Work

| Wave | Exit condition | Work |
| --- | --- | --- |
| 1. Establish the clean gallery | From a clean checkout and documented inputs, one ordinary Site runs the four surfaces and both adrenal journeys. The duplicate pilot can retire. Check existing bookmarks and exact downloads. | [Name and verify the gallery](../work-items/items/AG-GAL-001-name-and-verify-gallery.md) · [Absorb the adrenal pilot](../work-items/items/AG-GAL-002-absorb-adrenal-pilot.md) |
| 2. Move and compact | Reuse existing views and evidence, starting with Head & Neck. Move files to their owners and prune redundant copies in the same slice. Sunset replaced visitor interfaces after authorized cutover. Bring possible reshoots and interaction rebuilds to the end-of-wave review. | [Migrate Head & Neck](../work-items/items/AG-GAL-003-migrate-head-and-neck.md) · [Account for remaining experiences](../work-items/items/AG-GAL-013-reconcile-gallery-coverage.md) · [Consolidate legacy repository packages](../work-items/items/AG-GAL-004-consolidate-legacy-packages.md) · [Separate Body Systems replay](../work-items/items/AG-GAL-005-separate-body-systems-replay.md) · [Co-locate diagram sources](../work-items/items/AG-GAL-009-colocate-diagram-sources.md) · [Re-home verification](../work-items/items/AG-GAL-010-rehome-verification.md) |
| 3. Rework and retire by collection | Use the direction agreed at the review below to rework selected views and interactions one collection at a time. Deprecate superseded variants and tools after their replacements and recovery pass. Simplify R2 delivery, on-demand retrieval and backup by applying and testing changes to one set of assets at a time. | [Refresh a legacy comparison](../work-items/items/AG-GAL-006-refresh-legacy-comparison.md) · [Plan R2 delivery and recovery](../work-items/items/AG-GAL-007-plan-r2-and-recovery.md) · [Apply the first storage change](../work-items/items/AG-GAL-014-compact-delivery-and-recovery.md) · [Re-home import records](../work-items/items/AG-GAL-011-rehome-import-records.md) · [Consolidate transport tools](../work-items/items/AG-GAL-012-consolidate-transport-tools.md) · [Evaluate full Head & Neck host shutdown](../work-items/items/AG-GAL-008-retire-head-and-neck-host.md) |

### Between Waves 2 and 3 — feel the vibe

Once the light migrations have put the material in its intended homes, walk through the assembled Gallery together. Open an ordinary collection, a strong example and one that feels awkward. Look at them at their normal viewing size and follow the lesson or review they support. Which shots already work? Where does the collection feel inconsistent, hard to read or repetitive? What would we happily remove?

Record a few concrete examples and why they matter. Choose what to keep as it is, what to retire, and at most one representative artifact to try reworking. If the Gallery already works well, record that judgment and skip the reshoot. Otherwise review the trial in context before deciding which lessons from it should guide the next collection. The exact refactor standard stays open until then. This gate governs editorial rework. File identity, attribution, tested delivery and recovery continue under their existing contracts.

## Learning ledger

- A declared R2 entry proves a recorded identity match. The [migration baseline](../../docs/gallery/migration.md#page-addresses-and-file-addresses) and live file checks answer different questions.
- [The Site build](../../sites/anatomy-gallery/tools/gallery_runtime.py) reads the maintained Body Systems display export and restores Three.js independently from its own lock. The dated reports and backup member paths have their own replay package.

## Closeout

Close when every public viewing experience in the migration inventory has a verified Gallery destination or a recorded retirement. Deferred specialist rebuilds and explicitly retained external tools keep an owner and disposition. They do not gate the four retained Gallery journeys. Record the owner of each remaining compatibility route. For each consolidated package, identify what was removed, what still needs to be retained and how to recover the required inputs. Verify the adopted storage changes through the normal pull-down and restore commands. Full host shutdown has its own decision.
