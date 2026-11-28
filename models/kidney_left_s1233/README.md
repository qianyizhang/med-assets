# s1233 left kidney exterior

The adopted r01 survey exterior retains the left kidney poles and medial hilar recess at the saved s1233 left flank long-axis acquisition. The packed positions use the original 265 × 265 × 401 voxel-index grid at 1.5 mm spacing in RAS. The [AssetKit record](asset.record.json) pins the affine, source label, and 4,800-triangle export. [Wave 2A receipt](../../records/campaigns/ultrasound-refinement/wave-2a/kidney-left/README.md)

## Rebuild

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0, and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1233_CASE` to the public case directory containing `segmentations/kidney_left.nii.gz`. From the repository root, choose a fresh replay directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/kidney_left_s1233/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave2a/kidney-left/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe verifies the compressed mask and its voxel grid. The label has one connected component and no enclosed voids. The recipe resamples it to a 0.6 mm working grid and filters a signed-distance field. It uses a narrower filter at both poles and the RAS-medial recess. A 0.3 mm field taper rounds the terminal plateaus. A bounded extraction level preserves volume before Blender quadric collapse and packing. The recipe verifies the replay SHA-256 and byte count.

## Source and terms

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. The refinement is a teaching interpretation of the public left kidney label. It supports orientation of the exterior in the simulated scan. Collecting-system detail and renal length require separate acquisition evidence. [Source release](https://zenodo.org/records/10047263) · [CC BY 4.0 notices](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md)
