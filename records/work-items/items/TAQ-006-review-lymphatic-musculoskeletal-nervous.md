---
description: Review the maintained lymphatic, musculoskeletal and nervous teaching files.
scope: teaching assets
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: TAQ-006
work_status: done
work_kind: build
added: 2026-11-22
tags: gallery, evidence
depends_on: TAQ-001
---

# TAQ-006 — Review Lymphatic & tissue, Musculoskeletal, and Nervous & senses

[Teaching asset review campaign](../../campaigns/teaching-asset-review.md)

The [assessment record](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) covers the exact starting files for 5 Lymphatic & tissue, 12 Musculoskeletal and 8 Nervous & senses families. Each has a named learner action, four rubric scores, the source scope and a keep or follow-up decision. The [render receipt](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/render-evidence.json) binds the whole-model pairs, targeted neutral details and part counts to each exact file, pose and visibility selection.

## Teaching presentation

- **Single lymph node.** The [matched layer plate](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/views/A03-lymph-node-layers.webp) shows the intact capsule and three named tissue meshes at the same camera and scale. Leader labels identify the exposed surfaces and the caption lists the four hidden meshes. The original HRA network has conflicting blood/lymph labels, which keeps it outside this learner task. The visibility change and illustrative colors support orientation to the named layers. Flow, connected lumen and tissue contacts remain outside scope.
- **Collecting routes and peripheral nerves.** Bare whole views lose the thin paths at teaching scale. The assessed presentation for [collecting routes](../../../models/lymph-collecting-routes/source-context-r01/comparison-en.png), [median nerve](../../../reviews/peripheral_nerves/2026-10-30-median-wrist-r01/v2/teaching.png) and [ulnar nerve](../../../reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/evidence/teaching.png) uses the retained highlighted and labeled whole and detail plates. The figures distinguish source ends, editorial colors and context landmarks.
- **Knee.** The [matched neutral comparison](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/views/A10-knee-depth.webp) confirms that four visibility toggles expose the menisci and central ligament region hidden in the exterior state. The [existing knee inspection](../../../reviews/joints/knee-inspection-r01/README.md) remains the interaction for this task.
- **Right rotator cuff.** The [neutral posterior detail](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/views/A14-review.webp) resolves the thin scapular spine and narrow teres-minor strip. The paired source geometry and seven retained label-ray checks support the same learner task.
- **Anterior eye.** Use the cornea–pupil–lens visibility scope in the [owning review](../../../reviews/eye_anterior_segment/2026-10-28-teaching-scope-r02/README.md). The neutral alternate view of the exact seven-mesh export makes the diagnostic ciliary/zonular fringe conspicuous. Preserve its earlier rejection for attachment teaching.
- **Bone context.** The proximal femur container and the independently acquired trabecular comparator keep separate displays and scales. The [retained comparison record](../../../assemblies/marrow-comparison/2026-10-23/README.md) documents an unresolved specimen-spacing discrepancy. A quantitative comparison requires resolving it.
- **Mesh economy.** The 364,734-triangle trabecular representation takes almost all of the authored marrow cutaway's mesh cost. The [subsequent lighter-mesh trial](TAQ-009-test-marrow-lattice-economy.md) tested the protected struts and junctions and retained the strong candidate for the reviewed local teaching views.

## Verification

Inputs match the maintained starting files at campaign coverage commit `e0eae25c3914c27cfd81fb72436e443b023bf487`. Blender 5.2.3 `fab76e95306d` clean-imported all 25. The coverage report confirmed 25 full profiles with each view matching its recorded hash. Four scores describe the available evidence and include low scores for defects and incomplete checks. Retain the plates and receipt while the assessed files and their campaign ratings remain in use.

The replay reproduced identical decoded pixels for 64 render views and identical file bytes for all 27 WebP plates. The deliberately wrong GLB digest failed before rendering. The repository offline gate passed 447 tests, 26 transport manifests, 25 foundation records, 394 import references and 882 LFS pointer identities.

From the repository root, choose fresh output paths. Provide the exact hydrated models, Blender 5.2.3 and Python with Pillow. The batch reads each export's identity from the committed receipt and rejects changed bytes.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/render.py -- \
  reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/render-evidence.json \
  .artifacts/taq-006-replay
python3 reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/plates.py \
  .artifacts/taq-006-replay .artifacts/taq-006-replay-plates
python3.12 records/campaigns/teaching-asset-review/coverage.py
```

The assessments cover named static tasks in the exact assets. Specialist approval, animation, runtime performance and hosted delivery remain outside this verification.
