# Dental, reproductive, skin and urinary starting-file review

The [assessment batch](campaign-assessments.json) covers 20 exact starting files. It names one learner task and one disposition for each. The [work item](../../../records/work-items/items/TAQ-007-review-dental-reproductive-skin-urinary.md) records the focused bladder comparison and the outcome.

Blender 5.2.3 LTS Release Candidate `fab76e95306d` imported each source into a fresh scene. The three-panel JPEGs show palette camera-front, neutral oblique and neutral reverse, in that order. Camera-front refers to the camera setup in the import frame. [Raw view bindings and clean-import mesh counts](renders.json) record the three cameras, frames and visible parts. The [encoded component receipt](mesh-components.json) counts glTF triangle records and vertex-connected components per node after exact POSITION welding. Encoded triangle counts serve economy scoring. Blender loop-triangle totals differ slightly from encoded counts on FDI31, placenta, bladder and left kidney. For example, Blender reports 105,346 for FDI31 and the encoded export contains the owner's 105,370. The cause of each small count difference was outside this inspection.

## Bladder focused plate replay

Use Blender 5.2.3 from the repository root with the exact r03 GLB hydrated and a fresh output directory.

```sh
blender --background --factory-startup --disable-autoexec --threads 5 --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/bladder-view.py \
  -- .artifacts/taq-007-bladder-replay
```

Take the rear and front oblique pairs from the output. In each row place the all-parts capture at left and focused base at right. The retained labeled JPEG uses 500 × 500 Lanczos-resized panels. The [candidate receipt](bladder-view.json) binds the output plate to encoded bytes, raw images, exact GLB, matched cameras and visible selections. The target was regional orientation in a source-preserved illustrative atlas. The comparison does not establish lumen, patency or clinical measurements.

A fresh replay reproduced the camera and selection receipts and all six decoded RGB frames exactly.
