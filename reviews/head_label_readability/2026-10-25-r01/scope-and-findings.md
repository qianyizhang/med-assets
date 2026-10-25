# Representative wholebody 2D readability audit

Actual pixels reviewed: head.svg; regions/head-lateral.svg and head-midline.svg; regions/chest.svg; regions/urinary.svg; current regions/abdomen.svg; regions/uterine.svg; body-locator.svg. Not an exhaustive whole-atlas/browser audit. Source bindings pin current main a6539636cb16857f28d664b91d3a2f2d5e335fa4.

- Head: salivary sublabels 10.5–11px were weak; enlarged only these 3 labels to15px and matched organ-label contrast. Submandibular label placed below lateral neck; group label moved lower. Annotation leaders strengthened, 3 routes adjusted. Organ/context geometry, wording and credits unchanged.
- Chest/urinary: native small crops (350×181,353×271) give tiny text. Leftmost labels near crop edge, but no established clipping, overlap or wrong-organ leader. No speculative edits. Larger display/render helps; not tested as browser interaction.
- Abdomen: current approved stomach callout already improved; untouched.
- Pelvic uterine locator: no blocking label overlap found; untouched.
- Body locator: unlabeled skeletal navigation background inspected, no change. No full navigation or 3D quality pass.

EN and ZH PNGs actually inspected. ZH preview substitutes only preexisting data-zh strings, not rewritten translations or verified browser toggle. Simplified head shape remains unchanged and is not newly approved as anatomically precise. Reviewer approved only visible label-readability improvement; independent review checked label targets and XML preservation. Count delta0.

中文：本次仅检查代表性区域，不是全图或浏览器交互验收。头部3个唾液腺标签加大、调整位置并增强引线；器官形状、文字内容及署名不变。胸部与泌尿区域原始预览偏小，但未证实错标或裁字，不做推测性修改。腹部已修复标签和子宫定位图保持不变。中文预览只使用已有 data-zh。不得据此宣称完整解剖或3D通过。
