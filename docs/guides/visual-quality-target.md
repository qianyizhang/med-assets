# Visual and geometric quality target for 3D teaching assets

Use this guide to inspect a CT-derived, atlas-adapted, or authored teaching surface for a named learner task. The [scoring rubric](asset-quality.md) defines the evidence for each score. The [scan-derived surface refinement guide](scan-surface-refinement.md) covers methods for changing a scan-derived mesh.

## Examples of surface form

| Archetype | Appearance | Teaching outcome |
| --- | --- | --- |
| **Cartoon primitive ("toy / egg")** | Ellipsoids, constant-width cylinders, generic spheres (top row of [wave-1/matched-surfaces.webp](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp)). | Loses anatomical silhouette, asymmetry, taper, concavities and attachment cues. |
| **Raw voxel surface** | Visible terraces, flat slice caps and noisy dimples can survive direct extraction from a coarse mask. See the bottom row of the [kidney comparison](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp) and r01 in the [liver dome comparison](../../records/campaigns/ultrasound-refinement/pretrial/matched-dome.webp). | Acquisition artifacts can compete with real anatomy. Dense tessellation can increase payload without a visible benefit. |
| **Interpreted teaching exterior** | A surface shaped from the anatomical reference with continuous broad faces, distinct folds and margins, and restrained shading. See the [adrenal comparison](../../reviews/endocrine-locator/adrenal-study-r05/comparison.jpg). | Preserves placement, proportion and landmarks in the intended view, including grayscale. The review records the interpretation. |

Use a CT segmentation or atlas mesh as an anatomical reference. Change the surface when a comparison shows that the change resolves an artifact or reduces delivery cost while preserving the anatomy the learner needs. Keep the source accessible and record the interpretation.

## Six universal quality criteria

1. **Recognizable silhouette and proportions.** Inspect at least two angles and in grayscale. Preserve the asymmetry, taper, poles, scale and placement that identify the part. Use its anatomical relationships when the learner needs context to distinguish it.
2. **Smooth continuity and honest highlight flow.** Under neutral matte clay with broad light, highlights follow broad faces and turn at anatomical margins, folds and recesses. Investigate slice terraces, faceting and pinch ripples where they compete with those features. Round a flat end-slice cap when the reference supports the change.
3. **Anatomical features and intentional boundaries.** Preserve the shape of true hilums, clefts and fissures, which can be recesses on a closed shell. Preserve the lumen and junctions supported by the reference and required by the task. Open vessel ends, cut edges, wall cavities and disconnected parts should match the intended representation. Localize suspected tunnels, pinholes and islands in the source planes before editing. Record each editorial closure or removal.
4. **Clean topology and purposeful polygon economy.** Check closed parts for watertight, consistently oriented manifold shells. Check intentional cuts and sheets for clean boundary loops. Inspect for degenerate faces and self-intersections. A lighter trial should preserve turning silhouettes and thin margins at the closest teaching view. The ranges below offer starting points after the task, scale and protected features are known. Use the [soft mesh budgets](asset-quality.md#soft-mesh-budgets) for the economy evidence.

| Structure class | Starting range for a trial | Reason to retain more triangles |
| --- | --- | --- |
| Simple sheet, valve leaflet, calculus or short vessel segment | `300 – 1,500` tris | Sharp thin rims or animated deformation |
| Single curved exterior (kidney, gallbladder, spleen, thyroid lobe or adrenal) | `1,500 – 6,000` tris | Deep sulci or clefts, or a close-up cutaway |
| Large lobed exterior or chambered model (liver or heart chambers) | `4,000 – 12,000` tris | Multiple selectable parts or close-up inspection |
| Multi-branch vascular, biliary or airway tree | `5,000 – 20,000` tris | High-order bifurcations visible at teaching zoom |

5. **Restrained shading and finish.** Fix shape before materials. Use smooth area- or angle-weighted normals on organic surfaces, hard edges at intentional cuts, matte-to-satin roughness and enough value separation to distinguish the target in grayscale. Label illustrative colors.
6. **Honest anatomical fidelity.** Check placement, orientation, volume or span, and protected scan-plane geometry at the task's scale. Disclose what the source resolves and where it leaves the interpretation uncertain.

## Quick visual gate (on clean-reimported export)

1. **Neutral clay spin.** Use at least two angles and a close-up to inspect terraces, pinches, pits and highlight travel. For a replacement, inspect the exact previous delivery beside the candidate in matched views. [Comparison procedure](scan-surface-refinement.md#decide-whether-to-ship)
2. **Reference overlay.** Inspect teaching-plane contours with the poles, recesses and margins identified.
3. **In-context lesson view and grayscale.** Perform the named learner action. Check alignment with the probe, scan, overlay and calipers where the lesson uses them.
4. **Topology and budget evidence.** Record the topology checks for the represented anatomy, per-part triangles and export bytes. Use the lighter trial to show where the density matters at teaching zoom.
