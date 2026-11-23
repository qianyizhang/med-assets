# Full-term placenta · teaching economy edition

Distinguish the fetal cord-bearing surface from the lobulated maternal surface of the full-term placenta.

Fetal and maternal surface orientation. Retains the cord, amnion, chorionic and basal plates and placental vessels. Three internal cord vessel meshes remain in the full atlas.

The local GLB contains 155,138 triangles in 4,050,904 bytes. Its SHA-256 is `1c7fbe97548e365c40b886e31a97d3068e611efd79aef543cf49b9d3208ecf4f`.

[Original export](../hra-v1.1-r02/placenta_full_term.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/target-economy/views/placenta-updated.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../../../sources/datasets/hra/placenta-full-term-v1.1/LICENSE.txt).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The recipe checks retained accessor bytes, topology and transforms before comparing clean Blender imports and the exact reviewed GLB identity.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-placenta models/placenta/recipes/teaching-economy-r01.json
```
