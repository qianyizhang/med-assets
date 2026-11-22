# Replay the r01 form review captures

The [ovary](../../ovaries/2026-11-21-form-assessment-r01/README.md) and [esophageal wall](../../esophagus_wall/2026-11-21-form-assessment-r01/README.md) records own the judgments and plates. The [original pilot record](../../../records/work-items/items/AG-GAL-018-reconcile-library-revisions.md#teaching-assessment-pilot) preserves the observations before this follow-up.

Run from the repository root with both exact GLBs hydrated and Blender 5.2.3 LTS Release Candidate `fab76e95306d`.

```sh
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-21-form-followup/render.py \
  -- --root . --output .artifacts/form-review-replay
```

Use a fresh output directory. The script checks both GLB identities and reimports each into a clean scene. The cameras preserve native coordinates. The neutral material, AgX and broad light rig follow the [accepted bronchial diagnostic setup](../../../models/bronchial_tree/recipes/authored-central-fairing-r13/render.py), scaled to each crop. The palette and neutral panels use identical framing and lighting. The alternate camera uses the same target, scale and lights. Assemble plates from the three 960 × 960 frames in the owner receipt, with labels below the images, then encode lossless WebP. Each owner receipt binds the full-resolution raw frames and the assembled plate.
