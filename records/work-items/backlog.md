---
description: Discover and triage cross-session med-assets work.
scope: backlog
status: stable
last_update: 2026-11-21
document_class: coordination
---

# Backlog

Start with the [Anatomy Gallery campaign](../campaigns/anatomy-gallery-consolidation.md) for wave order and scope. Each work item's status, dependencies, acceptance and verification live in its [record](items/). Gallery and atlas items keep their established `AG-GAL` and `AG-ATL` IDs. Use the record structure from the [repo-kit work-item format](https://github.com/qianyizhang/repo-kit/blob/main/template/docs/rules/doc.md#work-item-records).

| Tag | Scope |
| --- | --- |
| gallery | Product, routes and visitor journeys |
| repository | Ownership, compaction and local replay |
| evidence | Reviewed exports, views and findings |
| transport | File compatibility, delivery and recovery |

```sh
rg -n '^work_status: (ready|wip|blocked)$' records/work-items/items
```

The [collection ledger](items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) records the migrations and public cutovers. The [Gallery walkthrough](../campaigns/anatomy-gallery-consolidation.md#between-waves-2-and-3--feel-the-vibe) sets the direction for editorial rework after the moves. [Oral spaces and regional locators](items/AG-GAL-016-integrate-retained-teaching.md#oral-spaces-and-regional-locators) passed the maintainer walkthrough. The maintainer approved the three bilingual pathways, dental arch identification and small archive migrations with recoverable evidence in the same local batch.

## Teaching asset review

The [completed campaign](../campaigns/teaching-asset-review.md) covers 79 maintained families. Start with the [lead review](../campaigns/teaching-asset-review/lead-review.md) for teaching decisions and the [coverage report](../campaigns/teaching-asset-review/current-coverage.md) for exact profiles and remaining evidence gaps.

## Deferred follow-up

- [AG-GAL-014 — Review backing for the original Airway downloads when a same-origin replacement is available](items/AG-GAL-014-compact-delivery-and-recovery.md)
- [AG-GAL-008 — Evaluate full Head & Neck host shutdown](items/AG-GAL-008-retire-head-and-neck-host.md)

## Outside the Anatomy Gallery campaign

- [AG-ATL-001 — Re-home the imported atlas packages](items/AG-ATL-001-rehome-imported-atlases.md)
