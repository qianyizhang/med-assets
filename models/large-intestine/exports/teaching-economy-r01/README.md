# Large bowel · teaching economy edition

Follow the large bowel exterior around the colon and identify the segmental wall contour and longitudinal taenia cues.

The exported atlas depicts the exterior. This trial does not establish identification of every ribbon at close inspection.

The local GLB contains 218,664 triangles in 4,846,448 bytes. Its SHA-256 is `4ba211f975eb8820d12e6f975051a73691efb69c83806a7d56794f48c00c232a`.

[Original export](../source-candidate-v4/large-intestine.glb) · [Source and review](../source-candidate-v4/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/large-intestine-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-large-intestine models/large-intestine/recipes/teaching-economy-r01.json
```
