---
description: Practice locating bladder and cervicovaginal landmarks in the existing Body Systems details.
scope: Anatomy Gallery pelvic part lessons
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-031
work_status: done
work_kind: build
added: 2026-11-23
tags: gallery, pelvis, teaching
depends_on: AG-GAL-027
---

# AG-GAL-031 — Pelvic part lessons

**Owner** · Body Systems. The two existing details used survey plates and sent the learner to separate Library exports. Each detail now opens a question, two unlabelled views and an independently revealed answer. The exact and wider Library views, neighboring detail stops and original survey plates remain available.

| Existing detail | Learner action and reviewed view |
| --- | --- |
| Urinary · Left vesical | Start with the bladder outline and find the base and neck. Hide the dome to see both ureters at the trigone. The [pelvic-base export](../../../models/bladder/exports/pelvic-base-r01/README.md) uses a separate HRA frame from the Workshop plate. The larger posterior-superior crop follows the [reviewed bilateral landmark view](../../../reviews/teaching-assessments/target-risk/views/bladder.webp). The long ureters extend outside the crop. |
| Reproductive · Female context | Orient to anterior bladder and posterior rectum. Isolate the central structures to identify the cervix above the vaginal exterior. The [seven-part r03 selection](../../../models/vagina_hra/exports/teaching-context-r03/README.md) pairs the same-atlas surfaces in a new frame that keeps the [reviewed side perspective](../../../reviews/teaching-assessments/target-form/plates/vagina_hra-comparison.webp). |

Both layers of each lesson keep the same starting camera and scale. The atlas surfaces show exterior relationships and ureteral entry landmarks. Establishing complete lumen continuity, filling, mucosal detail and anatomical variation falls outside the lesson. The geometry and [its shared editable source](../../../assemblies/hra-female-pelvis/README.md) retain their existing assessed identities. The new images are views of those exact GLBs with labels added only to the answers. They credit Kristen Browne and Heidi Schlehlein, [HRA United Female v1.10](https://doi.org/10.48539/HBM637.DWBM.744), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Replay the reference views

From the repository root, use the hydrated exports, the Gallery’s [restored viewer inputs](../../../sites/anatomy-gallery/README.md#restore-and-build-locally), Node 24 or later, a Playwright Core installation and a Chrome executable. The [layer data](../../../sites/anatomy-gallery/app/src/content/gallery/pelvic-lesson-layers.json) owns the shared cameras and exact mesh selections. The [render command](../../../sites/anatomy-gallery/tools/render_pelvic_part_posters.mjs) uses the ordinary Gallery renderer. It checks the source GLBs against their assessment records and writes the rendered images and their digest receipt to a fresh directory.

```sh
node sites/anatomy-gallery/tools/render_pelvic_part_posters.mjs \
  sites/anatomy-gallery/.local/viewer-inputs .artifacts/pelvic-posters-new \
  "$CHROME_EXECUTABLE" "$PLAYWRIGHT_ENTRY"
```

Compare the `pelvic-*.webp` outputs with the [bundled reference images](../../../sites/anatomy-gallery/app/src/content/gallery/part-images/). Replay with Playwright Core 1.62.1, headless Chrome 157.0.8103.80 and Three.js r180 matched all six 840 × 630 WebPs byte for byte in two runs. Visual inspection confirmed the two entry landmarks, the labeled base and neck, and the bladder–cervix–vaginal exterior–rectum relationship. The eight annotation points intersect their intended meshes in the rendered cameras. A missing viewer input and a same-size corrupted GLB each failed before writing output.

## Gallery acceptance

The two original detail addresses are `#/use-cases/systems/urinary?detail=urinary-left-vesical` and `#/use-cases/systems/reproductive?detail=reproductive-female-context`. Verify independent answer disclosure, visibly distinct layers, the same 3D starting frame, blocked-model recovery, and the original plate and Library links through both routes. The static lesson and wider historical atlas are the fallback entry points when the reviewed 3D export is unavailable outside the local preview.

The campaign lead checked both stops before and after in the ordinary Gallery. Each reference layer and labelled answer decoded, and the live camera returned to the same rotated frame after switching tissues. Missing and same-size corrupt GLBs preserved the reference exercise and supported retry. The six-task browser check also exercised the stills without WebGL. [Shared acceptance check](../../../sites/anatomy-gallery/tools/verification/layer-lessons.mjs)
