# Review and failure lesson / 复核与教训

- **Failure / 问题:** overlapping capped tubes produced hard main/lobar seams. Distal recipe repeated mid→end segments already represented by lobar tubes. / 封闭管段相交形成硬接缝；distal recipe 重复了 lobar tube 已覆盖的 mid→end 段。
- **Cause / 原因:** each AUTO Bezier continuation altered the duplicate stem tangent; simply unioning all original surfaces created 2 topological handles. / 不同 AUTO Bezier 续接改变重复茎段切线；直接 union 原模型产生 2 个拓扑柄。
- **Fix / 修改:** reconstruct original repair/subdivision-dependent recipe exactly; retain end→dest controls and radii, remove redundant first segments; union only screened contacts with tapered local fairing. / 精确复现依赖原始 repair/subdivision 的 recipe，保留 end→dest 控制点和半径，移除重复首段；仅对筛查后的接触位置合并并局部渐变平滑。
- **Retest / 复测:** exact source reconstruction sampled discrepancy 0; 8 unchanged input meshes, 15 retained control records, 16 terminal witnesses. Euler changed −2 in rejected direct-union experiment to 2 in the repaired candidate. / 原 recipe 重建采样差异为 0；8 个输入网格未变，15 组控制点、16 个末端 witness 保留。被拒绝的直接合并实验 Euler 为 −2，本候选为 2。
- **Negative evidence / 负面证据:** angular bends, simplistic thin routes, closed ends and residual irregularity remain. No clinical branch map, lumen, animation, or browser/runtime pass. / 生硬弯折、过简细枝、封闭末端和局部不规则仍在；未验证临床分支图、管腔、动画及浏览器运行性能。
- **Lesson / 教训:** inspect pixels AND authored graph/topology. A closed manifold alone can still contain unintended handles; smoother shading alone is not better anatomy. / 同时检查实际图像与 authored graph/拓扑。封闭 manifold 仍可能有非预期拓扑柄；着色更平滑不等于解剖更准确。

General reference: OpenStax Anatomy and Physiology §22.1, checked 2026-10-25, https://openstax.org/books/anatomy-and-physiology/pages/22-1-organs-and-structures-of-the-respiratory-system . Supports general branching hierarchy only, not these routes or dimensions. No reference image copied.

Reviewer viewed candidate front and approved proceeding to independent exact-export QA for scoped authored mesh repair only. Final package review remains separate. Before/after images use matched cameras and lights. Topological handle removal is a measured result, not a claim that every handle is visible in the front image.
