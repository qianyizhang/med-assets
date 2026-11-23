# Small bowel · teaching economy edition

Find the proximal attachment region and point out the folded small-bowel loops without inferring a continuous path.

Use this file for the static proximal-attachment and folded-loop task. Source animation data and protected sparse rows are retained. The three sampled weights do not qualify the full continuous clip.

The local GLB contains 86,616 triangles in 2,140,672 bytes. Its SHA-256 is `b5bb67aae18a3fa305cbf29f7d1464cdfdc9d9d22b8dbb6de6c48efb03f0b190`.

[Original export](../source-candidate-v4/small-intestine.glb) · [Source and review](../source-candidate-v4/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/small-intestine-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-small-intestine models/small-intestine/recipes/teaching-economy-r01.json
```
