# Ovary + tubal-end context / 卵巢与输卵管末端

In the Gallery, open **Reproductive → Asset detail → Female · left pickup** or
**Regional locators → Ovary and tubal end**. Both entrances use the same
[bilingual sequence](lesson.json). Follow each tube from the uterus in the
[anterior pelvic assembly](../body-systems/display/reproductive-female-context-ortho.webp).
Then switch to the enlarged [teaching ovoid r02 views](../../reviews/teaching-assessments/reopen-source/ovary-teaching.webp)
and point to each source-labeled ovary, its adjacent fringe and the gap between
them. The pelvic assembly and close-ups use independent camera framing and
scale. The [r02 package](../../models/ovaries/exports/teaching-ovoid-r02/README.md)
records the interpreted exteriors and unchanged tubal contours.

The [Gallery build](../../sites/anatomy-gallery/README.md#restore-and-build-locally)
checks the exact r02 plate against its [assessment](../../reviews/teaching-assessments/reopen-source/campaign-assessments.json)
before bundling it. The pelvic orientation and HRA comparison retain their
ordinary delivery routes. The bilingual pointing instructions remain available
without their images.

## Compare with source (HRA r01)

Open [teaching.png](teaching.png) for the native overview and two enlarged side
views. Follow **1 — ovary / 卵巢** and **2 — fimbrial end / 伞端**. The numbered
leaders end on visible source-named surfaces and remain readable in grayscale.
The [source GLB](../../models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb)
contains the same ten meshes and native materials. All acquired tube and
fimbrial surfaces fit inside the side views. Source gaps and cut ends remain
intact. Source R is image-left and Source L is image-right in the recorded
native +Z view. These labels describe source provenance. Tissue attachment,
lumen continuity and patient orientation remain unresolved.

本课先用盆腔组合模型定位，再观察 r02 教学模型放大图，最后可对照 HRA r01 原图。
左右沿用来源命名，仅用于观察卵巢与输卵管伞端的大体位置关系。

## Earlier comparison and replay

[Original/Updated](original-updated.png) documents the archived comparison of
the earlier schematic and the HRA r01 source-native alternative. The models
have independent camera framing and scales. The source overview has a
background-only crop with at least 84 pixels of vertical clearance around the
geometry.

Recompose the r01 plate and archived comparison after the documented render
replay using Pillow and Noto Sans CJK.

```sh
python3 models/ovaries/recipes/tubal-context/compose.py --renders /tmp/ovary-tubal-renders --baseline reviews/ovaries/2026-10-23-v10-exterior-review/draft_ovaries/screenshots/contact.png --output /tmp/ovary-tubal-sheets
```

The composer verifies input hashes, matched RGB pixels, named visible leader
anchors, text bounds, and every source-panel pixel outside the editorial overlay.
It does not rescale or reconstruct anatomy. See [attribution](../../sources/datasets/hra/ovary-tubal-context/ATTRIBUTION.md)
and [review scope](../../reviews/ovaries/2026-10-30-hra-ovary-tubal-r01/README.md).
