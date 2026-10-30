# Ovary + tubal-end context / 卵巢与输卵管末端

Open [teaching.png](teaching.png) for the native overview and two enlarged side
views. Follow **1 — ovary / 卵巢** and **2 — fimbrial end / 伞端**. The numbered
leaders end on visible source-named surfaces and remain readable in grayscale.
All acquired tube and fimbrial surfaces fit inside each detail view; no displayed
tube endpoint is caused by the view crop. Source gaps and cut ends remain intact.

The [GLB](../../models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb)
contains the same ten source meshes and native materials shown here. Source R is
image-left and Source L image-right in the recorded native +Z view. These are
provenance labels, not an independently established patient orientation.

[Original/Updated](original-updated.png) contrasts the retained schematic with this
source-native alternative. They are different models with independent views and
scales, not registered before/after geometry. The original contact image is reused
without resampling. The new overview uses a pixel-exact background-only viewport
crop; all geometry remains inside it with at least 84 pixels of vertical margin.

仅用于观察粗略卵巢外形与来源输卵管末端的相对位置。左右沿用来源命名；不据此推定
患者方位、组织附着或连续管腔。不含卵泡、韧带、系膜或子宫，也不转移旧示意稿动画。

Recompose after the documented render replay (Pillow and Noto Sans CJK required):

```sh
python3 tools/ovary_tubal/compose.py --renders /tmp/ovary-tubal-renders --baseline reviews/ovaries/2026-10-23-v10-exterior-review/draft_ovaries/screenshots/contact.png --output /tmp/ovary-tubal-sheets
```

The composer verifies input hashes, matched RGB pixels, named visible leader
anchors, text bounds, and every source-panel pixel outside the editorial overlay.
It does not rescale or reconstruct anatomy. See [attribution](../../sources/datasets/hra/ovary-tubal-context/ATTRIBUTION.md)
and [review scope](../../reviews/ovaries/2026-10-30-hra-ovary-tubal-r01/README.md).
