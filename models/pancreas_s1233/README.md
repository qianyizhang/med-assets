# s1233 pancreas exterior

The survey and standalone pancreas sweep use r02 to locate the head, uncinate region, body and tail in 3D. The filled 3D exterior agrees with the reference within 2.44 mm. Local raw scan-section errors reach 10.18 mm, so exact tracing, calipers and internal anatomy remain unqualified. R01 remains available for comparison. Both exports use the original s1233 voxel grid and RAS affine pinned in the [package record](asset.record.json). [Orientation decision and evidence](../../records/campaigns/ultrasound-refinement/wave-2a/pancreas/orientation-r02/README.md)

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1233_CASE` to the public case directory containing `segmentations/pancreas.nii.gz`. Run from the repository root into a fresh work directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/pancreas_s1233/rebuild.py --revision r02 --case "$S1233_CASE" \
  --work .artifacts/us-wave2a/pancreas/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe verifies the compressed mask and voxel grid. For the closed exterior it fills three enclosed gaps in the native mask totaling 42 voxels. Their biological significance is uncertain at this spacing. It resamples onto a 0.6 mm grid and blends 3D signed-distance filters. The more conservative kernel protects the upper body and tapering tail and the inferior uncinate turn. A bounded level-set adjustment preserves the interpreted exterior volume. Blender quadric collapse packs the resulting 5,800 triangles into the native grid. Replay verifies the exported bytes against the record.

R02 adds two local corrections toward landmarks on the filled exterior. Their center displacements are 0.44 and 1.04 mm, with a smooth falloff over 6 mm. Omit `--revision` to replay the historical r01 recipe.

## Source

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. The frozen case reference includes the gaps, and the original CT masks still supply the simulated scan. See the [source release](https://zenodo.org/records/10047263) and the [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
