# Refine the 46 below-target teaching assets

At `7b07c7d`, the [maintained-file review](teaching-asset-review/lead-review.md) identified 46 starting files with at least one assessed axis below 3. Keep that denominator and the original learner task. The other 33 starting files include the partial ovary assessment.

| Work item | Reason to open it | Acceptance |
| --- | --- | --- |
| [TAQ-010 · Teaching risk](../work-items/items/TAQ-010-refine-teaching-risks.md) | 10 revisions with fidelity or readability below target | Try to perform the same task in the current and proposed teaching experience. Test the change against the specific false inference or hidden landmark. |
| [TAQ-011 · Form](../work-items/items/TAQ-011-refine-form.md) | 13 further revisions with distracting or misleading surface features | Inspect the implicated feature against the source. Compare a justified geometry edit, source-backed presentation, or bounded use at the intended zoom. |
| [TAQ-012 · Economy](../work-items/items/TAQ-012-test-mesh-economy.md) | 23 further revisions with economy as the only low axis | Measure the same-scope control and candidate, inspect the vulnerable feature, and retain, reject or qualify the lighter delivery. |
| [TAQ-014 · Tissue-only lymph node](../work-items/items/TAQ-014-lymph-node-tissue-layers.md) | Highest-priority source contradiction remained in the downloadable mesh | Produce a scoped four-tissue derivative, independently check its retained data and render it at the same cameras. |
| [TAQ-013 · Lead review and pruning](../work-items/items/TAQ-013-review-and-prune.md) | Compare the whole set and simplify its working tree | Open the before and after for each revision. Correct unsupported claims, expose useful changes through the ordinary Gallery, and verify recovery and compatibility for removed material. |

Sol-high owns the three refinement batches. The campaign lead owns the rubric, implementation shared by the batches, final review and cleanup. Source limitations and inadequate candidates remain visible. Public cutover has a separate delivery process.

## Final review

The lead reviewer inspected all 46 original/proposed pairs and accepted nine score changes on the original exact exports. Eight readability scores rose from 2 to 3. The vaginal exterior's form score rose from 2 to 3 after matched isolation and a neutral opposite view exposed its contour. Two independently assessed local recommendations now open on newer exports. At the close of this round the maintained register had **34 at target, 44 below target and one partial**. The [next review](teaching-asset-target.md) owns the current decisions. Register totals count the selected file for each family. The local-scene alternatives below remain separately identified.

| Decision | What the review established |
| --- | --- |
| Single lymph node | The original model uses conflicting blood and lymph labels for one network. The [tissue-only edition](../../models/lymph_node/exports/hra-tissue-layers-r01/README.md) excludes that network and both vessel meshes. It retains the exact four tissue meshes, compares the capsule with three named interior regions, and reduces the GLB to 2,984,704 bytes. Four matched source and candidate selections have identical decoded pixels. Local teaching fidelity is 4. Irregular capsule openings and relief keep form at 2. |
| Eye and UFF tooth | The eye plate separates the cornea, iris opening and lens. The UFF plate compares the extracted inner-space proxy against consecutive source slices at its terminal closure. The learner can locate the extraction failure. Its appearance remains a limit on anatomical interpretation. [Ten teaching-risk decisions](../../reviews/teaching-assessments/refinement-risk/accepted.json) |
| Stomach, gallbladder and animated heart | The two digestive Library and Stage views switch between mutually exclusive source and authored groups. The time control on the cardiac edition exposes the left ventricular wall against the fixed aorta. At 41.7% of its authored cycle the sampled wall displacement reaches 5.05 mm. These actions persist through shared links. |
| Thyroid and bronchial fork | The [thyroid r02 edition](../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md) softens the lower rear ridges, retains the bridge coordinates and preserves both lobe silhouettes. Its form score is 3. The bronchial trial left the collar and introduced bright dimples on the daughter branch. The lead reviewer rejected that trial and kept r14 for the first-fork task. [Thirteen form decisions](../../reviews/teaching-assessments/refinement-form/accepted.json) |
| Mesh economy | Twelve local options preserve the reviewed task at its tested zoom. Their combined downloads use 74,930,548 bytes versus 96,836,556 for the matched controls, a reduction of 21,906,008 bytes (22.6%). Ten options are new. Skin and marrow were independently recovered. Ten candidates earned 4 for economy. The static cardiac and breast atlas candidates earned 3 because their finer interior detail lies beyond the checked views. Five further candidates are measurement-only. Six trials failed the visual or protected-seam checks, including the visible surface speckling on the left kidney. [Measurements, protected details and replay](../../reviews/teaching-assessments/refinement-economy/README.md) |

Open **Compare → Teaching asset refinements** in the local Gallery to browse the 46 cases, toggle original and refinement views, and download an accepted candidate. Promoted candidates use the maintained export when its SHA-256 and size match. The [current scorecard](teaching-asset-review/current-coverage.md) follows the maintained register. A low score names a specific defect or cost, and every candidate score belongs to the file that was inspected.

## Source and delivery limits

These are teaching-task judgments and local delivery checks. The two new model defaults apply to local teaching. The published Gallery keeps its prior source and routes. The marrow schematic, mismatched trabecular specimen spacing, unresolved source annotations, excluded eye attachments and open-ended airway casts retain their existing limits. This round left ovary form unassessed. The next review scores the visible finish and keeps specimen interpretation separately bounded. Cross-platform byte reproducibility for historical bronchial r07 remains open; its digest guard fails identically before and after input deduplication on native macOS ARM64. [Replay scope](../../models/bronchial_tree/recipes/authored-junction-repair-r07/README.md)

## Delivery evidence

Tested implementation `8665826ef60a687d69793012a508b5472e2e1a63`. The protected Gallery build produced HTML SHA-256 `3c6bf87b6655aefc907065ba9333c5cc7c44d19669c301c477c5ed7a6ad52bca`. The loopback Compare page serves all 46 controls, both locally recommended editions and twelve recipe-built alternatives. The acceptance bundle is under `.artifacts/teaching-refinements/`.

| Check | Result |
| --- | --- |
| Coverage and repository | 450 offline tests, 26 transport manifests, 394 import references and 25 foundation records passed. Payload integrity verified 1,006 hydrated LFS identities totaling 939,060,618 bytes and 13 package checks. The separate pinned UFF environment passed seven dental tests. |
| Gallery and evidence | 15 packaged tests and three loopback storage tests passed. Chrome walked 105 Library revision or package routes and 25 exact downloads. On the refinement route it verified both images for all 46 cases, 14 candidate downloads, candidate-specific scores, recovery and invalid links. The eleven-system walkthrough, teaching plates, 3D group selection, cardiac scrub, Stage sharing/reload and file failure paths passed. |
| Pruning | [TAQ-013](../work-items/items/TAQ-013-review-and-prune.md#cleanup-and-accounting) records the net tracked size change, separate scratch/install savings, recovery and the r07 native replay limitation. |
