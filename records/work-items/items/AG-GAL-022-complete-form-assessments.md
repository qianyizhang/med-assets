---
description: Resolve the missing form and surface evidence for two exact Library exports.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-022
work_status: done
work_kind: build
added: 2026-11-21
tags: gallery, evidence
depends_on: AG-GAL-018
residual_of: AG-GAL-018
residual_items: none
---

# AG-GAL-022 — Complete the ovary and esophageal form reviews

- [x] Pin both tasks, exports and the original rubric. Preserve the dated pilot.
- [x] Inspect matched neutral and alternate close-ups, document source limits and score against the rubric where supported.
- [x] Verify Library discovery, exact links, axes, totals and changed failure paths through the local build.

## Assessment

On 2026-11-21 Codex (agent review) followed up the [original pilot](AG-GAL-018-reconcile-library-revisions.md#teaching-assessment-pilot) with the same [rubric revision](../../../docs/guides/asset-quality.md), SHA-256 `76965de563c60a29f5c27a53f8a29081ee25dc4c5e0b6713c567243b1d5e0e4e`. The [active Gallery assessments](../../../reviews/teaching-assessments/2026-11-21-library-pilot/assessments.json) bind the exact file, unchanged task and ordered views. Each review records the neutral material, angles, camera, light and plate identities from the fresh GLB reimport.

| Exact Library route | Teaching action | Fidelity | Form | Readability | Economy | Teaching total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `library/ovaries/hra-ovary-tubal-r01` | Locate the fimbrial end next to each source-labeled ovary and point to the gap between them. | 4 | Unrated | 3 | 3 | Partially rated |
| `library/esophagus_wall/authored-cutaway-r01` | Read from the lumen to the adventitia and identify the two muscularis externa compartments within the four tunics. | 3 | 3 | 3 | 3 | 12/16 |

- [Ovary–tubal context review](../../../reviews/ovaries/2026-11-21-form-assessment-r01/README.md). Both sides show the fringe, adjacent ovary and visible separation. The evidence confirms the contours came from the source meshes. A registered source section or a suitable annotated surface reference is still needed to account for specific angular regions on the coarse ovarian surfaces.
- [Esophageal wall review](../../../reviews/esophagus_wall/2026-11-21-form-assessment-r01/README.md). The folded opening and wedge silhouette read in both neutral close views. The matched palette and labeled section identify the flush bands. This supports form 3 for the wall-order schematic. The specific fold geometry, thicknesses and surface finish are illustrative.

The three close-up plates are local preview evidence. Publication and specialist anatomy acceptance remain separate decisions.

## Local verification

The final protected build used `13c4f87` plus the AG-GAL-022 verification follow-up. The browser-tested HTML SHA-256 was `8cf74c602158faec71fe433d122cd6a25a49cbcd3f5ff46bacd6fde435e43d22`. Chrome 157 found both exact revisions by path and digest, opened and reloaded their Library pages, checked all axes and the displayed totals, and matched the downloaded GLBs and all 13 reviewed images across the two assessments and bronchial r13. All three new WebP plates decoded at 2880 × 1024 and their forged digests returned 404. Bronchial r13 remained 11/16 and its assessment matched the baseline. The Library regression covered 102 revision routes and 22 exact download responses. Assembly refused all three plates when their digests were changed in a test index. The protected Gallery build and repository offline gate passed. See the captures and verification receipt in `.artifacts/AG-GAL-022-form-assessments/`.
