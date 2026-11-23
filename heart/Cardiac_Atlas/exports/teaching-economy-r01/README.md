# Cardiac Atlas · native & static · teaching economy edition

Distinguish the pulmonary trunk from the aortic arch on the procedural heart’s full static ED exterior.

Use the exact clinical ED variant for chamber-wall or internal-part studies. The existing Workshop opaque exterior has separate source, material and visibility scope.

The local GLB contains 181,922 triangles in 4,248,224 bytes. Its SHA-256 is `342e445b8d460458d322a7e5db875d462867b1e7f99043c711bce73c34c9a813`.

[Original export](../Cardiac_Atlas_Clinical_Full_ED.glb) · [Source and review](../../docs/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/heart-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-cardiac_atlas heart/Cardiac_Atlas/recipes/teaching-economy-r01.json
```
