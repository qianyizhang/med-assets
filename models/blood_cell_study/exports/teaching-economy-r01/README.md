# Blood-cell forms · teaching economy edition

Distinguish erythrocytes face-on and edge-on, then locate the segmented neutrophil nucleus in the opening.

The authored study compares independent display scales. This trial supports appearance and gross discrimination only.

The local GLB contains 111,302 triangles in 2,722,128 bytes. Its SHA-256 is `cd34b007869be3d77a0e8493b21c51f5bd99fc86c0e496aee9716f698055d4b6`.

[Original export](../authored-r05/blood-cell-authored-study-r05.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/blood_cell_study-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-blood_cell_study models/blood_cell_study/recipes/teaching-economy-r01.json
```
