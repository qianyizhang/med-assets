# Pharynx / larynx · teaching economy edition

Find the epiglottis, thyroid cartilage and cricoid within the dissected pharyngeal exterior.

This comparison covers cartilage location. The lighter muscles have not been qualified for close fiber study.

The local GLB contains 211,184 triangles in 3,834,688 bytes. Its SHA-256 is `6145abfa541670441bdc7b61978121dc4f5d2730731b873a76b9fff1428d7bff`.

[Original export](../r03/pharynx_larynx.glb) · [Source and review](../r03/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/pharynx_larynx-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../r03/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-pharynx_larynx models/pharynx_larynx/recipes/teaching-economy-r01.json
```
