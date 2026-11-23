---
description: Improve the learner views for the ten files with fidelity or readability below three.
scope: exact 2026-11-22 campaign exports in local Anatomy Gallery
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: TAQ-010
work_status: done
work_kind: build
added: 2026-11-22
tags: gallery, teaching, evidence
depends_on: TAQ-008
---

# TAQ-010 — Refine teaching risks

[Below-target refinement campaign](../../campaigns/teaching-asset-refinement.md) · [Per-export outcomes](../../../reviews/teaching-assessments/refinement-risk/accepted.json)

The prior campaign scored ten exact exports below 3 on either fidelity or teaching readability. The local Library and lesson openings at `7b07c7d` establish the comparison baseline. Earlier visibility plates are part of that baseline.

The ten new learner views address the immediate point of confusion: disputed lymph node vessels, hidden eye and bladder landmarks, UFF slice selection failure, the obscured urethral course and diaphragm crest, subtle cardiac deformation, overlapping digestive alternatives, and the missing thyroid in the target-only parathyroid component. Eight tasks gained a readability point. The two digestive tasks now have separate source and teaching-section modes on the exact files. The cardiac task has exact-clip scrubbing with a wall-and-aorta selection.

The lymph node's fidelity remains 2 because its blood/lymph metadata conflict remains unresolved and the projection cannot establish layer contacts. The parathyroid target-only file's readability remains 2 because it lacks the thyroid required by the task. The new paired plate distinguishes that file from the separately verified context companion.

## Verification

The [review bundle](../../../reviews/teaching-assessments/refinement-risk/README.md) contains exact-file render and plate receipts, replay commands, and source limits. The matched panels were inspected after correcting callouts on the bladder, lymph node, and dental views. The baseline Chrome run checked the ten Library openings and the existing breathing and lymphatic lessons at 1280 pixels. The [focused Gallery Chrome check](../../../sites/anatomy-gallery/tools/verification/refinement-scenes.mjs) verified the exact three interactive views, visible changes after selection or scrubbing, recovery after loading failures, and state on Stage reload. Repository gates are recorded in the campaign delivery.
