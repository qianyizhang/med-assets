---
description: Improve form and surface for the flagged teaching assets.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: TAQ-011
work_status: done
work_kind: build
added: 2026-11-22
tags: gallery, evidence
depends_on: TAQ-004
---

# TAQ-011 — Refine misleading form and surface

[Below-target refinement campaign](../../campaigns/teaching-asset-refinement.md) · [Refinement evidence](../../../reviews/teaching-assessments/refinement-form/README.md) · [Accepted bindings](../../../reviews/teaching-assessments/refinement-form/accepted.json)

- [x] Cover the 13 exact exports at `7b07c7d` with form below 3, fidelity at least 3 and teaching readability at least 3.
- [x] Preserve each learner task and its protected landmarks. Use matched renderings and source evidence to distinguish verified anatomy, known source limits, authored junctions and unresolved defects.
- [x] For geometry trials, compare the actual clean-import candidate and control. Keep the source and exact evidence needed to replay accepted or rejected results.

The s0189 thyroid r02 exterior reduces repetitive rear-band ridges and preserves the unequal lobes and bridge. The lead reviewer accepted r02 for the bridge task with r01 retained as its exact comparison. The pelvic selection exposes cervix, bladder and rectum context and gives the original exterior task a form score of 3. The Workshop and pancreas selections expose the intended relationships with neighboring anatomy. The remaining source and specimen findings are available as callouts and matched close-ups, with unresolved detail still visible. The retained source heart shows the abrupt upper contours before display processing. The bronchial test left a collar and introduced small bright spots at the edited junction, so r14 retains the original disposition.

The [recipe and receipts](../../../reviews/teaching-assessments/refinement-form/README.md#replay-the-images-and-geometry) bind the tested baseline, renders and candidate. This work supports case-level or authored teaching tasks. Specialist review, clinical use and publication have separate acceptance.

## Local Library adoption

The [maintained register](../../../docs/gallery/maintained-models.md) selects [thyroid r02](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) for the original bridge task. Its [separate assessment](../../../reviews/teaching-assessments/refinement-form/campaign-assessments.json) records 4 / 3 / 3 / 3 and binds the matched teaching plate. Library history retains r01 at 4 / 2 / 3 / 3. Hosted routing continues to resolve the published r01.

The Library data check exercised the local recommendation, hosted exclusion and a round trip of the r02 Stage preset. All three preview delivery tests passed. A local HTTP probe fetched both r02 download routes, the exact teaching image, owner record, independent integrity receipt and original r01. Their bytes matched their recorded hashes. The public index included r01 and excluded r02.
