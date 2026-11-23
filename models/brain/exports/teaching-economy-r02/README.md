# Brain · full-scene teaching edition

Distinguish the cerebral hemispheres, cerebellum and exposed brainstem in the exterior atlas.

This edition packed the vertex normals using three signed normalized bytes in a four-byte stride with the standard glTF `KHR_mesh_quantization` extension. Worst measured normal direction change is 0.382°. Positions, topology, materials, all names and scene placements are exact. The full 49-mesh scene uses 242,358 triangles and 3,446,724 bytes, saving 968,660 bytes (21.9%).

[Teaching views](../../../../reviews/teaching-assessments/reopen-economy/views/brain-updated.webp) · [Original views](../../../../reviews/teaching-assessments/reopen-economy/views/brain-original.webp) · [Historical measurements and comparison](../../../../reviews/teaching-assessments/reopen-economy/README.md) · [Source and terms](../bodyparts3d-4.0-atlas-r2/ATTRIBUTION.md)

The [original export](../bodyparts3d-4.0-atlas-r2/brain-source-frame.glb) is the canonical input. Both files use the same model scope. The [review](../../../../reviews/teaching-assessments/reopen-economy/campaign-assessments.json) describes the protected landmarks and anatomical limits. Local size and image comparisons qualify the stated task. Distribution and frame-rate measurements require separate evidence.

## Rebuild

From the repository root, use the hydrated source and Python 3.12. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py models/brain/recipes/teaching-economy-r02.json .artifacts/rebuild-brain-teaching-economy-r02
```
