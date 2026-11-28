# s1127 left common carotid exterior

Use `neck` for the left common carotid sweep and its registered frame-48 companion in `carotid-normal / left-cca-gray`. That port preserves the earlier native Z crop [371, 407). The `carotid` export preserves the full labeled course from source slices 356–408 and fits the thyroid context's [344, 409) crop. Both are in the original s1127 voxel-index frame. The caps record label or display limits. The exterior supports vessel course and orientation. Plaque, vessel walls, Doppler, patency and clinical measures need separate evidence. [Asset record](asset.record.json) · [Comparison packet](../../records/campaigns/ultrasound-refinement/wave-2b/carotid-left/README.md)

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1127_CASE` to the public source with `segmentations/common_carotid_artery_left.nii.gz`. Launch from the repository root.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/carotid_left_s1127/rebuild.py --case "$S1127_CASE" \
  --work .artifacts/us-wave2b/carotid-left/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The [paired carotid reconstruction](../carotid_s1127/reconstruct.py) resamples a signed-distance field at 0.5 mm. It smooths axially at 1.55 mm on the tubular course and uses a tighter kernel near the endpoints and inferior turn. A bounded level shift preserves the full label volume. The source reaches the last imaged slice. The smoothing field extends the last contour into its padding, then caps exactly at the source boundary. Both display cuts act on that refined field. Quadric reduction produces compact separate exports from both extents. Replay verifies both pinned outputs.

## Source

TotalSegmentator v2.0.1, case s1127, by Jakob Wasserthal and contributors at University Hospital Basel. See the [source release](https://zenodo.org/records/10047263) and [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
