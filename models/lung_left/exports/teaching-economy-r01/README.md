# Left lung · s1233 · teaching economy edition

Find the left upper and lower lobes and follow their oblique fissure.

Re-encodes the three embedded PNGs with identical channels and metadata. All scene, UV, geometry and morph data stay exact.

The local GLB contains 31,200 triangles in 2,093,088 bytes. Its SHA-256 is `4cb7524a3843fda941d50adc060d2a3c9d08135bea6cddc99d03284d25bb683c`.

[Original export](../metadata-cleanup-r01/lung_left.glb) · [Source and review](../../../../reviews/lung_left/2026-10-23-metadata-cleanup-r01/verification.json) · [Matched view](../../../../reviews/teaching-assessments/target-economy/views/lung_left-updated.webp) · [Historical comparison and edition register](../../../../reviews/teaching-assessments/target-economy/README.md).

## Rebuild

From the repository root, use the hydrated source and Python 3.12 and Pillow 13.0.0. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/lung_left/recipes/teaching-economy-r01.json .artifacts/rebuild-lung_left-teaching-economy-r01
```
