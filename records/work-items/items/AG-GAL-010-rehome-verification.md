---
description: Move ci packages to test owners while preserving workflow invocation and pinned evidence.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-GAL-010
work_status: done
work_kind: build
added: 2026-11-20
tags: repository, evidence
depends_on: AG-GAL-001
residual_of: none
residual_items: none
---

# AG-GAL-010 — Re-home runtime probes and source checks

## Intent

Retire the top-level `ci/` directory after the Site prepares its own vendor dependencies. Organize executable verification by the behavior it tests.

## Acceptance Criteria

- [x] Move browser and runtime probes with their pinned inputs under `tests/runtime/`. Move executable source checks and their inputs under `tests/source_checks/`.
- [x] Give any review-owned file read as a workflow fixture a test-owned input. Keep the historical witnesses and cited identities with their review.
- [x] Migrate workflow commands, path filters, sparse-checkout entries, docs and local consumers together. Preserve invocation guards, expected hashes, source and animation assertions, and receipt status semantics. Verify both normal and missing-input paths through the applicable entry points.
- [x] Verify that the ordinary Site build uses its own pinned setup. Retire `ci/` once its readers have moved.

## Context and Trade-offs

[AG-GAL-001](AG-GAL-001-name-and-verify-gallery.md) decouples the Site from legacy vendor inputs. The [guarded runtime workflow](../../../.github/workflows/firefox-glb-runtime.yml) and [FDI31 source workflow](../../../.github/workflows/fdi31-source-verification.yml) own online invocation. Keep execution under their existing authorization.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Accepted test ownership and the Site build dependency |
| 2026-11-20 | Codex | deferred | done | Moved sources and reran fixture, source-only, guard and ordinary Site checks locally. |

## Implementation Ledger

### Local verification

Moved browser sources, runtime recipes and pins from `ci/` to [tests/runtime](../../../tests/runtime/) and the FDI31 source-only command to [tests/source_checks](../../../tests/source_checks/). Updated the workflow invocations, sparse entries, change filters, One Breath, the historical Body Systems viewer, the heart fixture comparison and local regressions. The FDI31 workflow now also watches its transport helper.

The workflow reads the byte-identical test-owned morph expectations. The original bundle member remains with the historical manifest and prior run evidence. Current preparation produced the same 38,076-byte served fixture and preserved all 228 node tracks, 912 sampled values and 232 render primitives. Missing, corrupt and wrong-scope fixture paths failed in the offline regression. A direct run outside Actions refused before browser or network work. The source-only FDI31 suite passed and the command refused an existing destination before transfer.

The ordinary Site rebuilt from its own lock and remained independent of these fixtures. Hosted Firefox and FDI31 Actions are pending; no guarded job was dispatched.
