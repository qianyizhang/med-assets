# s1233 liver surface

The [governed record](asset.record.json) owns one packed mesh for the 3D scene of the [liver sweep](../../experiments/ultrasound-sweep/abdomen-tracks.json). It uses coordinates in the s1233 source voxel grid. The case, grid shape, and affine into RAS millimetres are pinned in the revision export. The sweep checks them against the [case input record](../../assemblies/workshop-s1233/inputs.json). The 3D mesh is a smoothed surface derived from the liver mask. The sweep samples the original CT and masks for its images.

## Rebuild and verify

Use the [sweep replay environment](../../experiments/ultrasound-sweep/README.md#replay) and its pinned s1233 liver mask. Rebuild to a fresh path from the repository root.

```sh
mkdir -p .artifacts/liver-s1233-replay
python models/liver_s1233/rebuild.py --case "$S1233_CASE" \
  --output .artifacts/liver-s1233-replay/liver.mesh
uv run assetkit show anatomy:s1233:liver-window
uv run assetkit impact anatomy:s1233:liver-window@r01:liver
```

The recipe accepts an exact replay of r01. The SHA-256 matches the preceding liver sweep mesh. To run through AssetKit, set `S1233_CASE` and run `assetkit build anatomy:s1233:liver-window r01 --apply` in an environment containing both the repository package and the pinned replay dependencies. The normal sweep builder requires hydrated bytes for the pinned export.

## Provenance and limits

Credit Jakob Wasserthal, the TotalSegmentator contributors, and University Hospital Basel for the [TotalSegmentator v2.0.1 dataset](https://zenodo.org/records/10047263). Retain the [dataset and label-source notices](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md). Delivery identity and the grid are verified by the pilot. Teaching qualification stays provisional.
