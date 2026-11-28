# s1127 right common carotid

The [native record](asset.record.json) owns two voxel-grid exports made from one TotalSegmentator label. The `carotid` export contains the complete source label for thyroid context. The `neck` export uses the original `[371, 407)` slice bounds for the right carotid acquisition.

The vessel reaches the upper image boundary in the source. The closed ends of the display surfaces mark acquisition or crop limits. The full label ends at voxel z = 408.5. The longer export adds no geometry beyond it. The exterior supports orientation to the artery's course. Wall thickness, plaque, flow, lumen patency and clinical calipers use separate evidence.

## Replay

Use the [study replay environment](../../experiments/ultrasound-sweep/README.md#replay) and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1127_CASE` to the public case directory and run from the repository root.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/carotid_right_s1127/rebuild.py --case "$S1127_CASE" \
  --work .artifacts/us-wave2b/carotid-right/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The rebuild checks the mask SHA-256 and physical affine. The shared [signed-distance recipe](../carotid_s1127/reconstruct.py) samples the label at 0.5 mm and uses stronger smoothing along the axial direction of the trunk. It tapers the filter near both ends and preserves the source volume. The two export scopes share that field. The mesh reducer writes packed voxel coordinates and the replay verifies both recorded output hashes.

Source [TotalSegmentator v2.0.1 s1127](https://zenodo.org/records/10047263), Jakob Wasserthal and contributors at University Hospital Basel, CC BY 4.0. Retain the [label-source notices](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md). The [Wave 2B receipt](../../records/campaigns/ultrasound-refinement/wave-2b/carotid-right/README.md) records measurements and matched playback.
