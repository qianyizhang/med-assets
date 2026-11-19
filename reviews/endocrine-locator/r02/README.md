# Regional endocrine review · 19 November 2026

The posterior atlas neck now has an independent model with distinct gland
and thyroid materials. An s1233 neck and abdomen provide separate source
references. The [owner](../../../assemblies/endocrine-locator/r02/README.md)
records replay, units, source terms and selection guidance.

Local outputs are in `.artifacts/body-systems-refinement-2026-11-19/endocrine/`.
The input revision is `219eee4d28acf777c283776adcfaa0945e07371a`. The exact
recipe and audit identities, portable and editable file hashes and bytes
are in `geometry.json`. `renders/renders.json` binds the ten PNGs to their
actual GLBs. The original atlas comparison is the r01 locator.

| Export | Meshes | Triangles | GLB SHA-256 |
| --- | ---: | ---: | --- |
| Atlas neck | 5 | 3,112 | `fb3564861cbfef87ec6be216996f74508d08e66e7b5bc2e5bc3690ad168d880f` |
| s1233 neck | 2 | 14,888 | `bba67c00f5d1b323ff0d1c0db0e69c8bc1cda0fd6766091b109766df3d67838c` |
| s1233 abdomen | 5 | 74,444 | `84b8af5ad628ae328a2b32fb366c0e77fe84c33633df75fb01832a689659c32f` |

**Technical.** The atlas neck clean import preserves the original world
triangle triples at 1 μm rounded precision, with two left and two right
targets. Seven masks passed SHA-256, grid and occupied-boundary checks.
The largest vertex displacement was 0.750 mm. Clean imports preserve named
parts, bounds, triangle counts, source identity and materials. A tampered
thyroid mask failed preparation before output creation.

**Visual.** Compare posters `neck-original` and `neck-updated` with the same
orthographic camera and lighting. The revised ochre glands separate from the
rose thyroid in the rear view. The `abdomen-atlas` and `abdomen-s1233` views
use their respective source frames and camera fits. Orange adrenals remain
distinguishable with kidney and pancreas context. The `thyroid-s1233` view
preserves isolated points and visible voxel steps. Labels and live
accessibility remain outside the asset review.

**Anatomical scope.** The s1233 thyroid has two substantial 6-connected
components of 1,113 and 571 voxels and three single-voxel components.
Its superior extent leaves two unused voxel centres before the grid edge.
The labels show local relation to the airway, with 2.12 mm between their
nearest occupied boundary voxel centres. An isthmus, parathyroid placement
and completeness near the superior limit remain unverified. The left and
right adrenal masks are each connected. The nearest ipsilateral kidney
boundary centres are 20.18 mm away on the left and 31.78 mm on the right.
These source distances establish separation only. The atlas and case
surfaces have no common registration. Specialist verification remains open.

**Runtime.** Blender build, import and render passed. Interactive browser
behavior was outside this asset review.
