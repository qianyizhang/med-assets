# Shared Cardiac Atlas teaching review

The current static great-vessel and ventricular-motion lessons are produced from one [editable atlas](../../../heart/Cardiac_Atlas_Animated/Cardiac_Atlas_Animated_Source.blend). The task-specific GLBs are in the [shared export package](../../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/README.md). Reviewers can inspect the original and updated outputs side by side at the same angle, scale, lighting and phase.

| Task | Matched evidence | Original → updated |
| --- | --- | --- |
| Distinguish pulmonary trunk and aortic arch | [Whole atlas, isolated anterior and neutral posterior views](views/great-vessels.webp) | 4,248,224 → 3,501,292 bytes. The four chamber walls recover their full native tessellation, giving 181,922 → 222,336 triangles with all 247 mesh selections preserved. |
| Compare ventricular wall with fixed aorta | [Reference, peak and neutral reverse views](views/wall-motion.webp) | 1,158,724 → 850,364 bytes with the same 30,646 triangles, two meshes and three material primitives. |

The static lesson preserves every vertex of the arch, pulmonary trunk and both pulmonary arteries from the current control. Both focused vessel renders exactly match the control pixels. The restored chamber wall triangulation changes a few small highlights and edges in the whole model. The target ordering remains legible behind the anterior pulmonary tract and from the reverse view in neutral lighting. The trunk and its branches are authored tubes with visible discontinuities at the joins.

The motion lesson's wall and aorta match all evaluated control vertices at 25 samples. The wall moves up to 5.047 mm, while the aorta stays fixed. The matched renders differ by at most one luminance level in the tested 8-bit renders. The two structures form a visual comparison of movement and position. Their apparent contacts do not demonstrate a physical junction.

## Registration and rebuild

The native static and animated imports match on protected vessel and chamber vertex arrays, mesh topology, material regions and placement. The native complete and sectioned LV meshes also share their Basis and shortening keys across both imported assemblies. The two new lesson exports use a single native object for each shared structure. A 1 mm patient-left edit to the aorta in a disposable source copy appears in both exports and leaves every other mesh's tested world vertices in place.

The fresh-import check on the re-exported complete atlas found 247 meshes, 222,336 triangles and 228 original morph channels. Every original channel weight and time sample matches. Eight protected structures, including representative AV and semilunar leaflets, match the original animated GLB within 0.000006 mm across the sampled poses. Minor float differences on the leaflets fall within the 0.002 mm verification tolerance. Both teaching exports reproduced byte for byte in a second build without the full-model output.

The original static scene, full clinical/cutaway and texture studies remain imported alternatives, reference witnesses and replay inputs. The shared teaching path has one editable owner for both lessons. Workshop and specimen-derived geometry retain separate coordinates and provenance. The authored reference joins and motion retain their schematic scope.

## Replay the review

Build with `--full-model` as documented in the [export package](../../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/README.md). Then run these commands from the repository root with Blender 5.2.3 and Python with Pillow 11.3.

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-23-cardiac-shared-source/review.py \
  -- .artifacts/cardiac-replay .artifacts/cardiac-review
python3.12 reviews/teaching-assessments/2026-11-23-cardiac-shared-source/plates.py \
  .artifacts/cardiac-review .artifacts/cardiac-plates
```

The [technical receipt](checks.json) binds exact imports, original and updated exports, clean reimports, the disposable edit and matched renders. The [plate receipt](views/plates.json) binds the derived matched plates and browser posters. The [campaign assessments](campaign-assessments.json) score each exact teaching export. The source checkout before these local changes was `41b7186a9e7a90ef3fcdba723cdf6457585aaf5b`. The original exports and maintained source carry the historical provenance. The generated full-atlas QA GLB, disposable copy, raw renders and build logs remain scratch outputs.
