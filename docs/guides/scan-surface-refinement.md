# Refine a scan-derived teaching surface

Use **scan-derived surface refinement** to turn a CT/MRI segmentation mask or raw extracted surface into a clean, sculpted, low-poly teaching mesh. Treat the scan mask as an **anatomical reference** for placement, proportion, orientation and key landmarks — not a jagged voxel surface to clone pixel-for-pixel. See [Visual and geometric quality target](visual-quality-target.md) for the expected appearance and [Review a teaching asset](asset-quality.md) for scoring.

## Before shaping

Write down the learner's action, closest intended view and the landmarks most likely to disappear (poles, clefts, thin rims, hilums or branches). Keep original volume, segmentation and derived mesh identities distinct; record voxel spacing `(dx, dy, dz)`, units, `rasMmFromVoxel` affine, laterality and source terms. When only a mask or mesh survives, call it the **case reference** and bound claims accordingly. Use external specimens or atlases to understand organic folds and finish, and the case reference to position this individual's anatomy.

## CT-to-mesh refinement pipeline

1. **Clean the label volume and upsample.** Remove floating noise specks (`scipy.ndimage.label`), fill internal noise cavities for solid organs (`binary_fill_holes`), and resample onto a finer isotropic working grid (e.g., `0.5–0.75 mm` for `1.5 mm` CT) so smoothing has continuous sub-voxel room. Record both acquisition and working-grid spacing.
2. **Smooth in Signed Distance Field (SDF) space.** Convert the cleaned mask to a physical-unit SDF (`EDT(inside) − 0.5` inside, `0.5 − EDT(outside)` outside, scaled by grid step). Apply **anisotropic, spatially adaptive smoothing**: smooth broad domes and the acquisition slice axis (`z`) strongly to remove terraces, while blending to a narrower kernel (`~0.45–1.0 mm`) at poles, thin walls and real clefts/hilums. Gently round abrupt top/bottom end-slice plateaus while preserving axial span. Prevent Gaussian shrinkage by solving for a **volume-preserving level set** (clamped to ~`±0.25–0.5` voxel) rather than blindly extracting at `0.0`. For touching organs, use joint multi-label smoothing ([3D Slicer](https://slicer.readthedocs.io/en/latest/user_guide/modules/segmenteditor.html#smoothing) or VTK `vtkSurfaceNets3D`) or verify clearances together.
3. **Extract and verify topology.** Run `marching_cubes(..., allow_degenerate=False)` on the smoothed SDF (or `vtkSurfaceNets3D` on multi-label volumes). Immediately check component count, outward orientation (positive signed volume) and Euler characteristic (`χ = 2`, genus `0` for a closed solid organ — higher genus signals a spurious through-tunnel).
4. **Fair without shrinkage and sculpt purposefully.** For residual ripples, use **Taubin / Windowed Sinc fairing** (`vtkWindowedSincPolyDataFilter` or Blender `Smooth Corrective`) — never naive Laplacian smoothing (5–10% shrinkage) and never 1D/z-only height-field shifts on marching-cubes meshes (flips steep flank normals, as in the [liver pretrial](../../records/campaigns/ultrasound-refinement/pretrial/README.md)). Use [Blender](../WORKFLOW.md#blender-workflow) (interactive MCP to explore, headless recipe to replay) to reopen pinched clefts, close spurious tunnels, or refine organic form against the reference overlay.
5. **Retopologize and reduce polygons.** Raw isosurfaces carry `20k–150k+` redundant triangles; changing connectivity is expected. Choose either **feature-aware QEM decimation** (Blender `Decimate` Collapse with vertex-group masks on thin rims/landmarks, or [mesh_contraction.py](../../lib/med_assets/mesh_contraction.py)) or **clean quad retopology** (watertight `Voxel Remesh` → `QuadriFlow` in Blender, inspecting deep crevices afterward so tight clefts are not bridged). Recompute smooth area/angle-weighted outward normals and budget triangles against [visual-quality-target.md](visual-quality-target.md#six-universal-quality-criteria) and [soft mesh budgets](asset-quality.md#soft-mesh-budgets).

## Common caveats and fixes

| Defect | Root cause | Fix |
| --- | --- | --- |
| Axial staircasing / terraces | Direct marching cubes on `1.0–1.5 mm` binary mask | Upsample to `0.5–0.75 mm` → SDF → anisotropic smoothing → volume-matched extraction. |
| Volume shrinkage / eroded tips | Naive Laplacian or uncompensated Gaussian blur | Volume-matched SDF level set + narrower polar kernels, or Taubin fairing. |
| Flat end-slice ceilings/floors | Abrupt first/last occupied CT slice | Gentle bounded terminal taper in SDF space (or Blender sculpt) preserving span. |
| Spurious through-tunnel (`genus > 0`) | Partial-volume hole through thin region | `binary_fill_holes` + Euler check; close non-anatomical tunnels and document the edit. |
| Erased cleft, hilum or thin wall | Global smoothing or coarse `QuadriFlow`/QEM | Narrow local SDF kernel + vertex-group protection; inspect cut planes before/after. |
| Reversed triangle normals | 1D/z-only vertex push or aggressive unconstrained smoothing | Smooth in 3D SDF space or topology-safe 3D fairing; assert outward normals on export. |
| Touching-organ gaps or overlap | Independent heavy smoothing of adjacent masks | Joint multi-label smoothing (`vtkSurfaceNets3D` / Slicer) and assembled contact check. |

## Decide whether to ship

Clean-import the final export (`.glb` or `.mesh`). Verify part identities, laterality, placement, manifold closure, zero degenerate/self-intersecting faces, outward normals and neighbor contacts.

Compare against the case reference in both directions (global `p95`/`max` and volume `%`) and **check each protected landmark in its own scan plane** — whole-organ averages can hide a shortened cleft, while narrow folds need in-plane contour checks. Avoid brittle voxel-clone traps:
- Do **not** gate rounded/blunt caps on single-vertex `argmax(axis)` displacement (flat binary ceilings cause `2–3 mm` tangential slides even on `0.5 mm`-accurate contours, as seen in the [Wave 1 kidney trial](../../records/campaigns/ultrasound-refinement/wave-1/README.md)); measure **cap contour distance + chord/principal-axis span** instead.
- Localize any worst 2D section error visually and recheck without sector clipping.
- Compare a lighter copy of the same shape at intended zoom to confirm turning silhouettes stay within `~1 px`.

Retain a matched overview, a decisive close-up in neutral clay and finished lighting, and the reference section overlay. Record editorial edits, the feature justifying the polygon budget, and remaining limits, then score with [asset-quality.md](asset-quality.md).

## Proven reference recipes in this repository

- **Adrenal r05 (`16/16` benchmark):** [gland_field.py](../../assemblies/endocrine-locator/adrenal-study-r05/gland_field.py) (`0.6 mm` SDF, adaptive body/endpoint/cleft smoothing, terminal rounding, volume-preserving threshold, topology check) + [build.py](../../assemblies/endocrine-locator/adrenal-study-r05/build.py) (Blender reduction to `1,500` tris/gland — `500` tris moved the oblique shoulder `2.24 px`; cleft error dropped from `6.55 mm` to `1.23 mm`). [Case sections](../../reviews/endocrine-locator/adrenal-study-r05/case-sections.png) · [Scored review](../../reviews/endocrine-locator/adrenal-study-r05/README.md)
- **Bounded Blender decimation:** [mesh_contraction.py](../../lib/med_assets/mesh_contraction.py) and [rebuild_mesh.py](../../tools/rebuild_mesh.py) (Blender `5.2.3` at `/Applications/Blender.app/Contents/MacOS/Blender`).
