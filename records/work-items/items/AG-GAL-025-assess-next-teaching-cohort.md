---
description: Assess three exact Gallery revisions with retained source and view evidence.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-025
work_status: done
work_kind: build
added: 2026-11-21
tags: gallery, evidence
depends_on: AG-GAL-018
---

# AG-GAL-025 — Assess three Gallery teaching revisions

Codex assessed three previously unrated revisions on 2026-11-21. The [canonical rubric](../../../docs/guides/asset-quality.md) is pinned at `a1115defec3676d942d3432242d29431109693f9`. The owner records bind each task and observation to the export digest, source references and inspected views.

| Exact export and assessment | Teaching action | Fidelity | Form | Readability | Economy |
| --- | --- | ---: | ---: | ---: | ---: |
| [Skin envelope · bp3d-envelope-r01](../../../reviews/skin/2026-10-24-bp3d-envelope-r01-bounded-migration/teaching-assessment.json) | Locate the shoulder, hand and foot outlines in the Body Systems envelope and confirm their depth. | Unrated | Unrated | 3 | 2 |
| [Right rotator cuff · z-rotator-cuff-r01](../../../reviews/joints/2026-10-30-rotator-cuff-r01/teaching-assessment.json) | Locate the three posterior muscles around the scapular spine and the subscapularis on the opposite face. | 4 | Unrated | 3 | 3 |
| [Illustrative thyroid · s0189 illustrative-exterior-r01](../../../reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/teaching-assessment.json) | Follow the thin bridge joining the two unequal lobes across the recess. | 4 | Unrated | 3 | 3 |

The retained views support localization. The form axes need neutral-material close-ups of the digit and foot edges, the cuff surface margins, and the thyroid depressions respectively. The skin fidelity axis also needs a direct landmark comparison to the archived FJ2810 member. The source-frame thyroid comparison covers the isolated exterior and preserves the case-specific bridge measurement. The cuff close-ups show a teaching role for the thin teres minor and scapular spine. The scapula accounts for 25,326 of the model's 38,678 triangles. The raw count leaves room for a future efficiency measurement while the visual evidence supports the contours as teaching landmarks.

The build reads the dated pilot plus `reviews/<asset>/<review>/teaching-assessment.json` records. The generated data carries the evaluator, date and rubric on each assessment. It refuses duplicate routes and export or image identities that conflict with the delivery index. The Library renders the existing rating and evidence disclosure only at a matching exact revision. General Library browsing can link to a rated revision. The established family bookmarks and recommended exports retain their existing routing. The dated pilot retains the ovary's Unrated form axis, the esophageal wall at 12/16 and bronchial r13 at 11/16.

## Skin envelope refinement trial

At the 680-pixel teaching scale, 75–79% of the control’s front-facing triangles projected to less than one square pixel, including occluded faces. The [navigation trial and viewer decision](../../../reviews/skin/2026-11-21-navigation-trial/README.md) retain the recipe-built lighter envelope for whole-body navigation. This assessment applies to r01.

## Local verification

The protected Gallery build used Node 24.21.0 and `9b0813a5fd2e737b64dd76d9a7ab3d5cba6faae5` plus this slice. Browser-tested HTML SHA-256 was `a8cf46a2270cbf862ee49e23a76f8a7af99e3a48cef67422b7b283d68e0461f5`. Chrome 157.0.8103.80 covered 103 revision and parent routes, 25 exact download responses, six assessment disclosures, and successful decoding and hash checks for all 24 reviewed views. Chrome found the new assessments by path and digest, retained unrated siblings and unavailable states, and displayed the original pilot's exact axes. The eleven new linked source files also resolved via GitHub at the recorded revision.

The assembly tests verified score and observation validation, cross-owner duplicate refusal, per-batch metadata and image identity mismatch. All 17 Site tests passed, including loopback delivery recovery. The repository payload-integrity gate passed with 442 offline tests and 1,012 hydrated LFS files. Receipts and captures are under `.artifacts/AG-GAL-025-library-assessments/`. This review covers static teaching views and local delivery. Specialist assessment, real-time performance and hosted publication remain outside the verification.
