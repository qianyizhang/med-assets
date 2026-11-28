# s1127 bilateral thyroid exterior

The paired lobes and their connecting isthmus share one anatomical label and one registered CT-frame surface. R03 preserves both lobes and the bridge for the right and left long-axis orientation exercises. R01 retains the exact original bilateral sweep export and its historical bridge review. The [package record](asset.record.json) pins both revisions and the s1127 voxel grid. See the [Wave 2B evidence](../../records/campaigns/ultrasound-refinement/wave-2b/thyroid/README.md).

## Replay

Use the study’s Python 3.12 environment with the repository package installed, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0. Shaped revisions also use Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1127_CASE` to the case containing `segmentations/thyroid_gland.nii.gz`. Run from the repository root into a fresh output directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/thyroid_s1127/rebuild.py --case "$S1127_CASE" \
  --work .artifacts/us-wave2b/thyroid/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

Pass `--revision r01` to replay the original bilateral sweep mesh directly from the pinned mask through the original sweep extraction. R02 and r03 blend a softened label field with the original half-label at the thin left lobe shoulder and the isthmus. Volume compensation reduces shrinkage on broad faces. R03 softens the left shoulder and bridge where the raw contours permit and applies a small outward field compensation around the grazing shoulder. Blender packs the reduced mesh back into the same voxel grid. The recipe checks the exact packed export digest and byte count.

## Source

TotalSegmentator v2.0.1, case s1127, by Jakob Wasserthal and contributors at University Hospital Basel. See the [source release](https://zenodo.org/records/10047263) and the [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
