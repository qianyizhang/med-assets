---
description: Trial a separate lossless repack of the static opaque heart exterior.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-019
work_status: done
work_kind: build
added: 2026-11-21
tags: heart, repository
depends_on: AG-GAL-018
residual_of: AG-GAL-018
residual_items: none
---

# AG-GAL-019 — Repack the static opaque heart exterior

The [first trial in AG-GAL-018](AG-GAL-018-reconcile-library-revisions.md#ranked-simplification-candidates) isolates payload left by the r01 visibility operation. The [package recipe](../../../heart/exterior-presentation-r01/README.md#static-repack-candidate) builds a separate local candidate from the exact r01 control.

- [x] Save at least 5,000,000 export bytes using only unreachable data. The candidate saves 5,543,680 bytes (61.93%).
- [x] Match decoded primitives, materials, transforms, hierarchy and names. Both clean Blender imports retain the same 124 individually selectable objects. Matched whole and neutral close-up renders have zero differing pixels.
- [x] Exercise deterministic replay, failure paths and repository gates. See the [heart review and receipts](../../../reviews/heart_exterior/2026-11-21-static-repack/README.md).

Accepted as a verified local packaging candidate. [AG-GAL-020](AG-GAL-020-adopt-static-heart-repack.md) records the separate Gallery adoption and consumer verification. Remote or billed savings require a separate deployment and measurement.
