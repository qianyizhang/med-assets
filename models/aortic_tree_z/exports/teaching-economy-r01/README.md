# Aortic tree · Z · teaching economy edition

Locate the brachiocephalic/right-carotid composite, left common carotid and left subclavian at the aortic arch.

The review covers the arch task and overview; it does not verify small-branch teaching at arbitrary zoom.

The local GLB contains 39,822 triangles in 700,032 bytes. Its SHA-256 is `a5835c72254467451cd295b7bcae5115a93c7a3df8de87e593a857a8929998b6`.

[Original export](../r02/aortic_tree_z_source_frame.glb) · [Source and review](../../../../reviews/aortic_tree_z/2026-10-29-arch-locators/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/aortic_tree_z-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../../../sources/datasets/z-anatomy/small-static-studies/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-aortic_tree_z models/aortic_tree_z/recipes/teaching-economy-r01.json
```
