# s1233 aorta

The [asset record](asset.record.json) retains the Workshop `metadata-cleanup-r01` GLB and adds a separate `ultrasound-r01` revision on the s1233 CT voxel grid. The ultrasound revision has one source-labeled exterior and two capped views derived from the same field.

| Export | Geometry |
| --- | --- |
| `aorta` | Complete source-labeled aortic exterior, including the arch and both source terminations |
| `aorta-abdomen` | Exterior inside the original abdominal sweep bounds, voxel slices `[140, 271)` |
| `aorta-screening` | Exterior inside the original screening bounds, voxel slices `[117, 237)` |

The first occupied source slice is 147, so each crop adds only an upper cap. Neither cap indicates an anatomical termination. The separate iliac labels and clinical wall, lumen, flow and caliper measurements have their own sources.

## Replay

Use the [study replay environment](../../experiments/ultrasound-sweep/README.md#replay) and Blender 5.2.3 LTS RC (`fab76e95306d`). Set `S1233_CASE` to the public TotalSegmentator case directory. Run from the repository root into a fresh directory.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 models/aorta/rebuild.py --case "$S1233_CASE" \
  --work .artifacts/us-wave2b/aorta/replay-clean \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The recipe checks the compressed mask and its physical grid. A 0.6 mm interpolated field uses a 1.8 mm axial Gaussian kernel along the trunk and a narrower kernel near the distal end and upper thoracic turn. A shared level adjustment preserves volume. Marching cubes extracts the full exterior and the two intersections with the previous cap planes. Blender reduces each surface with quadric collapse. Packing welds coincident float32 points before writing the native voxel-index positions and checks the emitted hashes against the record.

The source is [TotalSegmentator v2.0.1 s1233](https://zenodo.org/records/10047263), by Jakob Wasserthal and contributors at University Hospital Basel. See the [attribution and source terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md). The [Wave 2B packet](../../records/campaigns/ultrasound-refinement/wave-2b/aorta/README.md) records the geometry and local browser evidence.
