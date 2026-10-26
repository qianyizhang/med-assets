# Dental set checkpoint: overview useful, contacts not ready

**The existing adult atlas is useful for a whole-mouth exterior overview. It is not a contact-accurate dental set.** New crown-facing views show the actual surfaces; a geometry audit confirms crossings between adjacent teeth. Source teeth were not moved, reshaped or repaired.

## What improved

- Corrected upper/lower views now face the crowns, not the exposed root ends shown by the earlier superior camera.
- Shared neutral lighting makes the same assembly easier to compare. Separate teeth-only views reveal shapes without gingiva obscuring them.
- Source names map to 28 FDI slots. Left/right and upper/lower centroid order agree with those labels in the native frame. This is an internal consistency check, not professional anatomy approval.
- 3 unchanged, colour-separated closeups show where neighbouring surfaces meet the independently verified crossing witnesses.

## What fails or remains uncertain

- **Contacts fail:** 22 of 26 within-arch neighbouring pairs have strict mesh-surface crossings, not merely touching bounding boxes. All 22 were corroborated with a second plane/barycentric calculation.
- **4 pairs remain separated:** 14/13 and 23/24 about 0.19 mm; 11/21 about 0.33 mm; 41/31 about 0.34 mm. These are mesh distances, not biological diagnoses or clinical tolerances.
- **Bite remains unvalidated:** this audit covers within-arch neighbours only. The side view shows the source arrangement; it does not establish opposing-arch contact or jaw motion.
- **Fine morphology remains limited:** the renders show broad, smooth crown relief. This is not evidence for fine fissure anatomy, measured tissue thickness or a realistic caries/restoration boundary.
- Exposed roots and omitted bone are context limitations, **not periodontal disease**. Colours in closeups identify teeth, not pathology.
- Coverage is unchanged: 28 adult exteriors; 4 adult exterior slots and all 20 primary exterior slots missing. No new layers or condition variants were created.

## How to read the views

| Files | Meaning |
|---|---|
| `upper-occlusal-context.png` / `lower-occlusal-context.png` | Crown-facing upper/lower arch with shared gingiva; anterior at screen top. These are source-axis views, not a calibrated functional occlusal plane. |
| `upper-occlusal-teeth.png` / `lower-occlusal-teeth.png` | Same crown-facing view, gingiva hidden; no tooth repositioning. |
| `whole-front.png` / `whole-patient-left.png` | Native whole assembly; source-limited external context. |
| `pair-35-36.png`, `pair-12-11.png`, `pair-17-16.png` | Local closeups centred on confirmed crossings. First FDI is blue, second orange. Cropped on purpose for local inspection. |
| `triangle-witnesses.png` | Actual source triangle coordinates around those crossings; red point is a strict crossing witness, not a lesion marker. |

Upper view: patient right is screen left. Lower view: patient right is screen right. These opposite display orientations follow the recorded opposite viewing directions; the source anatomy is not mirrored. Render receipts include camera axes, selected source IDs and source-to-screen object-centre projections.

## Next useful creation step

Keep this atlas as the exterior overview, not the definitive contact/condition baseline. Select a higher-detail, licensed dental baseline with verified tooth identity and suitable neighbouring context before authoring the first baseline/caries/restoration pair. Preserve measured source geometry separately from any later, explicitly reference-authored educational variant.

Do not fix this result by arbitrarily spacing the teeth until crossings disappear. That would alter the source arrangement without evidence for crown form, proximal contacts or occlusion. The first new condition pair also needs a referenced lesion site/extent and professional review; a recoloured tooth or arbitrary drilled hole is insufficient.

## Evidence and replay scope

- Source: existing `models/teeth_gums/exports/r02/teeth_gums.glb`, 814,328 bytes; SHA-256 `82bfaeead46bb51b1fa5bdfdb06c918dfd01aa23b28acae733ab75ec2cd6897f`.
- Native 28 teeth + 2 gingiva surfaces retained; all node transforms were identity. GLB uses metres; geometric calculations explicitly converted to millimetres. Blender import maps GLB `(x,y,z)` to `(x,-z,y)`.
- All 28 tooth meshes are closed and winding-consistent, with no boundary/nonmanifold edges or degenerate triangles in this audit. Teeth 17 and 27 each contain 2 face-connected components. Closure alone does not validate neighbouring contacts or internal tissue semantics.
- 7 primitive tests include crossing, separation and touching-only examples. The 4 positive-gap results match exhaustive enumeration of 6,985,744 triangle pairs. Surface crossings do not quantify penetration depth or overlap volume; fully contained objects are outside this surface-crossing test.
- 6 final neutral renders, 3 coloured closeups and the source-triangle diagram were personally inspected. Earlier overexposed/dim lighting attempts are not included. All supplied PNGs have empty metadata and preserved decoded pixels after sanitization.
- Numeric receipts are included for inspection. This package does not claim a new browser/runtime pass, professional anatomy approval, or a complete redistributable dental atlas. Existing source attribution/licence obligations still apply; the repository's canonical attribution must accompany public derivatives.

Checked 2026-10-26. The exact mesh remains unchanged; this is a validation/presentation checkpoint, not repaired geometry.
