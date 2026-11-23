# Auricles / pinnae · teaching economy edition

Locate the outer auricular rim and distinguish it from the recessed bowl.

This comparison supports the tested views of the external ear, with no finer landmark or canal claim.

The local GLB contains 54,966 triangles in 1,005,904 bytes. Its SHA-256 is `cb5f38d7d5b8d617df11b53c65ef9d1fe11eb0c3f208d161209bda534917deed`.

[Original export](../r04/ears_z.glb) · [Source and review](../r04/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/ears_z-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../../../sources/datasets/z-anatomy/small-static-studies/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-ears_z models/ears_z/recipes/teaching-economy-r01.json
```
