# UFF Tomo1B — DRAFT research-display candidate

Owner-requested repository and Site browser review. **Not an approved dental teaching asset.**

## What you can review

A scan-derived tooth surface and a separately selectable illustration of the space selected inside it. Review whether the outer shape is useful and where the internal-space extraction stops making anatomical sense. **The internal proxy is not a finished root-canal model.**

[Open the browser review](https://anatomy-dental-review.landy123007.chatgpt.site/) to compare the original extraction with the lighter display model and inspect the source overlays. The two named meshes remain separate; this is not a replacement for the mouth model or a complete set of teeth.

## Critical source limitation

All 559,390 selected space-proxy voxels connect to exterior in 3D. Per-slice filling stops at an open channel; the mesh then imposes an algorithmic closing surface. It is **not** an anatomical apex or sealed lumen. This method fails complete canal reconstruction. Do not diagnose visible lines as cracks or claim a healthy/intact tooth.

## What is verified, and what still needs work

- The published surface matches the reviewed output, and the extraction can be repeated from the pinned source scan.
- The browser page, static images and exact file downloads were checked. The cloud browser could not initialize WebGL, so interactive rendering and performance are **not verified**.
- Tooth number, side, health and anatomical orientation are unknown. Enamel, dentin and cementum are not separated. Expert tissue labeling and a complete canal reconstruction remain open work.

<details>
<summary>Technical identity and measurements</summary>

- One GLB, 2 independently named boundary meshes; 20,434,544 bytes.
- SHA-256: `46694985ff0162a4220d959528847446ffe48b3be41e481f5890429500e2d3b3`.
- Unnumbered pre-treatment source specimen. Exact FDI, laterality, health and anatomical orientation are unknown.
- `hard_tissue_boundary`: threshold-positive mineralized bulk; not separately segmented enamel, dentin or cementum.
- `slice_enclosed_space_proxy`: method illustration, not pulp tissue or complete canal anatomy.
- Units: metres. X/Y/Z = source column/row/slice; not registered to the existing mouth assets.

### Display measurements

|Component|Faces before → after|Face islands retained|Conservative master-relative bound|
|---|---:|---:|---:|
|Hard boundary|2,026,564 → 1,013,896|62|0.009731 mm|
|Space proxy|242,580 → 121,290|1|0.004889 mm|

Bounds include 0.00001 mm numerical allowance. Source grid: 0.020002117 mm. Near-zero sampled errors reflect coplanar surface reduction, not anatomical precision.

- Actual final GLB: positive orientation, exact master bounds, 0 degenerate triangles.
- Independent review: 5 actual render views, 48,000 distance samples, 28/28 naive cross-checks.
- Builder supplied per-island/full-bound evidence; independent review sampled geometry, not every certificate.
- Threshold 75–85 changes derived space volume by 6.34%. No expert segmentation approval.


</details>

## Evidence and replay

- [Source and method](../../../../../sources/datasets/uff-ds-uct-002/README.md)
- [Dated review](../../../../../reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/README.md)
- [Attribution and changes](ATTRIBUTION.md)

Raw source ZIP, ROI, high-poly master and rejected candidates are external replay inputs/outputs, not repository payloads. No clinical, complete-canal, tissue-interface or simulation approval follows from publishing this DRAFT review candidate.
