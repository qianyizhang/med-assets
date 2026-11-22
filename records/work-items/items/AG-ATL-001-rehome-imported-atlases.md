---
description: Defer a possible major move of body and heart packages into atlases.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-ATL-001
work_status: deferred
work_kind: build
added: 2026-11-20
tags: repository, evidence
depends_on: none
residual_of: none
residual_items: none
---

# AG-ATL-001 — Re-home the imported atlas packages

## Intent

Revisit grouping `body/` and `heart/` under `atlases/` if a future maintainer can show a concrete improvement in use, maintenance or recovery.

## Acceptance Criteria

- [ ] Quantify the benefit and trace the impact on original import paths, public exports, review bindings, coordinate frames and recovery archives.
- [ ] Before any move, agree on a path mapping and prove that the verifier covers retained import identities and that old consumers and archive restores still work.
- [ ] Move the approved packages in bounded slices and verify the final layout against the accepted mapping. Close with a rationale if the benefit does not justify starting the migration.

## Context and Trade-offs

This item is outside the Anatomy Gallery campaign. Keep the current atlas paths during that work. Opportunistic package-level pruning can proceed when its readers, evidence and recovery have been checked. The [target ownership map](../../../docs/WORKFLOW.md#target-layout) describes the current atlas homes.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Deferred the major atlas move outside the gallery campaign |

## Implementation Ledger

No implementation events yet.
