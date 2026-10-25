# Authored bronchial mesh repair · r07

**Whole asset: needs revision.** Scoped correction of visible mesh joins and redundant authored stems only. No anatomical validation, lumen, motion, or browser-performance pass.

- Original 23-node schematic recipe retained as reference; not segmented airway anatomy.
- 8 original input meshes unchanged. 15 distal branches retain their original end→dest Bezier controls and radii; duplicate mid→end stems removed because the lobar tube already owns that stem.
- 0.3 mm voxel consolidation, contact-local tapered fairing; 1 connected closed surface, Euler 2. Terminal witnesses are 16 recipe points, not a skeleton-derived clinical branch count.
- Limitations: angular bends, thin and oversimplified routes, capped ends, residual surface irregularity. High-resolution diagnostic export, not runtime optimized.
- Baseline remains in its original path. This revision does not add an anatomical study or increase coverage counts.

**整体资产仍需修改。** 本次仅修复 authored 示意网格的接缝与重复茎段，不代表解剖验证、管腔、动画或浏览器性能通过。角度生硬、细枝过简、末端封闭和局部表面不规则仍存在。16 个末端 witness 来自原始 recipe，不是临床分支计数。
