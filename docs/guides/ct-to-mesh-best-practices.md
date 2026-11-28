# CT-to-mesh refinement best practices

This guide documents proven strategies, tool pipelines, and common pitfalls for turning a **CT segmentation mask** (such as a `1.0–1.5 mm` TotalSegmentator NIfTI mask or anisotropic clinical CT label map) into a clean, organic, low-poly 3D teaching mesh that meets the [visual quality target](visual-quality-target.md) and [four-axis rubric](asset-quality.md).

## Why raw CT masks fail as teaching meshes

Running marching cubes directly on a binary CT label volume treats a discontinuous `0 / 1` voxel step function as a geometric surface. The output almost always exhibits:
- **Axial staircasing / terracing** along curved domes and oblique faces,
- **Flat top and bottom end-slice plateaus** at the first and last occupied slices,
- **Spurious segmentation tunnels, pinholes, or floating islands** from partial-volume noise, and
- **Severe over-tessellation** (`20,000 – 150,000+` tiny uniform triangles) that wastes bytes while still looking blocky.

**Rule of thumb:** Treat the CT mask and grayscale volume as the **anatomical reference** for placement, scale, orientation, and landmarks — then reconstruct, sculpt, and retopologize a smooth surface in physical units rather than trying to nudge raw marching-cubes vertices.

## Recommended 6-stage CT-to-mesh pipeline

### Stage 1 · Audit and clean the label volume before meshing
Inspect the volume in physical coordinates **before** generating any triangles:
1. **Record source metadata:** voxel spacing `(dx, dy, dz)`, anisotropy ratio, `rasMmFromVoxel` affine, grid shape, laterality, and source SHA-256.
2. **Remove floating noise specks:** run connected-component labeling (`scipy.ndimage.label`) and discard isolated single/few-voxel artifacts while keeping genuinely separate anatomical parts.
3. **Fill internal voids for solid organs:** apply `scipy.ndimage.binary_fill_holes` so hollow internal noise pockets do not become hidden interior shells or through-tunnels.
4. **Resample onto a finer isotropic working grid:** for a `1.5 mm` CT mask, working on a `0.5 – 0.75 mm` isotropic grid gives continuous sub-voxel room for smoothing, terminal rounding, and cleft preservation (see the `0.6 mm` working grid in [adrenal-study-r05/gland_field.py](../../assemblies/endocrine-locator/adrenal-study-r05/gland_field.py)). Record both original acquisition spacing and working-grid spacing.

### Stage 2 · Smooth in Signed Distance Field (SDF) space, not raw binary masks
Converting the cleaned binary mask into a continuous **Signed Distance Field** (`EDT(inside) - 0.5` inside, `0.5 - EDT(outside)` outside, multiplied by working-grid step in mm) is the single highest-leverage step for eliminating staircasing without destroying topology:
- **Use anisotropic / spatially adaptive kernels:**
  - Apply a broader Gaussian or curvature-flow filter along the acquisition slice axis (`z`) and across wide smooth domes to wipe out terraces (for example, `[1.45, 1.45, 2.0] mm` on broad faces in `gland_field.py`).
  - **Blend to a narrower kernel near thin ends, sharp poles, rims, and real clefts/hilums** (`[0.45 – 1.0] mm`) so global smoothing never erodes an apex, collapses a thin wall, or bridges a narrow recess.
- **Round flat terminal end-slice caps gently:** where the first or last occupied slice forms an unnatural flat horizontal plate, apply a smooth, bounded taper near the terminal slice while keeping the organ's axial span anchored to the reference.
- **Prevent volume shrinkage with quantile/volume-matched level selection:** Gaussian smoothing on an SDF shrinks convex regions. Instead of extracting blindly at `level = 0.0`, solve for the level set that preserves the source mask's enclosed volume (clamped to a modest bound such as `±0.25–0.5` voxel) so organ size and pole span stay faithful.
- **Multi-label adjacent structures:** when extracting touching organs (for example, liver + gallbladder, or vessel wall + lumen), avoid smoothing each mask in isolation if shared contact matters. Prefer joint multi-label smoothing (3D Slicer joint smoothing or VTK `vtkSurfaceNets3D`) or explicitly verify clearance/contact after smoothing so organs neither pull apart nor interpenetrate.

### Stage 3 · Extract and verify baseline topology
- Extract the zero/volume-matched level set from the smoothed SDF with `skimage.measure.marching_cubes(..., allow_degenerate=False)` (or `vtkSurfaceNets3D` for multi-label volumes).
- Check topology **immediately** before further editing:
  - Single connected component (unless multiple parts are anatomically expected),
  - Consistent outward orientation (positive signed volume),
  - Expected Euler characteristic / genus (`χ = 2`, genus `0` for a closed solid organ with no anatomical through-hole — any genus `> 0` reveals a spurious segmentation tunnel to inspect and close!).

### Stage 4 · Shrinkage-free mesh fairing and targeted sculpting
If minor ripples, fused clefts, or local contour flaws remain after SDF extraction:
- **Prefer Taubin / Windowed Sinc smoothing over Laplacian smoothing:** standard Laplacian smoothing pulls vertices inward and shrinks organs by 5–10%, eroding poles and thin walls. Taubin smoothing (`vtkWindowedSincPolyDataFilter` or alternating positive/negative fairing passes, or Blender's `Smooth Corrective`) damps high-frequency ripple while preserving volume.
- **Never apply 1D/z-only height-field vertex shifts to an existing marching-cubes mesh:** as demonstrated in the [s1233 liver pretrial](../../records/campaigns/ultrasound-refinement/pretrial/README.md), displacing vertices along a single axis over steep terrace flanks flips triangle normals (`42` reversals). Smooth in 3D scalar/SDF space or with full 3D topology-aware fairing instead.
- **Sculpt localized features intentionally in Blender:**
  - Explore targeted fixes interactively via [Blender MCP](../WORKFLOW.md#blender-workflow) (reopening a pinched hilum/cleft, smoothing a persistent step, closing a spurious tunnel, shaping a vessel junction), keeping the raw CT reference visible as a wireframe/overlay.
  - Capture accepted parameters or sculpted masters in a deterministic headless Blender (`blender -b --factory-startup --disable-autoexec`) or Python replay recipe.

### Stage 5 · Retopology and feature-aware polygon reduction
Raw SDF isosurfaces still contain tens of thousands of triangles. **Retopologizing or decimating with new connectivity is expected** to hit `4/4` on Economy and Form:
- **Path A — Feature-aware Quadric Error Metric (QEM) decimation (fast, exact frame preservation):**
  - Use Blender's `Decimate` (Collapse) modifier with vertex-group weights protecting thin rims, clefts, and landmark borders, or the repository's bounded contraction helper ([mesh_contraction.py](../../lib/med_assets/mesh_contraction.py) / [rebuild_mesh.py](../../tools/rebuild_mesh.py)).
  - Preserves sharp silhouettes while collapsing redundant coplanar triangles on broad domes.
- **Path B — Clean quad retopology (best shading & deformation quality on closed organs):**
  - On a watertight, manifold mesh in Blender: `Voxel Remesh` (only if fixing self-intersections/non-manifold junk) → `QuadriFlow Remesh` targeting the structure's budget (`~1,500 – 6,000` faces for a single solid organ) with sharp-edge preservation as needed.
  - Always inspect deep clefts and recesses immediately after `QuadriFlow` — low target face counts can bridge tight crevices. If bridged, raise face count slightly or gently re-project (`Shrinkwrap` with masked crevices) / sculpt open.
- **Normal and shading hygiene:** recompute consistent outward normals, enable smooth shading (angle/area-weighted normals) across organic exteriors, and verify clean-reimported `.glb` / `.mesh` files have zero degenerate triangles, zero non-manifold edges, and zero self-intersections.

### Stage 6 · Validate anatomically (avoiding voxel-clone traps)
Validate the **clean-reimported final export** against the CT reference and the lesson's actual teaching task:
- **Global & scan-plane fidelity:** measure bidirectional surface distances (`p95` and `max`) globally and in the lesson's key cross-sections, plus overall volume change (`%`) and landmark spans (such as pole-to-pole length or cleft depth).
- **Avoid brittle numerical traps:**
  - **No `argmax(axis)` point-displacement gates on blunt/rounded caps:** an unsmoothed binary mask has flat voxel ceilings/floors along constant slice coordinates; smoothing rounds that plateau so the single extreme-coordinate vertex can slide `2–3 mm` tangentially along the cap even when the contours sit within `0.5 mm` (observed in the [Wave 1 kidney trial](../../records/campaigns/ultrasound-refinement/wave-1/README.md)). Gate rounded caps by **cap contour distance + principal-axis / chord length** instead.
  - **Localize 2D section maxima and check without sector clipping:** grazing cuts or sector clip edges can inflate apparent 2D point-to-segment maxima even when the 3D surface is accurate. Always locate the worst sample visually on the section overlay.
  - **Do not demand same-connectivity vertex diffs after retopology:** check orientation, manifoldness, self-intersections, and surface/contour fidelity directly on the exported mesh.
- **Visual & lighter-trial check:** inspect neutral clay and finished lighting from `>=2` angles + close-up + grayscale, and compare a lighter copy to verify turning silhouettes stay within `~1 px` at teaching zoom ([soft mesh budgets](asset-quality.md#soft-mesh-budgets)).

## Common CT-to-mesh caveats and fixes

| Caveat / defect | Root cause | Recommended fix |
| --- | --- | --- |
| **Horizontal staircasing / terraces** | Direct marching cubes on `1.0–1.5 mm` binary mask | Resample to `0.5–0.75 mm` working grid → SDF → anisotropic Gaussian/curvature smoothing → volume-matched extraction. |
| **5–10% organ shrinkage / thinned poles** | Naive Laplacian smoothing or uncompensated Gaussian blur on mask/SDF | Use volume-matched SDF level set + spatially narrower kernels at poles/tips, or Taubin (Windowed Sinc) fairing. |
| **Flat top/bottom end-slice caps** | Abrupt termination of discrete axial slices | Gently round terminal slice plateau in SDF space (or Blender sculpt) while preserving overall axial span. |
| **Spurious through-tunnels (`genus > 0`)** | Noisy segmentation holes bridging a thin region | Run `binary_fill_holes` + check Euler characteristic (`χ = 2` for closed sphere-like organ); close non-anatomical tunnels explicitly and document the edit. |
| **Erased cleft, hilum, or narrow fold** | Single global smoothing kernel or overly coarse `QuadriFlow` | Blend a narrow local SDF kernel around the protected recess (`gland_field.py` pattern), protect vertex groups during decimation, and verify in cut-plane sections. |
| **Collapsed thin wall or pinched vessel lumen** | Unconstrained QEM decimation collapsing opposite faces | Protect wall/lumen vertices with vertex groups or thickness-aware constraints; verify inner/outer separation in cross-section. |
| **Reversed triangle normals** | 1D/z-only vertex shifting over steep steps, or aggressive unconstrained smoothing | Smooth in 3D SDF space or with topology-safe 3D fairing; run automated outward-normal and self-intersection checks before export. |
| **Gaps or overlap between touching organs** | Independent heavy smoothing of adjacent binary masks | Smooth jointly (`vtkSurfaceNets3D` / Slicer joint smoothing) or verify inter-organ clearances in the assembled multi-part scene. |

## Reference implementations and tools in this repository

- **Proven `16/16` CT-to-mesh pipeline:** [adrenal-study-r05/gland_field.py](../../assemblies/endocrine-locator/adrenal-study-r05/gland_field.py) (binary hole-fill → `0.6 mm` SDF → anisotropic body/endpoint/cleft adaptive smoothing → terminal cap rounding → volume-preserving level set → topology assertion) paired with [adrenal-study-r05/build.py](../../assemblies/endocrine-locator/adrenal-study-r05/build.py) (Blender reduction to `1,500` tris per gland + clean-import verification + natural finish).
- **Bounded Blender decimation & landmark protection:** [lib/med_assets/mesh_contraction.py](../../lib/med_assets/mesh_contraction.py) and [tools/rebuild_mesh.py](../../tools/rebuild_mesh.py).
- **Local Blender setup (macOS):** `/Applications/Blender.app/Contents/MacOS/Blender` (`Blender 5.2.3`) + [Blender MCP / headless workflow](../WORKFLOW.md#blender-workflow).
- **External references:** [3D Slicer Segment Editor smoothing](https://slicer.readthedocs.io/en/latest/user_guide/modules/segmenteditor.html#smoothing), VTK `vtkSurfaceNets3D` & `vtkWindowedSincPolyDataFilter` (Taubin windowed sinc fairing), Garland–Heckbert QEM decimation, and Blender `QuadriFlow` / `Decimate` workflows.
