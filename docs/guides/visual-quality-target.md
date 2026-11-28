# Visual and geometric quality target for 3D teaching assets

This guide defines **what a finished 3D teaching mesh should look like** across `med-assets` — whether CT-derived, atlas-adapted, or authored — complementing the byte-stable [scoring rubric](asset-quality.md) and pairing with [scan-derived surface refinement](scan-surface-refinement.md) (the *how*).

## Neither cartoon primitive nor raw voxel lump

| Archetype | Appearance | Teaching outcome |
| --- | --- | --- |
| **Cartoon primitive ("toy / egg")** | Ellipsoids, constant-width cylinders, generic spheres (top row of [wave-1/matched-surfaces.webp](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp)). | Loses anatomical silhouette, asymmetry, taper, concavities and attachment cues. |
| **Raw voxel lump ("staircase potato")** | Unrefined marching cubes on a `1.0–1.5 mm` mask: axial terraces, flat slice caps, noisy dimples, `20k–120k` redundant triangles (bottom row of [wave-1/matched-surfaces.webp](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp); `r01` in [pretrial/matched-dome.webp](../../records/campaigns/ultrasound-refinement/pretrial/matched-dome.webp)). | Voxel artifacts compete with real anatomy and bloat payloads without adding signal. |
| **Interpreted teaching exterior (target · `4/4`)** | Smooth, organic, sculpted surface built **from** the anatomical reference: continuous broad faces, crisp true folds/margins, zero staircasing, closed spurious holes, clean low-poly topology and restrained shading ([adrenal-study-r05/comparison.jpg](../../reviews/endocrine-locator/adrenal-study-r05/comparison.jpg)). | Immediately legible in 3D and grayscale, faithful in placement and proportion, light for web playback, honest about editorial smoothing. |

**Core rule:** A CT segmentation or atlas mesh is an **anatomical reference**, not a pixelated surface to clone vertex-for-vertex. Actively smooth terraces, close needless segmentation holes, clarify real landmarks and cut polygon counts cleanly.

## Six universal quality criteria

1. **Recognizable silhouette and proportions.** Identifiable by silhouette alone in `>=2` angles and in grayscale; preserves real asymmetry, taper, poles, scale and placement without stretching to fake a textbook number.
2. **Smooth continuity and honest highlight flow.** Under neutral matte clay with broad light, highlights glide across broad faces and turn **only** at real anatomical margins, folds or recesses — never along horizontal slice terraces, faceting rings or pinch ripples. Gently round flat end-slice caps.
3. **Purposeful openings vs. spurious defects.** Keep genuine hilums, clefts, fissures, lumens and junctions crisp and open; close meaningless segmentation tunnels, pinholes and floating islands, and record each editorial closure against the source reference.
4. **Clean topology and purposeful polygon economy.** Closed structures must be watertight, outward-oriented manifolds with zero degenerate or self-intersecting faces; open cuts or leaflets need clean intentional boundaries. Changing connectivity via retopology or decimation is expected. Concentrate density on turning silhouettes and thin margins so a lighter copy departs by `≤ ~1 display pixel` at teaching zoom:

| Structure class | Typical target budget | Higher density justified when |
| --- | --- | --- |
| Simple sheet, valve leaflet, calculus or short vessel segment | `300 – 1,500` tris | Sharp thin rims or animated deformation |
| Single curved solid organ (kidney, gallbladder, spleen, thyroid lobe, adrenal) | `1,500 – 6,000` tris | Deep sulci/clefts or close-up interior cutaway |
| Large multi-lobe or hollow chambered organ (liver, heart chambers, pelvis) | `4,000 – 12,000` tris | Multiple named selectable sub-parts or close-up inspection |
| Multi-branch vascular, biliary or airway tree | `5,000 – 20,000` tris | High-order bifurcations visible at teaching zoom |

5. **Restrained shading and finish.** Fix shape before materials. Use smooth area/angle-weighted normals on organic surfaces (hard edges only on intentional cuts), matte-to-satin roughness rather than waxy gloss, and clear target-vs-context value contrast that survives grayscale. Label illustrative colors explicitly.
6. **Honest anatomical fidelity.** Judge fidelity at anatomical and teaching scale — placement, orientation, volume/span and scan-plane landmark geometry — not against raw discrete voxel corners. Disclose source limits clearly.

## Quick visual gate (on clean-reimported export)

1. **Neutral clay spin (`>=2` angles + close-up):** Zero terraces, no pinched normals, no unexplained pits/tunnels, smooth highlight travel.
2. **Reference overlay (2D/3D section):** Refined contour tracks the source across key teaching planes with poles, recesses and margins intact.
3. **In-context lesson view + grayscale:** Target reads immediately against context and aligns with probe, scan, overlay and calipers where applicable.
4. **Topology & budget receipt:** Manifold/normal checks pass, triangles fit the structure class (or justify an exception), and zero intermediate sculpts or scratch renders are committed.
