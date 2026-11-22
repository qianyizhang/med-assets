---
description: Assess the teaching quality of the maintained 3D assets and test improvements against the learner task.
scope: maintained 3D models and assemblies
status: stable
last_update: 2026-11-22
document_class: coordination
---

# Teaching asset review campaign

For each maintained family, answer two questions. What can a learner identify, distinguish or trace using the selected export? Which change, if any, would help them do it?

## Scope and evidence

Start with the [maintained family register](../../docs/gallery/maintained-models.md). At baseline `a6f4b3c` it selects 79 files across 12 groups, including two editable assemblies. The [discovery audit](../work-items/items/AG-GAL-018-reconcile-library-revisions.md#reconciled-library) established which older public files could be found in the Library. Use that audit for provenance. Reconcile subsequent changes against the register and the current Library.

Count each family once against its starting file. Identify any other export needed for a distinct teaching task, including a published revision still in use. Show those assessments separately so alternate files cannot inflate family coverage. If the selected file is an assembly, assess the assembly in the interaction or view the task requires.

Use the [quality rubric](../../docs/guides/asset-quality.md) for scores and attribution. The review belongs to an exact export and task. The coverage report points to its evidence and names the next action. Keep the original evidence accessible when an improvement introduces a new revision. A candidate becomes Recommended through the [maintainer decision](../../docs/gallery/asset-library.md).

## Work and acceptance

| Work item | Deliverable |
| --- | --- |
| [TAQ-001 · Establish coverage](../work-items/items/TAQ-001-establish-review-coverage.md) | A reproducible view of the current 79 starting files with full, partial and missing assessments. |
| [TAQ-002 · Review Respiratory](../work-items/items/TAQ-002-review-respiratory.md) | A task, assessment decision and evidence for each of the ten Respiratory starting files. |
| [TAQ-003 · Test a Respiratory improvement](../work-items/items/TAQ-003-test-respiratory-improvement.md) | A matched comparison for one supported improvement or the evidence for keeping the existing assets. |
| [TAQ-004 · Review the remaining collections](../work-items/items/TAQ-004-review-remaining-collections.md) | Collection-sized review and improvement batches for the other 69 families. |

Close when every starting file has an attributable assessment or a specific evidence gap, and each prioritized finding has a verified resolution, a documented keep decision or an owned follow-up. Record coverage, actual improvements and unresolved limitations separately. Reconcile additions and replacements since the baseline explicitly.

## Review decisions · 2026-11-22

The maintainer authorized Sol to repeat inspections wherever they improve confidence, generate missing evidence, and proceed through every collection autonomously. Prioritize misleading anatomy and hard-to-read teaching views. Pursue mesh savings when measurements show a benefit and the teaching landmarks survive. Make a local candidate for a supported improvement and retain the comparison that explains its disposition.

Sol owns the collection assessments and proposed refinements. The lead reviewer owns calibration and the final collection decisions. Use the [cross-collection review standard](../../docs/guides/asset-quality.md#review-a-teaching-set) and link the lead review from [TAQ-004](../work-items/items/TAQ-004-review-remaining-collections.md). Compare a previously assessed example, a borderline score and a changed asset across collections. Review the actual lesson context as well as isolated exports. Resolve score disagreements against the evidence and preserve reviewer attribution. If a material design choice remains, show a small number of matched variants for the maintainer to choose. Continue independent work while that choice is open.

## Outcome · 2026-11-22

[Lead review and teaching decisions](teaching-asset-review/lead-review.md) · [Current scorecard](teaching-asset-review/current-coverage.md) · [Baseline counts and replay](../work-items/items/TAQ-001-establish-review-coverage.md#result)

The three collection batches in [TAQ-004](../work-items/items/TAQ-004-review-remaining-collections.md#delivered-collection-batches) and the Respiratory pilot reviewed all 79 starting files. Seventy-eight have four scores, one has an explicit source gap, and 32 meet the four-axis target. Eight Library files gained a selected teaching view. [TAQ-008](../work-items/items/TAQ-008-use-reviewed-plates-in-lessons.md) carries two reviewed plates into existing lessons. [TAQ-009](../work-items/items/TAQ-009-test-marrow-lattice-economy.md) retains a measured recipe-built geometry option for the femur cutaway. Results are local. Published revisions and maintainer recommendations retain their existing identities.

## Delivery evidence

Implementation revision `088be25a2ad7a32ce7fe8731a9ef07d245dfe954`. The pinned Gallery build produced HTML SHA-256 `f7378236cc81e8e8671f9b7df2143cdb40e31e22061fbc5354ff6c83bb0cdd8d`.

| Check | Verified outcome |
| --- | --- |
| Exact coverage and attribution | The [coverage command](teaching-asset-review/coverage.py) reproduced the 79-file report at campaign close. The scorecard now follows the maintained register. Local file and section links in the changed Markdown resolved. |
| Repository and payloads | 448 offline tests, 26 manifests, 25 foundation records, 394 import references, and 937 hydrated LFS identities totaling 933,104,986 bytes. Thirteen package checks and seven isolated UFF dental tests passed. |
| Local Gallery | The protected build, 15 packaged tests and two preview delivery tests passed. Chrome walked 98 Library rows and 103 revision or package routes, verified 25 exact downloads, exercised all 79 campaign disclosures, fetched and decoded 123 bound view images and exercised missing teaching-image recovery. The full eleven-system and four-surface journey passed. |
| Teaching and geometry | Two lesson plates passed exact-image, keyboard, 1024/1280-pixel layout, missing-image, neighboring-lesson and simulated hosted-origin checks. The bronchial preset and recovery check passed. The [marrow trial](../work-items/items/TAQ-009-test-marrow-lattice-economy.md) reproduced both candidate GLBs and its matched views. |

The accepted build and local receipts are under `.artifacts/teaching-asset-review/`. The [lead review](teaching-asset-review/lead-review.md) and work items own the durable decisions, source limitations and replay instructions. Hosted publication and specialist assessment have separate acceptance.
