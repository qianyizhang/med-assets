# Urinary outflow · original 2D teaching aid / 尿液排出教学示意

EN/中文 each has an outlined display SVG and PNG. Display SVGs contain glyph paths, no external fonts, images, scripts or network dependencies. Editable text versions and generator are in `sources/authored/urinary_outflow/r01/`; text editing/rebuild requires Noto Sans CJK SC and Noto Sans. Font files are not bundled. Renderer: Inkscape 1.4 (e7c3feb100, 2024-10-09).

**Purpose:** distinguish ureter from urethra; compare separate female urethral/vaginal outlets with the male urethral route through the prostate and penis. Original geometry and layout, not a copied reference figure. Typical simplified relationships only—not a measured section or clinical guidance.

**用途：** 区分输尿管与尿道；对比女性分离的尿道口、阴道口与男性经前列腺及阴茎的尿道路径。曲线与版式为原创，未复制参考图。仅表示典型的简化结构关系，不是测量剖面或临床指导。

- Male short intramural/preprostatic segment is not separately labeled. Sphincters, reproductive ducts and other pelvic structures are omitted.
- 男性短的膀胱壁内段（前列腺前部）未单独标注；省略括约肌、生殖管道和其他盆腔结构。
- Existing 2D locator artwork remains unchanged. This comparison fills an explanatory gap, not a claim that every prior image was poor.
- 原有2D定位图保持不变；本图补充关系讲解，不意味着此前所有图像质量差。
- No 3D asset repair or passed-organ count increase. Existing 3D urethra assets remain needs revision.
- 不代表3D资产修复，不增加已通过器官计数；现有3D尿道资产仍需修改。

## References / 参考
Checked 2026-10-25; no image or source geometry copied.
- NIDDK, The Urinary Tract & How It Works: https://www.niddk.nih.gov/health-information/urologic-diseases/urinary-tract-how-it-works
- OpenStax, Anatomy and Physiology 2e §25.2: https://openstax.org/books/anatomy-and-physiology-2e/pages/25-2-gross-anatomy-of-urine-transport

No separate public license for this newly authored diagram/code is declared by this package. References do not imply endorsement or clinical validation.

## Re-render
With Python3/Pillow and Inkscape1.4:
`python tests/urinary_outflow/render.py --output <NEW_NONEXISTENT_DIRECTORY>`

Final outlined SVG→PNG decoded-pixel identity is tested. Text-to-outline conversion produced small measured antialias differences; no exact equivalence with editable-text render is claimed. Source review and final outlined image bindings are distinct. No browser visual/interaction pass is claimed.
