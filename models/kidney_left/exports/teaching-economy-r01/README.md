# Left kidney · teaching economy edition

Find the left kidney medial hilum and orient the retained exterior.

Left kidney hilar exterior. Retains capsule, outer cortex and hilum. Internal renal columns, papillae and pyramids remain in the full atlas.

The local GLB contains 30,561 triangles in 560,708 bytes. Its SHA-256 is `e000c2b4408caf1bbbbf2a5649c5e0e3ceaf94b3c2bf794da3a2f30587bb3778`.

[Original export](../hra-female-v1.3-r02/kidney_left.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/target-economy/views/kidney_left-updated.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../../../sources/datasets/hra/kidney-female-left-v1.3/metadata.json).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The recipe checks retained accessor bytes, topology and transforms before comparing clean Blender imports and the exact reviewed GLB identity.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-kidney_left models/kidney_left/recipes/teaching-economy-r01.json
```
