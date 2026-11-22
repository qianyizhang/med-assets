# Shared parotid and salivary teaching exports

The [native region recipe](../../../models/salivary_glands/recipes/native-region/build.py) evaluates the named objects once from the pinned Z-Anatomy `Startup.blend`. Three selections reuse those evaluated surfaces and native transforms. The envelope-only selection keeps the rose material. The two salivary selections keep the original gland, duct, muscle and bone colors.

| Lesson | Reviewed views | Bytes before → after | Triangles |
| --- | --- | ---: | ---: |
| Compare the bilateral parotid envelopes | [Matched anterior and oblique](views/parotid-matched.webp) · [Current lesson](views/parotid-poster.webp) | 63,688 → 53,656 | 3,408 |
| Follow the visible parotid duct course | [Matched isolated views](views/duct-course-matched.webp) · [Current ducts and masseter context](views/duct-course-poster.webp) | 129,736 → 116,896 | 7,144 |
| Locate the glands using the jaw and oral floor | [Matched lateral and superior views](views/jaw-context-matched.webp) · [Current jaw lesson](views/jaw-context-poster.webp) | 763,124 → 654,988 | 38,522 |

Original and updated captures use the same world-space camera, crop, lights and projection within each pair. The superior jaw view selects the mandible and the paired lower glands to expose their position along the arch. The duct lesson uses the context GLB beside the isolated selection to show its course over the masseter. The two lesson views frame different selections.

## What the checks establish

- All three updated GLBs clean-import with their original part selections and appearance. The parotid pair has the exact same decoded world positions and oriented triangles across the three updated GLBs. The eight primary surfaces also match between the two salivary exports.
- The largest world-vertex difference against the preceding exports is 0.00024 mm. The old left exterior had baked winding. Its 852 quadrilateral faces used the other diagonal. The new left exterior uses the source-native local transform and the same 1,704 oriented triangles as both salivary selections. No faces are reversed, duplicated or collapsed. The largest sampled triangle-interior difference across the two left tessellations is 0.373 mm. Bilateral contours, concavity and original shading remain legible in the matched images. The largest measured projected outline shift is below 0.001 pixel in those views.
- Both parotid ducts preserve every world position and oriented face, including the visible tips. The mandible retains every world position and all 18,834 oriented faces, including the empty socket rims. Removing unused UVs reduces the two salivary files and removes 586 UV-split jaw vertices. Blender warns about the native mandible. Validation on a disposable evaluated copy identified four duplicate source triangles. Both lesson exports contain the same 18,834 unique triangles with no collapsed faces.
- One disposable edit moved the right parotid source mesh by 1 mm before evaluating source modifiers. All three fresh exports show that move within 0.00012 mm. Every other part stays in place. A second normal build reproduced all three release SHA-256 values byte for byte, and a wrong atlas member failed before creating any output.
- The pinned left submandibular source centerline intersects the source mylohyoid surface at two sampled points. Both submandibular ducts remain absent from the three lesson selections. The right course remains unaccepted. The historical [negative plate and source scope](../../salivary_glands/2026-10-26-native-scoped-r02/README.md) cover this exclusion. The views establish gross localization and the visible parotid course. Outlet, lumen and complete duct anatomy stay outside the reviewed scope.

## Rebuild and review

Extract only `Z-Anatomy/Startup.blend` from the [pinned source archive](../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json). Run from the repository root. `atlas_member` is the extracted member and `replay` is a fresh scratch directory. Use Blender 4.3.2 for the exact Mac build and clean import. The retained views were rendered in Blender 5.2.3 with CPU Cycles and composed with Pillow 11.3.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python models/salivary_glands/recipes/native-region/build.py \
  -- --source "$atlas_member" --out "$replay/build"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python reviews/teaching-assessments/2026-11-23-salivary-shared-source/review.py \
  -- --source "$atlas_member" --build "$replay/build" --out "$replay/checks"
```

The build emits all three files under their delivery names. Replay the [bound views](render.py) with Blender and `-- --out "$replay/renders"`, then run [the plate compositor](plates.py) with `--renders "$replay/renders" --out "$replay/plates"`.

[Technical receipt](checks.json) · [Exact four-axis assessments](campaign-assessments.json) · [Z-Anatomy source and historical BodyParts3D credits](../../../sources/datasets/z-anatomy/salivary-region/License.txt)
