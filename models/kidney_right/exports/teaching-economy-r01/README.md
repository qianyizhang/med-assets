# Right kidney · teaching economy edition

Find the right kidney medial hilum and distinguish it from the smooth convex exterior.

Right kidney hilar exterior. Retains capsule, outer cortex and hilum. Internal renal columns, papillae and pyramids remain in the full atlas.

The local GLB contains 28,682 triangles in 526,464 bytes. Its SHA-256 is `fdddbde55104ab9af2b5ebafea7e52692dad7f94aad85d93a2237cbdd371e3eb`.

[Original export](../hra-female-v1.3-r02/kidney_right.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/target-economy/views/kidney_right-updated.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../../../sources/datasets/hra/kidney-female-right-v1.3/metadata.json).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The recipe checks retained accessor bytes, topology and transforms before comparing clean Blender imports and the exact reviewed GLB identity.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-kidney_right models/kidney_right/recipes/teaching-economy-r01.json
```
