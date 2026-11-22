---
description: Prove a repeatable rework and deprecation slice on one retained comparison.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-006
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, evidence
depends_on: AG-GAL-005
residual_of: none
residual_items: none
---

# AG-GAL-006 — Try a clearer trachea r06 comparison

## Intent

Help a learner answer “What does the r06 cutaway reveal that the r05 closed cast hides?” The original overview fit three variants into half the page. Test the presentation on the local trachea review.

## Acceptance Criteria

- [x] Show the retained whole-airway overview at full content width, followed by the proximal detail. Preserve the source identities, comparison order, limits and links to both revisions.
- [x] Compare the original and trial at the same laptop viewport. Check whether the opening is visible and the reader can identify which representation exposes it. If it still reads poorly, retake only the decisive shot from the exact export, recording camera, scale and a distinct evidence identity.
- [x] Deliver a local before/after comparison and explain what improved or still needs work.
- [x] Review the trial with the maintainer before applying the treatment to another collection.

## Context and Trade-offs

Use the [gallery display policy](../../../docs/gallery/design.md#display-images), [visual comparison requirements](../../../docs/WORKFLOW.md#evidence-for-comparison) and [teaching-asset rubric](../../../docs/guides/asset-quality.md). Keep the original evidence for claims that still cite it.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Seeded the first collection-sized rework |
| 2026-11-21 | Maintainer | deferred | ready | Selected trachea r06 for the local presentation trial. |
| 2026-11-21 | Codex | ready | wip | Passed the local comparison and returned the trial for maintainer review. |
| 2026-11-21 | Maintainer | wip | done | Accepted the full-width local trachea layout and selective reuse. |

## Implementation Ledger

### Verification · Matched laptop views

The trial changes only the saved trachea r06 review at `/#/compare/trachea-r06`. It answers the question before the figure. The r06 cutaway exposes the modeled Y-shaped cavity from the upper opening through the fork to both branch outlets. The r05 closed cast shows the outer shape, and the middle r06 open shell shows the upper rim while retaining its enclosing side wall.

Chrome at 1280 × 900 CSS pixels showed the same whole-airway WebP at 518 px wide on decision commit `a1e9747` and 1,048 px wide in the trial. The full overview and its three labels fit in the first screen. The top rim is easy to distinguish from the r05 cap, and the cutaway's inner surface can be followed through the fork. The branch outlets remain small, and the next screen's proximal detail confirms the upper rim only. The enlarged view is sufficient for the stated question. Both WebPs retain their exact hashes and [projection provenance](../../../reviews/trachea/2026-10-29-open-airway-r06/projection-bindings.json), so a new shot was unnecessary. The matched captures, build fingerprints and local preview command are in the ignored `.artifacts/anatomy-gallery-wave-3/` bundle.

Both revision links were exercised. The pinned Gallery build, Site tests, Chrome journey and repository offline gate passed. At 1024 × 768 the trial fit without horizontal scrolling. A failed overview request showed its unavailable notice while the detail and source link remained reachable. Anatomy, the 3D exports and hosted delivery retain their prior evidence. The maintainer accepted the layout on 21 November. The [design guide](../../../docs/gallery/design.md#display-images) records when to reuse it.
