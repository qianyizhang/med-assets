# Prostate · teaching economy edition

Distinguish the prostate gland outline below the paired seminal vesicles and identify the proximal source ducts.

The evidence supports gross orientation, with no claim of continuous duct patency or fine internal-zone inspection.

The local GLB contains 165,066 triangles in 3,013,520 bytes. Its SHA-256 is `b46de84b02283254f06855274831657641dbd8c3e94f558f3677ecaa8255c700`.

[Original export](../hra-v1.1/VH_M_Prostate.glb) · [Source and review](../../README.md) · [Matched view](../../../../reviews/teaching-assessments/refinement-economy/views/prostate-trial.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md). [Source attribution and license](../../ATTRIBUTION.md).

## Rebuild

Use the hydrated source and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks the retained streams, clean imports, triangle count and exact reviewed GLB identity. The historical matched views remain linked above.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python tools/rebuild_mesh.py -- .artifacts/rebuild-prostate models/prostate/recipes/teaching-economy-r01.json
```
