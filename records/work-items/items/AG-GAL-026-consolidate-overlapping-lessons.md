---
description: Give repeated learner questions one maintained lesson, starting with the ovary and tubal end.
scope: Anatomy Gallery lessons
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-026
work_status: done
work_kind: build
added: 2026-11-22
depends_on: TAQ-019
tags: gallery, lessons
---

# AG-GAL-026 — Consolidate overlapping lessons

**Owner** · Gallery campaign lead. Start after the current teaching-asset refinement round. Use its accepted editions and record the starting revision.

**First lesson** · “Where is the fringed end of the fallopian tube relative to the ovary?” Open with the pelvis for orientation, then show each source-labeled ovary and the visible gap beside the fringe. The pelvis illustration and source close-ups have independent frames and scales. Label the transition and retain the existing English and Chinese teaching material. [Ovary lesson package](../../../lessons/ovary-tubal-context/README.md)

## Acceptance

- [x] Give the teaching sequence one content owner. Both existing entry links, **Reproductive → left pickup** and **Regional Locators → ovary and tubal end**, reach it. Keep each collection's return path and the reproductive sequence's neighboring steps. A learner can point to the ovary, fringed end and intervening gap from either entry.
- [x] Compare learner questions across the [Body Systems stops](../../../lessons/body-systems/reviewed-stops.json) and [other use cases](../../../reviews/teaching-assessments/use-case-checks.json). Consolidate confirmed repeats across the Gallery. Where shared anatomy serves distinct actions, keep those actions discoverable and record the distinction briefly in the existing review. The two check lists are starting points for discovery. Inspect the actual routes and neighboring stops.
- [x] Exercise both entry and return journeys, old bookmarks, the source/scale cue and the missing-image fallback in the local Gallery. Update the [use-case guide](../../../docs/gallery/use-cases.md), lesson checks and affected links. Remove redundant beta lesson content once its readers use the retained version. Run the [applicable gates](../../../docs/WORKFLOW.md#verification).

Use the resulting lesson requirements to select the [shared organ model pilot](AG-GAL-027-merge-reusable-organ-assets.md).


## Accepted locally on 2026-11-23

Starting revision `41b7186`. Reproductive left pickup and Regional Locators now read one [bilingual sequence](../../../lessons/ovary-tubal-context/lesson.json). The pelvis sets orientation. The next panel names the change to enlarged HRA-derived views, shows the interpreted ovarian contour, and leaves the fringe and gap visible on both labeled sides. The original HRA plate opens under **Compare with source**. The historical comparison and download keep their original identities.

The [Gallery overlap review](../../campaigns/organ-and-lesson-overlaps.md) also identified the airway route in One Breath and Respiratory. One Breath links to the maintained Respiratory route and retains its own mechanics, cutaway and gas-exchange steps. The original storyboard remains available. Shared vocabulary or anatomical parts alone did not qualify the other routes for consolidation.

Chrome exercised both ovary entries, returns, neighboring Reproductive steps, old bookmarks, keyboard navigation, the source/scale transition, exact images and GLB, and missing-media recovery at desktop and laptop widths. Run the focused check with `verify_gallery.mjs --ovary`. The shared delivery and repository checks are recorded in [AG-GAL-027](AG-GAL-027-merge-reusable-organ-assets.md).
