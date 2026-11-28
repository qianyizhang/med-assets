# Visual and geometric quality target for 3D teaching assets

This guide defines **what a finished 3D teaching mesh should look like and behave like** across `med-assets` — whether an organ, vessel, cavity, skeletal part, or pathological lesion, and whether viewed in Anatomy Gallery or Ultrasound Anatomy. It complements the [four-axis scoring rubric](asset-quality.md) (which stays byte-stable as the review contract) and pairs with [CT-to-mesh best practices](ct-to-mesh-best-practices.md) (the *how*).

## The target zone: neither primitive nor voxel lump

Medical teaching assets fail visually in two opposite directions:

| Archetype | What it looks like | Why it fails teaching |
| --- | --- | --- |
| **Cartoon primitive ("toy / egg")** | Geometric ellipsoids, constant-width cylinders, identical rounded blobs (for example, the 107 mm ellipsoid in the top row of [wave-1/matched-surfaces.webp](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp)). | Erases the real silhouette, asymmetry, poles, tapers, concavities, and attachment cues that learners must recognize in 3D and in cross-section. |
| **Raw voxel lump ("staircase potato")** | Unrefined marching-cubes output from a 1.0–1.5 mm binary mask: visible axial terraces, ribbed bands, flat top/bottom slice caps, noisy dimples, and 20,000–120,000 redundant triangles (for example, the bottom row of [wave-1/matched-surfaces.webp](../../records/campaigns/ultrasound-refinement/wave-1/matched-surfaces.webp) and `r01` in [pretrial/matched-dome.webp](../../records/campaigns/ultrasound-refinement/pretrial/matched-dome.webp)). | Distracting voxel artifacts compete with real anatomy, look unpolished under interactive light, and bloat runtime payloads without adding anatomical signal. |
| **Interpreted teaching exterior (target · `4/4`)** | Smooth, organic, sculpted surface grounded in its source reference: continuous broad faces, crisp transitions at genuine anatomical folds and margins, zero staircasing, closed spurious holes, clean low-poly topology, and restrained natural shading (for example, the `16/16` regional surfaces in [adrenal-study-r05/comparison.jpg](../../reviews/endocrine-locator/adrenal-study-r05/comparison.jpg)). | Immediately recognizable in 3D and grayscale, faithful to the source's placement and proportions, light enough for smooth web playback, and honest about what is source-derived versus smoothed. |

**Core principle:** A CT segmentation or atlas mesh is an **anatomical reference**, not a pixelated surface to clone vertex-for-vertex. Workers are expected to smooth away acquisition staircasing, close meaningless segmentation holes, clarify genuine landmarks, and reduce polygon counts cleanly to meet all four rubric axes.

## Six universal quality criteria (the "What")

Apply these criteria to any anatomical structure regardless of body region or imaging modality.

### 1. Recognizable anatomical silhouette and proportions
- The target must be identifiable by **silhouette alone** from its primary view and at least one confirming angle (oblique, reverse, or orthogonal), including in **grayscale**.
- Preserve real anatomical asymmetry, taper, pole shape, branching order, and relative scale against neighboring context.
- Keep the source's physical position, orientation, and span intact; never stretch or shrink an organ to fake a textbook measurement.

### 2. Smooth organic continuity and honest highlight flow
- Inspect the clean-imported export under **neutral matte clay** with a broad light before judging materials.
- Highlights should glide continuously across broad curved faces and **turn or break only at real anatomical features** (a lobe margin, hilum, ridge, cleft, valve leaflet, or vessel bifurcation) — never along horizontal CT slice terraces, faceting rings, or pinch ripples.
- Flat end-slice ceilings and floors produced by discrete scan slices should be gently rounded into natural caps while preserving overall organ length.

### 3. Purposeful openings and recesses vs. spurious defects
- **Protect genuine anatomy:** Keep real hilums, clefts, fissures, ducts, ostia, chamber lumens, and vessel bifurcations clearly defined and open.
- **Remove segmentation noise:** Close meaningless through-tunnels, pinholes, jagged micro-cavities, floating noise islands, and zero-thickness bridges that come from partial-volume or mask noise.
- Document every editorial hole closure or smoothed margin against the retained source reference so reviewers know what is measured versus interpreted.

### 4. Clean topology and purposeful polygon economy
- Export a **watertight, consistently oriented manifold shell** (outward normals, zero degenerate triangles, zero self-intersections, zero stray unreferenced vertices) wherever the anatomy is closed. Open cut faces or thin leaflet sheets must have clean, intentional boundary loops.
- Concentrate triangles on **turning silhouettes, thin rims, branches, and recesses**; avoid wasting dense uniform grids on broad smooth domes.
- Changing mesh connectivity (remeshing, quad retopology, feature-aware decimation) is **expected and encouraged** when converting dense marching-cubes outputs into teaching meshes.

| Structure class | Typical target triangle budget | When higher density is justified |
| --- | --- | --- |
| Simple sheet, valve leaflet, calculus, or short vessel segment | `300 – 1,500` tris | Sharp thin rims or animated deformation |
| Single curved solid organ (kidney, gallbladder, spleen, thyroid lobe, adrenal) | `1,500 – 6,000` tris | Deep sulci/clefts or close-up interior cutaway |
| Large multi-lobe organ or hollow chambered structure (liver, heart chambers, pelvis) | `4,000 – 12,000` tris | Multiple named selectable sub-parts or close-up inspection |
| Multi-branch vascular, biliary, or airway tree | `5,000 – 20,000` tris | High-order bifurcations visible at teaching zoom |

Validate the chosen budget visually: at intended teaching zoom, a lighter copy should show **no more than ~1 display pixel** of silhouette departure on turning contours and zero collapse of protected thin features.

### 5. Restrained, readable shading and finish
- **Fix shape before touching materials.** Good shaders never hide bumpy or staircased geometry.
- Use smooth vertex shading (area/angle-weighted normals) on organic surfaces; reserve hard/creased edges for intentional surgical/section cuts.
- Keep teaching materials matte-to-satin with restrained specular highlights so tissue reads as organic rather than waxy plastic.
- Ensure clear value contrast between target, surrounding context, and cut faces in both color and grayscale. Always label illustrative colors and finishes explicitly.

### 6. Honest anatomical fidelity (reference, not pixel clone)
- Judge fidelity at **anatomical and teaching scale**, not against discrete voxel corners:
  - Does the refined surface stay aligned with the CT/source reference in global placement, overall volume/span, and key scan-plane contours?
  - Are the protected landmarks (poles, clefts, hilum, walls, lumens, junctions) accurately positioned in the planes the lesson actually inspects?
  - Are known source limits (e.g., coarse original slice thickness, missing internal sub-structures, cross-subject comparison images) disclosed honestly?
- A polished, low-poly surface that tracks the CT reference cleanly at anatomical scale (`~0.5–1.5 mm` typical surface agreement on `1.5 mm` CT, preserved volume, intact landmarks) beats an unsmoothed `25,000`-triangle staircase clone every time.

## Quick visual review gate (before asking for lead sign-off)

Inspect the **clean-reimported final export** (`.glb` or `.mesh`) with four checks:
1. **Neutral clay spin (2+ angles + close-up):** Zero voxel terraces, no pinched normals, no unexplained pits or tunnels, smooth highlight travel.
2. **Reference overlay (2D/3D section):** Refined contour tracks the CT/source outline cleanly across the key teaching planes without erasing poles, recesses, or thin margins.
3. **In-context lesson view (including grayscale):** Target stands out immediately from context, aligns with probe/scan/overlay/calipers where applicable, and reads cleanly in grayscale.
4. **Budget & topology receipt:** Closed/manifold check passes, triangle/byte counts fall within the structure class budget (or justify an exception against a lighter trial), and zero intermediate sculpts or scratch renders are left in Git.
