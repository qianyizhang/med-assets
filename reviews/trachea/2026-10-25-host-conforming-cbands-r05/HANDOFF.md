# Bounded handoff

1 corrected variant, not an additional organ/study count. Original baseline unchanged. Potential acceptance scope: ring-integration visual defect corrected. Entire anatomy/full asset remains limited, not approved.

## Tested rebuild
From repository root, baseline Git LFS bytes fetched:
```sh
blender -b --disable-autoexec -t 2 --python tests/trachea_cband_polish/rebuild.py -- --baseline body/anatomy-workshop-r1/meshes/trachea.glb --output /tmp/trachea-r05-replay
```
Output must not exist. Add `--render` for4source-scene diagnostic views. Tested Blender4.3.2 byte-identical GLB export; exact cross-version/render reproducibility not promised. Only existing baseline is needed—no rawCT, Z archive, site files or personal paths.

All packed PNG ancillary metadata removed with exact decoded pixel preservation. Independent GLB reimport receipt/images are separate evidence, not substituted for source renders. No publication/merge performed by this handoff.
