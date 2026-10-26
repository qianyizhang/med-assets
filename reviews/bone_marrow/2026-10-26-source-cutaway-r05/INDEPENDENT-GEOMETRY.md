# Final portable model — independent geometry binding

Final GLB SHA256: `7b21b74fb3712b2816801337bd4d0732ef8bb035a999ad36558b8235609cfe02`.

All 3 meshes have **exact oriented-coordinate geometry equality** to reviewed r05 (`dbfd05f3555691c30adde187b2ae1a77f0991e895bc4c0433a22abd0a4292813`), including topology after serialization-independent canonicalization. Raw GLB node transforms were identity. Metadata/object naming differences do not change this geometry binding. Receipt: `final-allmesh-equality.json`.

A fresh standalone verifier also ran successfully against final GLB and pinned source skeleton GLB, independently extracting `FJ3259 left femur`. It confirms all 3 components manifold and nondegenerate; all vertices pass source-envelope screening; shell has 0 nonadjacent contact candidates. Receipt: `final-portable-check/geometry.json`.

## Tested portable invocation

Requires Blender 4.3.2 with its bundled NumPy; no hidden .blend file or third-party Python package.

```sh
blender -b --python-exit-code 1 --python verify_geometry.py -- \
  --candidate marrow_cutaway.glb \
  --source skeleton-source.glb \
  --out NEW_CHECK_DIRECTORY
```

Default source hash is `d224985628cc62d0c9c4284019b73505c9ebf14d78d30a040d74a7b33c68620e`; final candidate hash is pinned above. Optional SHA arguments must only be changed intentionally for another review. Wrong hash rejected before creating output; existing output directory rejected. Both actual failure tests exit1; `verifier-safety-tests.json` records them. Hash validation precedes output creation. Normal successful verifier run took approximately1min in the shared cloud executor; resource-dependent.

## Scope retained

This is construction-level QA for an authored teaching cutaway, not patient cortical/trabecular segmentation, clinical anatomy validation, runtime testing, mechanical validation or whole original asset acceptance. Vertex containment is not full triangle-interior containment proof; shell contact screen excludes shared-vertex pairs and uses finite precision. No exhaustive network self-intersection proof. Network/backing overlaps are intentional. Measured 2,624 network-shell triangle contacts are not 142 verified attachment sites or watertight fusion. Original whole asset remains Needs revision; count delta0.

No model bytes were modified by this review. Separate visual/reference acceptance is still required.
