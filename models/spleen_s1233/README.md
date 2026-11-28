# s1233 spleen exterior

The adopted r01 survey exterior supports orientation of the convex diaphragmatic face and medial indentation through the frame-12 s1233 sweep. Its positions are on the original 265 × 265 × 401 voxel-index grid, with 1.5 mm spacing and RAS axes. The [AssetKit record](asset.record.json) pins the affine, source and exact packed mesh. The [Wave 2A receipt](../../records/campaigns/ultrasound-refinement/wave-2a/spleen/README.md) covers the review scope.

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1233_CASE` to the public case directory containing `segmentations/spleen.nii.gz`. Run from the repository root into a fresh work directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/spleen_s1233/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave2a/spleen/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe verifies the compressed mask and affine. It resamples onto a 0.6 mm grid, then blends anisotropic 3D signed-distance filters. The broad lateral surface gets stronger smoothing along RAS Z. A narrower kernel protects the tapered ends and the medial recess, especially its oblique shoulder where the saved planes run nearly tangent to the surface. A bounded level-set adjustment restores the native label volume. Blender quadric collapse packs the retained 4,800-triangle surface back into the native grid. Replay checks the exported bytes against the record.

## Source

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. This is an interpretation of the public segmented exterior. The simulated scan uses the same-case CT and masks. The label supports interpreting the medial indentation as an exterior landmark. See the [source release](https://zenodo.org/records/10047263) and the [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
