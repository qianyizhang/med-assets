# s1233 inferior vena cava exterior

The two r01 exports share one source label and one surface recipe. Use the full `ivc` export for the entire labeled course. Use the `abdominal` export for the historical study locator and its registered exterior companion at `abdomen-survey / ivc-long`. Both retain the original voxel-index frame. The abdominal export ends at the historical superior cut between source slices 270 and 271. This cap is a crop boundary. The label represents the case-specific exterior and includes no separately identified hepatic tributaries or verified junction. Flow, wall thickness, lumen patency and clinical calipers require separate evidence. [Asset record](asset.record.json) · [Measurement and comparison packet](../../records/campaigns/ultrasound-refinement/wave-2b/ivc/README.md)

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1233_CASE` to the source directory containing `segmentations/inferior_vena_cava.nii.gz`. From the repository root run:

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/ivc_s1233/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave2b/ivc/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe verifies the compressed source mask and native grid. It samples its signed-distance field at 0.5 mm, applies axial smoothing of 1.55 mm along the gentler trunk and narrows the filter near the inferior extension, mid-trunk bulge and superior flare. A bounded level shift recenters the volume. A local adjustment of at most 0.84 mm with a 5 mm falloff preserves the shallow shoulder present on native slices 245 and 246. Blender quadric collapse produces 5,798 triangles for the full exterior and 6,000 for the abdominal locator. Replay checks both packed identities.

## Source

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. See the [source release](https://zenodo.org/records/10047263) and [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
