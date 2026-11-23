---
description: Move two small legacy directories into existing package and test owners.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-GAL-004
work_status: done
work_kind: build
added: 2026-11-20
tags: repository, evidence
depends_on: AG-GAL-002
residual_of: none
residual_items: none
---

# AG-GAL-004 — Put the viewer fixtures and abdomen patch with their owners

## Intent

Put the Anatomy Verification fixtures with their test consumers and the abdomen label replay with the 2D atlas. Keep scope to `gallery/` and `patches/abdomen-label-clarity-r01/`.

## Acceptance Criteria

- [x] Keep the pinned v50 inputs and regression coverage intact. Give eye and knee evidence a review owner and record the pharynx prototype’s unapplied status and keep its historical evidence.
- [x] Put the replay of the already-applied label correction with the atlas recipes. Retain exact before/after evidence and verify public file addresses still serve the recorded types and bytes when touched.
- [x] Fix imports, binding paths and documentation. Verify retained byte identities and supported replay and check entry points before closing the old directories.

## Context and Trade-offs

See the [Verification integration](../../../tests/viewer/README.md), [fixture source record](../../../tests/viewer/source.json), [patch](../../../body/2d-v4/whole-body-anatomy-v4-spatial/recipes/abdomen-label-clarity-r01/README.md), and [transport manifest](../../../transport/manifests/c95434900062d9c23d8ef46be1272dd2752982a3ea6aaed6b31fa0821e476dc4.json). Historical guide shims and other packages can be reviewed separately when their readers are known.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Selected two bounded moves from the directory review |
| 2026-11-20 | Codex | deferred | done | Moved the files and passed local replay, fixture and exact-byte checks. |

## Implementation Ledger

### Local result

The [viewer integration](../../../tests/viewer/README.md) owns the v50 candidate, camera/lifecycle/context helpers and elbow fixture. The eye and knee tests consume exact bound modules. Their earlier [eye templates](../../../reviews/eye_anterior_segment/2026-10-30-viewer-v47/README.md) and [knee comparison](../../../reviews/joints/knee-inspection-r01/README.md) live with review evidence. The [pharynx prototype review](../../../reviews/pharynx_larynx/2026-10-30-visibility/README.md) retains the matched figures and pinned replay source. The v40 patch was never incorporated and its working implementation has since been retired.

The abdomen replay is with the 2D atlas. From its pinned baseline it reproduced the current abdomen SVG byte for byte. A mismatched input was refused before creating output. Both local PNGs matched the retained transport record. All four URLs in the historical manifest returned 307 to public object addresses. Direct readback of those four targets returned the exact PNGs. The original cross-origin responses still require a compatibility decision for the guarded transport, which refuses cross-origin redirects. No hosted change was made.

Local v50 viewer, pinned CPU camera, gallery renderer and pharynx patcher regressions passed. The Gallery's local delivery declarations point to the moved knee and abdomen bytes while their published names, digests and historical source links remain the same. The old tracked directories and their generated Python caches were retired.
