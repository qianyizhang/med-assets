# Breast pair · teaching economy edition

Locate each areola on the external breast and distinguish its surface position from the posteriorly visible atlas layers.

The covered task is gross external location and posterior overview. Color interpolation and isolated sublayers at higher zoom still need their own review.

The local GLB contains 691,668 triangles in 32,567,624 bytes. Its SHA-256 is `2a7d6d05e06fa8d86adffdf0fd324389cf23ac736b3b659f7c227b96e499fe51`.

[Original export](../source-candidate-02/breasts_hra_native_frame.glb) · [Source and review](../source-candidate-02/README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/breasts_hra-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../source-candidate-02/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-breasts_hra models/breasts_hra/recipes/teaching-economy-r01.json
```
