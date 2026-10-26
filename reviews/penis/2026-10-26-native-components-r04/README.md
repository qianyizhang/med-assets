# Penile internal components / 阴茎内部组织关系

**Useful change:** replace the cylinder-and-sphere teaching impression with source-backed curved corporal form, paired proximal sides, ventral spongiosum/bulb, and distal glans relationships. The annotated context identifies proximal/distal and components. This is an internal-component study, not a complete external penis model.

**实用改进：** 从柱体与球体草稿转为有来源依据的内部组织关系：近端两侧形态、腹侧尿道海绵体及球部、远端阴茎头。标注图说明近远端与组织名称。不是完整体表模型。

## Limits / 限制
- Original asset remains **Needs revision**; count delta **0**. No clinical-expert, whole-anatomy, motion or runtime pass.
- 原草稿仍需修改，不新增通过数量；未取得临床专家、完整解剖、动画或运行验收。
- Cavernosa are one connected source mesh, not two separately delineated internal chambers. No internal septum or continuous urethral lumen was added or verified. A dark distal spot is not a proven meatus.
- 阴茎海绵体在源模型中为一个相连网格，不代表两个独立标明的内部腔室。未添加或验证内部中隔、连续尿道腔；远端暗点不能当作已验证尿道外口。
- Source glans retains genuine boundary/nonmanifold edge defects. Tissue overlap is not watertight fusion. Skin, prepuce, tunica, vessels and nerves are not included.
- 保留源阴茎头的边界及非流形边缺陷。组织重叠不等于水密融合；未包括皮肤、包皮、白膜、血管及神经。
- Comparison images show different models/poses, not registered morphometry. Native views are named by source camera direction, not validated anatomical axes. Colors identify parts; they are not measured tissue appearance.
- 对比为不同模型及姿态，未配准，不用于形态测量。原始视图按源相机方向命名，并非已验证解剖轴；颜色仅区分组织，不代表实测组织外观。

## What changed / 修改范围
Only source selection, visibility and teaching materials. Native mesh coordinates, topology and effective object transforms were retained. No hidden repair, missing connector, lumen, smoothing or physical scaling.
仅调整源对象选择、可见性及教学材质。保留原生网格、拓扑及有效对象变换；未暗中修补、补接、造腔、平滑或物理缩放。

## Evidence
- `annotated-context.png`: readable teaching labels, separate from native evidence.
- `review-comparison.png`: old draft versus source study; explicitly unregistered.
- Native lossless WebPs: plus-y, side, oblique, inferior-source. The fifth minus-y view was reviewed but omitted from this lean publication closure; camera record retains it as external working evidence, not a packaged file.
- Independent visual verdict and source-export checks are distinct from anatomy validation. Fresh portable verifier additionally checks the exact pinned original Startup.blend, not an unshipped local inspection file.

## Failure lesson
Initial diagnostics used a stale Blender world matrix: zero location did not mean identity transform because source delta transforms existed. The failed render was rejected. The final build links selected objects, updates the dependency graph, then preserves effective world matrices. Genuine glans defects are unique source triangles, not harmless duplicate faces; no cleanup was falsely claimed.

## Primary references
- NIH SEER: https://www.training.seer.cancer.gov/anatomy/reproductive/male/penis.html
- OpenStax27.1: https://openstax.org/books/anatomy-and-physiology/pages/27-1-anatomy-and-physiology-of-the-male-reproductive-system
Reference text checked; no third-party figure reproduced.

## Rights
Selected Z-Anatomy derivative geometry and source-derived renders: CC BY-SA4.0. Preserve `sources/datasets/z-anatomy/penile-components/License.txt` and attribution: BodyParts3D — Database Center for Life Science — historical CC BY-SA2.1 Japan; Z-Anatomy — libre3D atlas — CC BY-SA4.0; Kousaku Okubo, Gauthier Kervyn, Marcin Zielinski and upstream credited contributors. The source license inventory has no penis-specific exception; this is not an independent per-object provenance audit. No separate public license is declared for newly authored scripts/prose; reference sources retain their own rights.
