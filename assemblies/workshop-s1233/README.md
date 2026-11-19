# Same-case digestive and cardiovascular assemblies

These optional body-systems gallery views use the retained TotalSegmentator
v2.0.1 s1233 masks from the original Anatomy Workshop case. They replace the
mixed-frame digestive overview and extend the earlier heart and vessel view
when the local build is available. The existing route schematics remain
available as Asset detail.

## Coverage and blockers

| Assembly | Source-frame improvement | Remaining gap |
| --- | --- | --- |
| Digestive | Esophagus, stomach, duodenum, small bowel, colon, liver, gallbladder and pancreas use the same scan frame. All four consecutive tract label pairs overlap or come within 1.5 mm by nearest boundary-voxel centres. | The colon has components of 122,899, 38,714 and 35 voxels under 6-connectivity. The two largest are separated by 24.602 mm between the nearest occupied voxel centres. The available labels leave the ileocecal junction, mouth, terminal outlet and accessory ducts unverified. A continuous anatomical route needs source evidence for those areas. |
| Cardiovascular | Heart, aorta, both venae cavae and pulmonary venous regions share the scan frame. Each vessel mask overlaps the heart label at its boundary. | The retained label set lacks the pulmonary arterial path and separate chamber and valve interiors. Complete circulation needs those structures in the same frame and coverage of the distal circuits. The overlap with the whole-heart label establishes proximity. |

Both views retain **Partial assembly** status for full-route coverage. Measured
voxel proximity is at the source-mask level and leaves lumen continuity open.
The single **Pulmonary venous mask** mesh contains three disconnected contour
regions. The source mask has four 6-connected regions of 3,953, 2,383, 1,014
and 24 voxels. The 24- and 1,014-voxel regions touch at an edge and merge
under 18-connectivity and in the contour. Region identities carry no individual
vein names. The small-bowel mask likewise has 16 regions by 6-connectivity and
one by 18-connectivity. Its contour is one connected region. These counts
describe the source labels and mesh topology. Lumen continuity remains open.

## Source and build

[Inputs](inputs.json) pins the thirteen locally retained source mask files and
the shared NIfTI affine. Use the s1233 segmentations kept by the Workshop's
[TB3 source integration](../../body/anatomy-workshop-r1/docs/BUILDER-NOTES.md).
The [official archive](https://zenodo.org/records/10047263) provides the public
dataset and the checksum in the input manifest identifies its version. Credit
Jakob Wasserthal, TotalSegmentator contributors and University Hospital Basel.
Retain the Workshop's [CC BY 4.0 dataset and label-source notices](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).

The baseline contours the binary masks at half a voxel.
Four coincident small-bowel triangles were removed before export so the
clean import retains the prepared triangle count. The conversion to Blender
metres is `(-R, 155 - A, S - 430) / 1000` with left, posterior and superior
as positive axes. Surface steps reflect the native 1.5 mm grid. Materials
identify parts in the gallery.

The preparer writes the 6-connected voxel counts in `componentVoxelCounts6`,
sorted largest first. `largestComponentsMinimumVoxelCentreMm` and
`largestComponentsClosestVoxelCentresRasMm` record the distance and the point
pair for the two largest colon regions. `pairProximity` retains its existing
source-mask measurements regardless of the exported surface treatment.

From the repository root, use fresh output directories. The verified mask
environment used Python 3.12 with NumPy 2.2.6, nibabel 5.3.2, SciPy 1.15.3
and scikit-image 0.25.2. Get command-specific approval for headless Blender
on macOS before its first invocation.

```sh
gallery=.artifacts/body-systems-survey-2026-11-19
prepared=.artifacts/s1233-mesh-prep-new
python3.12 assemblies/workshop-s1233/prepare.py \
  --masks "$S1233_MASK_DIR" --output "$prepared"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/workshop-s1233/build.py -- \
  --prepared "$prepared" --output "$gallery/workshop-s1233-r01"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P sites/body-systems-survey/render_gallery.py -- \
  --only digestive-s1233 cardiovascular-s1233
python3.12 sites/body-systems-survey/report.py
node sites/body-systems-survey/verify-browser.mjs --local-only --with-s1233
```

## Smoothed teaching overviews

Use this derivative to make organ outlines and great-vessel surfaces easier to
read. Hide the liver in the digestive route view to inspect the stomach and
duodenum. The separate route schematic explains connections beyond this case's
mask coverage.

The [refinement pass](refinement.py) smooths vertex positions within 0.75 mm,
half of the source voxel width. It keeps triangle connectivity and checks
orientation against the baseline. A distance guard holds adjacent anatomical
surfaces and disconnected contour regions in place wherever their triangles
could intersect within that budget. The outputs preserve the original label
names, matte palette and shared placement. `overviewRefinement` records the
baseline surface component count, protected vertices and displacement per
part. The original contour remains the fidelity reference.

Replay both derivatives into a fresh local bundle.

```sh
round=.artifacts/body-systems-refinement-2026-11-19/same-case
python3.12 assemblies/workshop-s1233/prepare.py \
  --masks "$S1233_MASK_DIR" --output "$round/prepared" --smooth-overview
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/workshop-s1233/build.py -- \
  --prepared "$round/prepared" --output "$round/assemblies"
```

The exporter binds the editable `.blend` and each portable GLB by hash. Its
clean import checks each part's name, material, triangle count, provenance and
prepared bounds within one micrometre. Keep the exported scenes and paired
views in the local gallery bundle. The preparer's NPZ files can be regenerated
from the pinned sources. Source masks and original Workshop exports retain
their existing owners.
