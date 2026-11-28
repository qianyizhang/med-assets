# s1127 tracheal air column

Choose the `thyroid` export to locate the air column deep to the thyroid isthmus in the separate s1127 teaching exemplar. The two thyroid sweep routes use this crop. The `carotid` crop shows a shorter context segment in both carotid sweeps. The `trachea` export preserves the full label and its distal bifurcation. All three retain the same original voxel-index frame. Their inferior boundaries come from the source or the named display crop. The exterior represents the labeled air column. The source does not identify wall thickness, cartilage, obstruction or clinical dimensions. [Asset record](asset.record.json) · [Comparison packet](../../records/campaigns/ultrasound-refinement/wave-2b/trachea/README.md)

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1127_CASE` to the public case containing `segmentations/trachea.nii.gz` and run from the repository root.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/trachea_s1127/rebuild.py --case "$S1127_CASE" \
  --work .artifacts/us-wave2b/trachea/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The signed-distance field uses a 0.5 mm sample step and 1.55 mm axial smoothing in the tubular trunk. A narrower filter protects the irregular endpoints and the two distal branches. A bounded level shift preserves the full label volume. Two local corrections below 0.4 mm preserve source-supported shoulders near native slices 344 and 382. The thyroid crop starts at voxel Z 343.5 and the carotid crop at 368.5, the half-voxel boundaries of their former display crops. Blender quadric collapse and reimport checks preserve the full shell and both route-specific crops.

## Source

TotalSegmentator v2.0.1, case s1127, by Jakob Wasserthal and contributors at University Hospital Basel. See the [source release](https://zenodo.org/records/10047263) and [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
