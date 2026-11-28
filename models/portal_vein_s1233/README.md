# s1233 portal and splenic vein exterior

R02 represents the course and visible joins of the combined TotalSegmentator vein label as one source-supported part in the s1233 voxel frame. The package supports 3D orientation. Flow, patency, wall thickness and caliber belong to acquisition and measurement evidence. Named branch labels would need separate anatomical evidence. See the [package record](asset.record.json) and [candidate evidence](../../records/campaigns/ultrasound-refinement/wave-2b/portal-vein/README.md).

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2, Pillow 11.3.0 and Blender 5.2.3 LTS RC (`fab76e95306d`). Point `S1233_CASE` to the public case directory containing `segmentations/portal_vein_and_splenic_vein.nii.gz`. Run from the repository root into a fresh work directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/portal_vein_s1233/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave2b/portal-vein/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe checks the mask digest and native grid, then projects the half-label vertices toward a smoothed distance field sampled every 0.5 mm. The broad kernel uses 1.55 mm along working-grid RAS Z. Local weighting limits the displacement near two junctions, the thin regions and the source saddle near the left posterior endpoint. Half-label connectivity retains the handle from the raw surface. The anatomical nature of the handle is unresolved. R02 strengthens local axial fairing at the upright limb and the shoulders of the observed underside relief. Replay r01 with `--revision r01`. Blender collapses the shaped surface to 6,000 triangles and packs voxel coordinates. Replay verifies the exact export against the package record.

## Source

TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. The original CT and masks supply the simulated sweep images. See the [source release](https://zenodo.org/records/10047263) and [CC BY 4.0 attribution and label terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
