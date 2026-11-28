# s1233 liver surface

The [AssetKit record](asset.record.json) owns two exterior revisions in the same s1233 265 × 265 × 401 voxel-index grid. The grid has 1.5 mm spacing with RAS axes. Each export pins the case and affine against the [case input record](../../assemblies/workshop-s1233/inputs.json). The [sweep recipe](../../experiments/ultrasound-sweep/abdomen-tracks.json) selects the active surface and samples the source CT and masks separately for its images.

| Revision | Use and design |
| --- | --- |
| r01 | Exact prior sweep surface. Its existing replay and asset identity remain available for the lobe-orientation comparison. |
| r02 | Adopted Wave 2A exterior for identifying the broad right lobe, narrower left extension and inferior cleft at the saved s1233 acquisition. Its neutral clay, source-plane and live playback evidence is in the [Wave 2A receipt](../../records/campaigns/ultrasound-refinement/wave-2a/liver/README.md). |

## Replay

Use Python 3.12, NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0 from the [sweep replay environment](../../experiments/ultrasound-sweep/README.md#replay). Install the repository package in that environment and point `S1233_CASE` at the public case directory containing `segmentations/liver.nii.gz`. Use Blender 5.2.3 LTS RC (`fab76e95306d`) for r02. Run from the repository root and choose fresh outputs.

```sh
python models/liver_s1233/rebuild.py --case "$S1233_CASE" \
  --output .artifacts/liver-s1233-replay/r01.mesh

PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python models/liver_s1233/rebuild.py --case "$S1233_CASE" --revision r02 \
  --blender /Applications/Blender.app/Contents/MacOS/Blender \
  --output .artifacts/liver-s1233-replay/r02.mesh \
  --dense-output .artifacts/liver-s1233-replay/r02-dense.npz

uv run assetkit show anatomy:s1233:liver-window
uv run assetkit impact anatomy:s1233:liver-window@r01:liver
```

The default command checks the original r01 identity. With `S1233_CASE` set, that replay also runs through `uv run assetkit build anatomy:s1233:liver-window r01 --apply`. The r02 command checks the same pinned mask and affine, applies adaptive 3D signed-distance smoothing on a 0.75 mm working grid, then uses Blender's quadric collapse before packing positions back into the original voxel coordinates. The local cleft kernel and narrow channel windows preserve the observed contour. The recipe bridges one thin passage at a recorded source location to produce a single closed shell for exterior orientation. Both recipes verify the exported SHA-256 and byte count before installing a new copy.

## Provenance and limits

Credit Jakob Wasserthal, the TotalSegmentator contributors, and University Hospital Basel for the [TotalSegmentator v2.0.1 dataset](https://zenodo.org/records/10047263). Retain the [dataset and label-source notices](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md). These surfaces are interpretations of the same s1233 exterior label. The narrow channels have uncertain anatomical identity in this mask. The model supports exterior orientation. Hepatic-vein junctions, channel patency and clinical caliper placement require separate evidence.
