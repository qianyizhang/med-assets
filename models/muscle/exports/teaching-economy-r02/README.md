# Muscle atlas · full-scene teaching edition

Locate the superficial chest and abdominal muscle surfaces anteriorly and the paired shoulder/back groups posteriorly.

This edition packed the vertex normals using three signed normalized bytes in a four-byte stride with the standard glTF `KHR_mesh_quantization` extension. Worst measured normal direction change is 0.389°. Positions, topology, materials, all names and scene placements are exact. The full 509-mesh scene uses 1,993,160 triangles and 22,558,848 bytes, saving 7,958,464 bytes (26.1%).

[Teaching views](../../../../reviews/teaching-assessments/reopen-economy/views/muscle-updated.webp) · [Original views](../../../../reviews/teaching-assessments/reopen-economy/views/muscle-original.webp) · [Historical measurements and comparison](../../../../reviews/teaching-assessments/reopen-economy/README.md) · [Source and terms](../z-anatomy-r02/ATTRIBUTION.md)

The [original export](../z-anatomy-r02/muscle_z_native_frame.glb) is the canonical input. Both files use the same model scope. The [review](../../../../reviews/teaching-assessments/reopen-economy/campaign-assessments.json) describes the protected landmarks and anatomical limits. Local size and image comparisons qualify the stated task. Distribution and frame-rate measurements require separate evidence.

## Rebuild

From the repository root, use the hydrated source and Python 3.12. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/muscle/recipes/teaching-economy-r02.json .artifacts/rebuild-muscle-teaching-economy-r02
```
