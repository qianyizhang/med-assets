# Proximal femur / marrow cutaway · 股骨近端与骨髓剖示

**Accepted scope: authored teaching relationships and bounded geometry checks. Original whole bone-marrow model remains Needs revision; count delta0.**
**接受范围：人工教学结构关系与限定几何检查。原始完整骨髓模型仍需修改；通过器官数量不变。**

## What improved / 改进
- Replaced the detached red oval, protruding sticks and generic half-tube with a recognizable source-derived femoral head/neck/shaft enclosure and contained interior.
- 用可辨认的来源股骨头、颈及骨干外包络与内部结构，替代悬浮红色椭圆、伸出的短棒及通用半管。
- Connected irregular scaffold replaces periodic wirebasket. Cortical shell, exposed cancellous compartment and shaft marrow are spatially coherent.
- 连通的不规则网架替代规则金属网状格栅；皮质外壳、暴露的松质骨区域及骨干骨髓在空间上保持连贯。

## Representation limits / 表示边界
- **Only the exterior derives from BodyParts3D left femur FJ3259.** Cortical inset, trabecular graph, marrow backing and colors are authored—not measured tissue or micro-CT reconstruction.
- **只有外形来自 BodyParts3D 左股骨 FJ3259。** 皮质内偏移、骨小梁网架、骨髓衬体及颜色均为人工示意，不是组织测量或 micro-CT 重建。
- Proximal crop/window and partial front-marrow removal expose the network. Lower backing termination and visible gaps are editorial, not physiological boundaries or air.
- 近端截取、开窗及移除部分前方骨髓用于展示网架。衬体下端及可见间隙是展示处理，不是生理边界或空气。
- Red/yellow transition is illustrative; not a universal adult/age-specific marrow map. No growth plate, trabecular count, density, load trajectory or cortical-thickness truth is claimed.
- 红/黄色渐变仅作示意，不是普遍成人或特定年龄的骨髓分布图。不声称真实生长板、骨小梁数量、密度、受力走向或皮质厚度。
- Tissue meshes intentionally overlap in the teaching display. Contact is not watertight fusion, disjoint tissue segmentation, print/simulation suitability, clinical validation or browser runtime approval.
- 教学显示中的组织网格有意重叠；接触不等于水密融合、互斥组织分割，也不构成打印/仿真适用、临床或浏览器运行验证。

## Actual evidence / 实际证据
- Independent final verifier: all3 components connected; no boundary/nonmanifold edges or zero-area triangles after exact-coordinate welding for checking. Shell nonadjacent BVH candidate/contact screen0; not exhaustive self-intersection certification.
- 独立最终检查：3 个部件均连通；检查时按精确坐标合并后，无边界边、非流形边或零面积三角形。外壳非相邻 BVH 候选/接触筛查为 0；不等于穷尽自相交证明。
- All exported vertices screened against original femur envelope: no confirmed escape beyond1µm. Vertex screening does not prove every triangle interior is contained.
- 所有导出顶点对照来源股骨包络检查，未确认超过 1µm 的越界；顶点检查不证明每个三角形内部均被包含。
- Source-exterior subset:1328 selected triangles unchanged through local inner-offset repair. Network-shell2624 triangle-contact pairs; not142 verified attachments or mechanical integrity.
- 来源外表面子集：局部内偏移修正前后选定的 1328 个三角形不变。网架与外壳有 2624 对三角形接触；不等于验证了 142 个附着点或力学完整性。
- Network simplification: all-vertex nearest-surface maximum77.14µm /51.39µm in opposite directions; not continuous Hausdorff or anatomical error bounds. Final mesh geometry exactly matches the independently reviewed r05.
- 网架简化：两个方向的全顶点至对方表面最大距离为 77.14µm /51.39µm；不是连续 Hausdorff 或解剖误差界限。最终几何与独立审查的 r05 完全一致。
- Actual final renders and bilingual context inspected.4 native WebPs preserve PNG pixels losslessly; before/after panels are separately fitted/resized. No physical registration between baseline and candidate.
- 已实际查看最终渲染与双语说明。4 张原生 WebP 无损保留 PNG 像素；前后对比面板分别取景、缩放，原模型与候选模型没有物理配准。

## Failure lesson / 失败教训
- r01: regular wirebasket and cut-plane shaft sliver—not convincing anatomy presentation.
- r02: better appearance, but split source vertices and offsetting an already-cut shell created37 contacts. Visual plausibility was insufficient.
- r03: exact weld removed topology defects, but23 shell contacts remained. Manifold was insufficient.
- r04: full-shell offset before Boolean cuts reduced contacts to1. Source was checked: remaining defect was authored inner offset, not upstream anatomy.
- r05: bounded local inset correction removed the remaining detected contact without moving the selected source exterior. No larger smoothing or hidden source alteration.
- r01 的规则格栅和骨干薄条不可信；r02 外观改善但出现 37 处外壳接触；r03 拓扑修正后仍有 23 处；r04 调整构造顺序后剩 1 处，确认来自人工内偏移而非来源；r05 限定局部内偏移后检测为 0，未移动选定来源外表面。**外观合理或流形均不能单独证明几何正确。**

Source/license: `sources/bone_marrow/source-cutaway-r05/`. Reproduction: `tests/bone_marrow/source-cutaway-r05/README.md`. Third-party source and reference rights are preserved; no separate public license is declared for newly authored code/documentation/additions.
