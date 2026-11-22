# Lymph reconstruction and runtime diagnostics

- **Goal** · Check exact source and compact candidate bytes, then sample visibility, normals, front/back culling, framebuffer and actual display. [Fixture and IDs](glb-runtime-fixture.json) · [Probe](glb_runtime_probe.py) · [Diagnostic checks](lymph_diagnostics.py).
- **Guard** · Main-only manual run after exposure review and authorization. 10 MiB per download, 16 MiB local generated-file cap. Rebuild the r03 intermediate, source map and compact candidate in ephemeral storage. Check byte count and SHA-256 before serving on loopback. Retain images, logs and provenance for three days. Keep temporary GLBs and recipe receipts out of uploaded bundles.
- **Identity** · Fixture binds the published source, intermediate, source map and reconstructed compact output. The retained compact comparison has different metadata and a distinct hash. Its Blender measurements and pixels belong to those retained bytes.
- **Historical scope** · Run 40624597742 passed its 21-state finite-normal, framebuffer/display and state checks. Back-normal speckling appeared in both source and candidate. Its cause remains unresolved. The diagnostics extend that sequence by 12 orbit and four mutation/restoration captures, before the esophagus extension.

| Gate | Acceptance |
| --- | --- |
| Matched samples | Same camera, projection, lights and background in paired lit views. Four fixed model-coordinate directions for front/back normal inspection. Keep common source bounds and scale. |
| Mesh normals | Per-mesh finite, zero/nonunit and min/max reports, with triangle, degeneracy and opposed-corner counts. Zero threshold ≤1e-6, unit tolerance 1e-3. Candidate referenced normals meet bounds. Source zero/nonunit normals and opposed corners are observations. |
| Real culling | Verify actual final-draw WebGL culling mode/front face, front/back switching and expected camera directions. Coverage applies to sampled draws and views. |
| Negative controls | Negate cloned normal attributes and independently reverse cloned triangle indices. Each changes at least 100 pixels at maximum RGB channel difference >2. Restore original attribute objects and require zero changed pixels at that tolerance. Preserve visibility, transforms and display checks. |
| Evidence | `lymph-diagnostics.svg` has 20 labeled tiles. `lymph-diagnostics.json` binds normal reports, raw readback and thumbnail hashes, control counts, attribution, scope and sheet hash. Full display/canvas captures support independent inspection. |

- **Local checks** · [Offline gate](../../docs/WORKFLOW.md#verification) and `node --test tests/runtime_receipts/test_lymph_diagnostics.mjs`. Receipt and CPU tests cover invalid cameras/culling, ineffective controls and imperfect restoration.
- **Limits** · Headed software-renderer checks cover sample states. GPU performance, supported-device behavior and production viewer need separate evidence. Anatomy, clinical and visual decisions remain independent. Vascular label and speckling cause remain unresolved.
