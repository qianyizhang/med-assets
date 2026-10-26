# Nasal / sinus airspace specimen — 鼻腔及鼻窦气腔标本展示

**Scoped acceptance: source-preserved display/reference only. Original whole model: Needs revision. Count delta:0.**

**范围：仅接受保留来源形态的展示/参考标本。原始完整模型仍需修改；通过器官数量不变。**

- **Finding / 发现:** The authored baseline reduced complex airspaces to floating beads, teardrops and pyramids. Polishing their surfaces would not recover the missing morphology. 原始示意模型以悬浮珠串、泪滴和棱锥代替复杂气腔；磨光表面不能补回缺失形态。
- **Change / 改动:** A separate licensed NIH3D CT-derived airspace cast gives coherent, asymmetric gross morphology. No anatomy was sculpted, repaired, combined or registered to the schematic. 单独引入有许可的 NIH3D CT 气腔铸型，呈现连续且不对称的大体形态；没有雕刻修补解剖结构，也未与原示意模型拼接或配准。
- **Representation / 表示方式:** The solid object represents AIRSPACE, not mucosa, bone or segmented conchae. It is not a normal/healthy anatomy template. 实体表面代表空气占据的空间，不是黏膜、骨或分割后的鼻甲；不能作为正常健康解剖模板。
- **Known negatives / 已知缺陷:** Creator reports a posterior right-maxillary retention-cyst indentation. Rough segmentation, the inferior cut boundary and 4 independently detected nonadjacent triangle-intersection pairs remain. 作者说明右上颌窦后部存在潴留囊肿形成的压迹；粗糙分割表面、下端截断边界及独立检测出的 4 对非相邻三角形相交均予保留。
- **Not qualified / 不适用:** No validated printing, CFD/simulation, surgical planning, lumen patency, complete drainage-route, animation or clinical pass. 不声称通过打印、流体仿真、手术规划、管腔通畅、完整引流路径、动画或临床验证。
- **Coordinates / 坐标:** Source physical units and anatomical axis convention are undocumented. Display fit is reversible: longest extent1 arbitrary unit. View names ±Y/+X are source-coordinate directions, not anatomical sides. 来源未注明物理单位及解剖坐标约定；可逆显示归一化使最长尺度为 1 任意单位。±Y/+X 仅为源坐标方向，不代表解剖方位。
- **Comparison / 对比:** Different models, each independently framed; not matched physical scale or patient registration. Before/after comparison is source substitution, not repaired baseline geometry. 两个不同模型分别取景，没有物理尺度匹配或患者配准；对比体现来源替换，不表示原模型几何被修复。

## Evidence / 证据
- Native candidate views come from freshly imported exact exported GLB. Lossless WebP pixels equal retained PNG hashes; composite panels are resized and annotated separately.
- 导出后的精确 GLB 经重新导入生成原生视图。无损 WebP 与记录的 PNG 像素相同；拼图另作缩放和说明。
- Independent inverse-transform check:98996 uniquely mapped vertices; oriented triangle topology preserved. Maximum inverse coordinate error1.09569e−5 source units (9.386e−8 of full extent). All4 detected intersection pairs persist.
- 独立逆变换检查：98996 个顶点一一对应，有向三角形拓扑保持；最大逆变换误差为 1.09569e−5 源单位（全尺度的 9.386e−8）。4 对已发现相交均保留。
- Source topology has0 boundary/nonmanifold-edge-count/degenerate triangles under the documented check. This does **not** erase self-intersections or certify anatomy. Source metadata's13 intersections uses an unspecified different method; counts are not equivalent.
- 指定检查下，边界边、非流形边计数及退化三角形均为 0；这**不能**消除自相交，也不构成解剖验证。来源自动报告的 13 次相交使用未明确的方法，与本次计数不可直接等同。
- Reviewer actually inspected4 native source views and fresh exact-export oblique view; comparison reviewed separately. No browser/runtime pass claimed here.

## Lesson / 教训
Prefer transparent source morphology to smooth invented primitives—but preserve representation, pathology, licensing and defect boundaries. Do not convert a useful source display into an unsupported “complete organ passed” claim.
优先采用来源清楚的形态，而不是磨光臆造的基本体；同时保留表示方式、病变、许可及缺陷边界。不能把有用的标本展示升级为“完整器官通过”。

See provenance/attribution under `sources/nose_sinuses/nih3d-airspace-r01/`. Derived model/renders retain CC BY4.0 attribution to nevitdilmen. No separate public license is declared for newly authored scripts/documentation. Third-party references retain their own rights.
