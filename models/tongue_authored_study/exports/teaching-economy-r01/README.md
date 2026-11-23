# Tongue · hybrid · teaching economy edition

Identify the dorsum, median line and posterior papillae on the gross tongue exterior.

The retained hybrid and illustrative surface distinctions still apply.

The local GLB contains 145,480 triangles in 3,245,136 bytes. Its SHA-256 is `44ece7903283ba0eadf045b588bcfb3fb02dba86566d4468c760e36352af7a8f`.

[Original export](../authored-p11/tongue-authored-hra-hybrid-p11.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/tongue_authored_study-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../source/ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-tongue_authored_study models/tongue_authored_study/recipes/teaching-economy-r01.json
```
