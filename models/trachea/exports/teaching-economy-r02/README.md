# Trachea / Y-airway · full-scene teaching edition

Locate the proximal mouth and identify the two distal outlets of the authored Y-airway shell.

This edition packed the vertex normals using three signed normalized bytes in a four-byte stride with the standard glTF `KHR_mesh_quantization` extension. Worst measured normal direction change is 0.373°. Positions, topology, materials, all names and scene placements are exact. The full 19-mesh scene uses 50,978 triangles and 751,300 bytes, saving 211,140 bytes (21.9%).

[Teaching views](../../../../reviews/teaching-assessments/reopen-economy/views/trachea-updated.webp) · [Original views](../../../../reviews/teaching-assessments/reopen-economy/views/trachea-original.webp) · [Historical measurements and comparison](../../../../reviews/teaching-assessments/reopen-economy/README.md) · [Source and terms](../open-airway-r06/ATTRIBUTION.md)

The [original export](../open-airway-r06/trachea-open.glb) is the canonical input. Both files use the same model scope. The [review](../../../../reviews/teaching-assessments/reopen-economy/campaign-assessments.json) describes the protected landmarks and anatomical limits. Local size and image comparisons qualify the stated task. Distribution and frame-rate measurements require separate evidence.

## Rebuild

From the repository root, use the hydrated source and Python 3.12. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/trachea/recipes/teaching-economy-r02.json .artifacts/rebuild-trachea-teaching-economy-r02
```
