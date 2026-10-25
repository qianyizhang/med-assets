# Rebuild the scoped repair

Requires Blender 4.3.2 and Python 3. Supply the exact original canonical GLB (Git LFS bytes, not a pointer). Bundled dependencies are hash-guarded; no network or source archive download is performed.

```sh
python tests/bronchial_tree/authored-junction-repair-r07/replay.py \
  --baseline body/anatomy-workshop-r1/meshes/bronchial_tree.glb \
  --output /path/to/rebuild-output
```

Add `--render` for the 4 candidate source-scene diagnostic PNGs. The byte-identical export replay was tested without rendering; rendered source and independent reimport evidence are separately included. Renderer QA is not browser validation.

The baseline camera record preserves original camera/light framing. Original generator is reference-only, not executed by replay; only the isolated recipe stages run. Source JSONs recover original display-subdivided bounds; they do not turn authored bronchial paths into segmented anatomy.

Metric caveat: 0.394760 mm is maximum sampled output-vertex distance to the trimmed-input surfaces, not a symmetric Hausdorff bound to the original model. Sixteen terminal witnesses do not prove a skeleton-derived branch count. Contact screening found no new intersecting node pair, but is not clinical route validation.
