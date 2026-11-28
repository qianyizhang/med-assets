# s1233 right kidney exterior

The provisional r01 export locates both renal poles and the medial hilar recess in the s1233 long-axis ultrasound teaching exemplar. The same exterior serves the standalone `kidney-right` sweep. Its positions are in the original s1233 265 × 265 × 401 voxel-index grid, with 1.5 mm spacing and RAS axes. The [AssetKit record](asset.record.json) pins the affine, source label and exact 4,800-triangle packed payload.

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). From the repository root, point `S1233_CASE` at the public case directory containing `segmentations/kidney_right.nii.gz`. Choose a fresh replay directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/kidney_right_s1233/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave1b/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe verifies the compressed mask and voxel grid. It retains the largest connected component, fills enclosed voids and resamples the label onto a 0.6 mm grid. An adaptive signed-distance filter protects the ends and medial recess while smoothing broad faces. Additional local fairing softens the inferior outer surface. A small cap taper rounds the terminal plateaus. The extracted level matches the cleaned mask volume, and Blender's quadric collapse reduces the surface before packing it back into voxel coordinates. The recipe rejects an export whose SHA-256 or byte count differs from the record. See the [Wave 1B receipt](../../records/campaigns/ultrasound-refinement/wave-1b/README.md) for measurements, witnesses and review limits.

## Source and terms

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. The geometry is a smoothed interpretation of the public right kidney label. The lesson samples the same-case CT and labels to simulate B-mode and overlay. It represents a separate teaching subject and an exterior contour with a medial recess. See the [source release](https://zenodo.org/records/10047263) and [retained CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
