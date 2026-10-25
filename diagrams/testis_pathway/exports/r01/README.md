# Testis pathway · original 2D teaching aid / 睾丸输送路径教学示意

EN/中文 each has an outlined display SVG and PNG. Display SVGs contain glyph paths, no external fonts, raster assets, scripts or network dependencies. Editable text versions and generator are in `sources/authored/testis_pathway/r01/`; text editing/rebuild requires Noto Sans CJK SC and Noto Sans. Font files are not bundled. Renderer: Inkscape 1.4 (e7c3feb100, 2024-10-09).

**Purpose:** distinguish internal rete/efferent ductules from the external epididymal head, body, tail and ascending ductus deferens. Original curves and layout, not a copied textbook figure. Static relationship teaching only; not precise anatomy, a 3D repair, or an organ-quality pass.

**用途：** 区分睾丸内部的睾丸网、输出小管与外部附睾头、体、尾及向上走行的输精管。曲线与版式为原创，未复制教材插图。仅用于静态结构关系教学，不代表精确解剖、3D修复或器官质量通过。

The failed 3D model remains needs revision. This supplement adds **0** to passed-organ/3D-study counts. Few lobules/coils and duct counts are symbolic; epididymal duct coiling is omitted. The rejected source-only 3D candidate is not included.

原3D模型仍需修改。本教学补充不增加已通过器官或3D研究计数。小叶、卷曲及管道数量为示意，附睾内部管道卷曲省略；不包含被拒绝的3D来源候选。

## References / 参考
Checked 2026-10-25; no reference image copied.
- NCI SEER, Anatomy of the Testis: https://www.training.seer.cancer.gov/testicular/anatomy/
- NCI SEER, Cross Section of the Testis: https://www.training.seer.cancer.gov/testicular/anatomy/cross-section.html
- OpenStax, Anatomy and Physiology 2e §27.1: https://openstax.org/books/anatomy-and-physiology-2e/pages/27-1-anatomy-and-physiology-of-the-testicular-reproductive-system

No separate public license for the newly authored diagram/code is declared by this package. References are attribution, not endorsement or evidence of clinical validation.

## Re-render
From repository root, with Python3/Pillow and Inkscape1.4 installed:
`python tests/testis_pathway/render.py --output <NEW_NONEXISTENT_DIRECTORY>`

This tests final outlined SVG→PNG decoded-pixel identity. Conversion from editable text to outlines produced tiny antialias differences; those are measured, not described as exact equality. Original editable-render review and final outlined-image bindings remain distinct. No browser visual/interaction pass is claimed.
