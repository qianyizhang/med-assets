# HRA lymph-node tissue-layer review

Use the [capsule and tissue plate](plates/tissue-layers.webp) to locate the follicles, paracortex and medulla at the same camera and scale as the capsule. The gold contour projects the capsule boundary onto the matching interior view. Its position supports gross comparison. Tissue contacts and flow require separate evidence.

The [matched source comparison](plates/matched-source.webp) shows exactly what disappeared from the full HRA scene. The aperture visible in the retained capsule was already in the source. Its identity remains unassigned. The older [teaching-risk review](../refinement-risk/accepted.json) rated the unmodified source revision. The [new assessment](campaign-assessments.json) rates the tissue-only export on the same learner task.

- The [decoded GLB audit](build.json) verifies the scene graph, every retained triangle index, position, normal, vertex color, material and provider node field against the pinned HRA source.
- The [clean-import receipt](render.json) binds the two artifacts to camera, visibility, triangle totals and world transforms. All four same-visibility source and candidate views match decoded RGBA pixels exactly. [Pixel and plate bindings](comparison.json).
- The [neutral views](plates/neutral-form.webp) identify the form limitation. Both views preserve the capsule shape and recognizable lobules. Round source apertures, irregular medullary surface and deep clefts remain conspicuous. Additional source evidence is needed to interpret them anatomically.
- The [named isolations](plates/named-selections.webp) confirm the labels without changing material or camera. In the combined neutral view paracortex and medulla are harder to distinguish, so the rating applies to the paired plate and named visibility controls.

The exact export saves 59.74% of the source bytes and 55.04% of the triangles. Each of the four remaining parts supports the stated task. The medulla carries 88,388 of 114,498 triangles, about 77%. This initial review had no same-scope lighter comparison. The [later protected medulla trials](../target-risk/README.md) retain the economy score of 2 after testing shorter contractions. The source shell, named tissue regions and matched relationship establish fidelity for this bounded task. The campaign form score remains 2.

The [export owner](../../../models/lymph_node/exports/hra-tissue-layers-r01/README.md) identifies the omitted meshes, full citation and derivative terms. The [original source record](../../lymph_node/2026-10-23-hra-v1.2/record.json) preserves the four source anatomy names and older review. [Columbia histology specimens](https://histologylab.ctl.columbia.edu/lab08/lymph-nodes/) provide general anatomical landmarks. No histology image is reproduced.

## Replay

From the repository root, require the original hydrated source, Python 3.12, Blender 5.2.3 LTS Release Candidate `fab76e95306d`, Pillow 11.3.0 and libwebp 1.5.0. Use a fresh scratch directory. The builder uses the standard library and the repository's exact GLB reader. The recipe holds the two cameras accepted in the earlier teaching-risk review. Lighting, crop and label projection are recorded in the local recipes.

```sh
recipe=models/lymph_node/recipes/tissue_layers_r01
scratch=.artifacts/taq-014-replay
mkdir "$scratch"
python3.12 "$recipe/build.py" --output "$scratch/lymph-node-tissue-layers.glb" --report "$scratch/build.json"
python3.12 "$recipe/build.py" --output "$scratch/lymph-node-tissue-layers.glb" --check
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python "$recipe/render.py" -- --build-report "$scratch/build.json" --candidate "$scratch/lymph-node-tissue-layers.glb" --output "$scratch/render"
python3.12 "$recipe/plates.py" "$scratch/render" "$scratch/plates"
```

The build verifies every retained accessor and rejects an input with a different source identity. It validates an existing derived file without modifying it with `--check`. The plate compositor verifies the raw image identities, matched cameras and source/candidate visibility equivalence before writing new evidence. The receipts distinguish exact model bytes, rendered pixels and educational claims. This is a case-level localization study with outstanding specialist and histological acceptance.
