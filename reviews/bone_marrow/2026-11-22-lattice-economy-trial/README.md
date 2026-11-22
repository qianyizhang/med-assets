# Proximal femur cutaway lattice economy trial

**Keep the strong version as a recipe-built local option for the reviewed teaching views.** In the oblique view, identify the unchanged cortical rim, then follow adjacent struts around an open window of the lattice against the red marrow backing. The close and reverse views confirm the exposed struts and continuous outer silhouette. The existing r05 rating and maintained file retain their original identities.

| Clean-imported file | GLB bytes | Total triangles | Lattice triangles | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| r05 control | 8,770,012 | 369,274 | 364,734 | `7b21b74fb3712b2816801337bd4d0732ef8bb035a999ad36558b8235609cfe02` |
| Moderate | 6,318,984 | 267,148 | 262,608 | `3cd5a4de8987eaa5b854c65b47605c4b837a5adc1c28f6aeb565e78650c81155` |
| Strong | 4,218,116 | 179,612 | 175,072 | `98c2e5ababce25387867803659b77f04ff1849d29c48fab65ad09b387e75b3d7` |

Strong saves 4,551,896 bytes (51.9%) and 189,662 lattice triangles (52.0% of the lattice and 51.4% of total triangles). Keep the existing [authored-content disclosure and source attribution](../2026-10-26-source-cutaway-r05/README.md). In particular, the lattice is a teaching schematic and the red backing helps show its geometry.

## What changed

[Matched overview](overview.jpg) · [Teaching close-up](detail.jpg) · [Diagnostic crop locator](locator.jpg) · [Enlarged worst control-to-candidate region](worst-forward.jpg) · [Enlarged worst candidate-to-control region](worst-reverse.jpg)

The lower visible lattice boundary, windows in the femoral head and oblique struts against the cut cortical rim remain traceable in the reviewed captures. In the forward diagnostic crop, look between the brackets at the crossing over the backing. The strong mesh subtly straightens a contour along the junction and changes its highlight. The dark gap between adjacent struts remains open. In the reverse-direction diagnostic crop by the femoral head, the highlight narrows on a small crossing and the adjacent opening remains distinct. The whole reverse view shows the same closed outer side. The lead reviewer independently confirmed the same teaching landmarks in the matched overview and close-up.

The trial starts from the exact r05 mesh. It applies Blender weighted collapse to the lattice only. Cortex and marrow accessor payloads are byte-identical and the scene, node transforms and materials compare equal. Exact-coordinate reimport gives one consistently oriented closed component with Euler characteristic −4204 and no zero-area triangles in both variants. The query against the candidate surface reports zero displacement for all 2,169 original near-interface vertices and 5,279 points classified as thin by an inward normal ray. These are sampled geometric protections.

| Measured nearest surface maximum | Control to variant | Variant to control |
| --- | ---: | ---: |
| Moderate | 72.42 µm | 50.45 µm |
| Strong | 97.13 µm | 98.45 µm |

The maximum search samples every vertex and triangle center on each surface. The strong maximum is under the scale of one native pixel in the close camera, with its near-head and lower-lattice locations shown separately at larger scale. This is a sampled point-to-surface result. The trial did not establish continuous Hausdorff error, per-strut mechanical integrity, exhaustive self-intersection or source-envelope containment. It does not claim measured load paths or browser speed.

## Replay and verification

[Recipe](../../../models/bone_marrow/recipes/lattice-economy-trial/README.md) · [Topology and deviation receipt](geometry.json) · [Exact render bindings](views.json) · [Retained plate identities](plates.json) · [Replay and failure checks](verification.json)

Both variant GLBs replayed byte-for-byte, and the 12 common decoded RGB frames matched exactly. The runs used Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay renders the same owner camera poses, scale and broad light rig for the three exports, fresh from GLB. All full frames are 1000 × 1200. The diagnostic crops use a shared 18 mm orthographic span centered on the worst directed sample, marked in the comparison. Raw frames and generated GLBs stay in ignored replay output. The recipe rejected a different GLB and an occupied output, preserving the occupied directory.
