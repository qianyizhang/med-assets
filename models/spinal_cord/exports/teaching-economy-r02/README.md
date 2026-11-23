# Spinal cord & roots · full-scene teaching edition

At one representative level, identify the dorsal-root swelling, separate ventral root and distal mixed-nerve union.

This edition packed the vertex normals using three signed normalized bytes in a four-byte stride with the standard glTF `KHR_mesh_quantization` extension. Worst measured normal direction change is 0.385°. Positions, topology, materials, all names and scene placements are exact. The full 104-mesh scene uses 178,960 triangles and 1,948,852 bytes, saving 714,436 bytes (26.8%).

[Teaching views](../../../../reviews/teaching-assessments/reopen-economy/views/spinal_cord-updated.webp) · [Original views](../../../../reviews/teaching-assessments/reopen-economy/views/spinal_cord-original.webp) · [Historical measurements and comparison](../../../../reviews/teaching-assessments/reopen-economy/README.md) · [Source and terms](../authored-roots-r04/README.md)

The [original export](../authored-roots-r04/candidate.glb) is the canonical input. Both files use the same model scope. The [review](../../../../reviews/teaching-assessments/reopen-economy/campaign-assessments.json) describes the protected landmarks and anatomical limits. Local size and image comparisons qualify the stated task. Distribution and frame-rate measurements require separate evidence.

## Rebuild

From the repository root, use the hydrated source and Python 3.12. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/spinal_cord/recipes/teaching-economy-r02.json .artifacts/rebuild-spinal_cord-teaching-economy-r02
```
