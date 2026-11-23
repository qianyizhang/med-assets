# Lung pair · HRA · teaching economy edition

Compare the right three-lobe and left two-lobe arrangement in the combined HRA source specimen.

Bilateral lobe orientation. Retains all five lobar groups, all their segments and hila. The separate tracheobronchial selection remains in the full atlas.

The local GLB contains 36,764 triangles in 724,960 bytes. Its SHA-256 is `5c56e323c09547b7d3333f2ff222cb165d322e9cac48aa0200733132129abf78`.

[Original export](../hra-female-normals-r02/lung_female_hra_normals_r02.glb) · [Source and review](../../../../reviews/lung_pair/2026-10-24-bounded-migration/historical-technical-scope.json) · [Matched view](../../../../reviews/teaching-assessments/target-economy/views/lung_pair-updated.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../hra-female-normals-r02/README.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The recipe checks retained accessor bytes, topology and transforms before comparing clean Blender imports and the exact reviewed GLB identity.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-lung_pair models/lung_pair/recipes/teaching-economy-r01.json
```
