# Skeletal atlas · teaching economy edition

Orient the skull, rib cage and pelvis, then distinguish the appendicular bones from the axial trunk.

Use the exact atlas for individual landmarks beyond the reviewed body views.

The local GLB contains 530,642 triangles in 11,048,256 bytes. Its SHA-256 is `ca10c44878ec836c63882855b9af29193e637773059dbc33b15daff044c2bb3c`.

[Original export](../source-candidate-03/skeleton_source_frame.glb) · [Source and review](../source-candidate-03/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/skeleton-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../source-candidate-03/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-skeleton models/skeleton/recipes/teaching-economy-r01.json
```
