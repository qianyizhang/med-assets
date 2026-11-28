# s1127 bilateral thyroid exterior

The paired lobes and their connecting isthmus share one anatomical label and one registered CT-frame surface. R04 is the active bilateral long-axis teaching surface. The continuous left superior shoulder replaces the ridged r03 form at the same 5,900 triangles. R01 retains the exact original bilateral sweep export and its historical bridge review. The [package record](asset.record.json) pins all four revisions and the s1127 voxel grid. [Matched shoulder comparison and r04 checks](../../records/campaigns/ultrasound-refinement/wave-2b/thyroid/surface-r04/README.md) · [Original Wave 2B evidence](../../records/campaigns/ultrasound-refinement/wave-2b/thyroid/README.md)

## Replay

Use the study’s Python 3.12 environment with the repository package installed, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0. Shaped revisions also use Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1127_CASE` to the case containing `segmentations/thyroid_gland.nii.gz`. Run from the repository root into a fresh output directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/thyroid_s1127/rebuild.py --case "$S1127_CASE" \
  --revision r04 --work .artifacts/us-wave2b/thyroid-fix/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

R04 reconstructs a cubic-interpolated, Gaussian-smoothed label field. A level of 0.47 compensates for smoothing shrinkage. Six broad 4 mm support functions retain the inner and outer grazing contours on the patient’s left shoulder. A separate nearby slice still has a 4.13 mm in-plane deviation at a point only 0.64 mm from the exterior in 3D. Use the model for exterior orientation.

Pass `--revision r01` to replay the original bilateral sweep mesh directly from the pinned mask through the original sweep extraction. R02 and r03 blend a softened label field with the original half-label at the thin left lobe shoulder and the isthmus. Volume compensation reduces shrinkage on broad faces. R03 softens the left shoulder and bridge where the raw contours permit and applies a small outward field compensation around the grazing shoulder. Blender packs the reduced mesh back into the same voxel grid. The recipe checks the exact packed export digest and byte count.

## Source

TotalSegmentator v2.0.1, case s1127, by Jakob Wasserthal and contributors at University Hospital Basel. See the [source release](https://zenodo.org/records/10047263) and the [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
