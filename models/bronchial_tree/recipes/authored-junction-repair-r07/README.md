# Rebuild the scoped repair

Requires Blender 4.3.2 and Python 3. Supply the exact original canonical GLB (Git LFS bytes, not a pointer). Replay checks the exact local dependencies, including the five lung-lobe JSON files in the [canonical Workshop source directory](../../../../body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy/). No network or source archive download is performed.

```sh
python models/bronchial_tree/recipes/authored-junction-repair-r07/replay.py \
  --baseline body/anatomy-workshop-r1/meshes/bronchial_tree.glb \
  --output /path/to/rebuild-output
```

Add `--render` for the 4 candidate source-scene diagnostic PNGs. The original byte-identical export replay used Blender 4.3.2 without rendering. Rendered source and independent reimport evidence accompany the review and cover Blender output.

The Workshop input consolidation reused the five existing SHA-256 pins. On macOS ARM64, Blender 4.3.2 `32f5fdce0a0a` gave byte-identical results before and after the change from `75c348b9d3fcce0389c4401696569b660cd29dca` for the trimmed GLB, contact screen, final GLB and three receipts. Both runs reached the final identity guard and rejected the same SHA-256 `9094a384cace4277a85fe80352b9a6479ec009d39519c0957d0d8dccad0229ed`. The divergence from the historical export already appears in the trimmed GLB on this platform. The [historical replay receipt](../../../../reviews/bronchial_tree/2026-10-25-authored-junction-repair-r07/replay-receipt.json) records the required export digest. Its companion dependency record describes the original bundled layout. Changing a staged Workshop lobe JSON caused the dependency guard to stop before Blender launched.

The baseline camera record preserves original camera and light framing. The original generator remains a historical reference. Replay executes the isolated recipe stages. The Workshop lobe JSONs recover the original display-subdivided bounds for the authored, illustrative bronchial paths.

Metric caveat: 0.394760 mm is maximum sampled output-vertex distance to the trimmed-input surfaces, not a symmetric Hausdorff bound to the original model. Sixteen terminal witnesses do not prove a skeleton-derived branch count. Contact screening found no new intersecting node pair, but is not clinical route validation.
