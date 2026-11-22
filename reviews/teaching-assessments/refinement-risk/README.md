# Teaching-risk refinement

[TAQ-010 work item](../../../records/work-items/items/TAQ-010-refine-teaching-risks.md) · [Decisions by exact export](accepted.json)

This follow-up covers the ten exports below 3 for fidelity or teaching readability at `7b07c7d`. The previous campaign's plates were already visible in parts of the Gallery. The follow-up compares with those openings, then uses task-specific visibility, orientation or labels to make the same exercise clearer.

| Learner view | Exact evidence and scope |
| --- | --- |
| [Lymph node capsule and regions](views/lymph-node-capsule-and-regions.jpg) | Two matched projections expose HRA’s named follicles, paracortex and medulla, carrying the capsule edge into the interior view. The vascular meshes are hidden from both states. The provider’s [version-pinned record](../../../sources/datasets/hra/lymph-node-v1.2/metadata.md) identifies the atlas, and the [University of Leeds histology guide](https://histology.leeds.ac.uk/home/lymphoid/lymphnodes/) illustrates gross compartments. The reference does not adjudicate node 7’s conflicting blood/lymph labels or validate the depicted interfaces. |
| [Anterior eye order](views/eye-anterior-order.jpg) | The labeled pair uses the two exact three-structure selections from the [owner's bounded teaching decision](../../eye_anterior_segment/2026-10-28-teaching-scope-r02/README.md). The [new replay receipt](eye-render-receipt.json) binds the visibility sets, cameras and input. The profile makes the cornea–iris–lens order visible without treating the retained non-smooth rim as anatomy. |
| [UFF computed inner space](views/uff-proxy-terminal-evidence.jpg) | The [owner's exact-export review](../../dental_specimens/uff_tomo1b/2026-10-26-r01/README.md) binds the outer tooth and isolated-space images. Three equally enlarged crops from the [verified terminal overlay](../../dental_specimens/uff_tomo1b/2026-10-26-r01/media-sanitization.json) show the exterior opening and lost proxy selection. The slice sequence is source evidence for the extraction failure, separate from the two GLB views. |
| [Bladder base landmarks](views/bladder-base-landmarks.jpg) | The matched rear oblique views from the [source-context review](../2026-11-22-dental-reproductive-skin-urinary/bladder-view.json) show both atlas entry landmarks in the focus panel. The full context panel points to a visible ureter. Use the [prior angle pair](../2026-11-22-dental-reproductive-skin-urinary/bladder-base-comparison.jpg) for a separate view of the pelvic context and basin. |
| [Gross urethral course](views/urethra-course-in-context.jpg) | Clean import yields exact-file opaque and route-only views. The retained translucent image has verified decoded pixels and the same scale, camera direction and target in the [owner’s receipt](../../urethra_male/2026-10-26-native-context-r01/replay-receipt.json) and [camera bindings](../../urethra_male/2026-10-26-native-context-r01/translucent-view-bindings.json). Compare with the original side view for a second angle. |
| [Breathing dome descent](views/breathing-dome-descent.jpg) | Match frames 1 and 49 in the original assembly. Keep the lung bases and liver visible in context and compare the crest with only the diaphragm visible. The dashed reference comes from the projected expiration contour. The [earlier motion receipt](../2026-11-22-respiratory/motion.json) records the actual bounds in the source frame. |
| [Cardiac wall motion](views/cardiac-wall-motion.jpg) | Same-clip Blender samples bracket the largest sampled wall change. The aorta stays fixed at the compared samples. The outline is the frame-zero ventricular silhouette. The [render receipt](render-receipt.json) and [owner’s clip-validation record](../../../heart/Cardiac_Atlas_Animated/GLB_VALIDATION.json) cover exact-file evaluation. The [focused browser check](../../../sites/anatomy-gallery/tools/verify_refinement_scenes.mjs) covers the local scrubber and Stage reset. |
| [Gallbladder exterior and wall section](views/gallbladder-exterior-and-section.jpg) | The points identify the cut rim and separately named schematic duct in exact source and section renders recorded in [TAQ-005](../2026-11-22-body-cardiovascular-digestive-endocrine/render-receipt.json). The matched views serve as the visual reference for the learner presets. |
| [Stomach exterior and rugae](views/stomach-exterior-and-section.jpg) | The points identify the authored mucosal detail and section edge in the same matched-source replay. All eleven folds belong to the section visibility set. The [section provenance](../2026-11-22-body-cardiovascular-digestive-endocrine/README.md) distinguishes the independent alternatives. |
| [Parathyroid targets and companion](views/parathyroids-targets-and-companion.jpg) | The two panels identify their respective files. The [companion review](../../parathyroids/2026-10-25-localization-r01/README.md) records same-source thyroid context. Clean import matched every gland vertex between the two display frames within 0.0001 mm. The target-only export cannot supply the missing thyroid landmark. |

## Replay the plates

Run from the repository root with hydrated inputs. Use Blender 5.2.3 LTS Release Candidate and Pillow 11.3.0 for this replay. Every command writes a new output directory.

```sh
risk=reviews/teaching-assessments/refinement-risk
digestive=reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine
urinary=reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary
out=.artifacts/taq-010-replay
mkdir "$out"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$risk/render.py" -- "$out/focused"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python models/eye_anterior_segment/recipes/detail_review.py -- --output "$out/eye"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$digestive/render.py" -- "$digestive/render-receipt.json" "$out/digestive"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$urinary/bladder-view.py" -- "$out/bladder"
python3 "$risk/plates.py" --render "$out/focused" --eye "$out/eye" --digestive "$out/digestive" \
  --bladder "$out/bladder" --output "$out/plates"
```

The [render receipt](render-receipt.json) records exact model identities, selection sets and camera settings. The [plate receipt](plate-receipt.json) pins the inspected output files. Platform and encoder differences can change replay bytes. The learner images are small JPEGs derived from identified source render and overlay records. Retain them with their recipes while they are active Library or lesson evidence.
