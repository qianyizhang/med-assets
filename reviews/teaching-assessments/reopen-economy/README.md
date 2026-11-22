# Six lighter full-scene teaching editions

These editions preserve the original learner tasks, all selectable meshes, transforms, triangle indices and vertex positions. Together they use 32,293,220 bytes, down from 42,724,088. Every task has a matched original and updated plate in the [decisions](decisions.json). The [four-axis assessments](campaign-assessments.json) apply only to the exact editions listed there.

| Asset | Protected feature inspected | Technique | Encoded bytes saved |
| --- | --- | --- | ---: |
| [s1233 stomach](views/stomach-updated.webp) | Separate source exterior and section rim with eleven illustrative folds | Lossless re-encoding of all three PNG textures | 410,040 (12.1%) |
| [HRA liver](views/liver-updated.webp) | Capsule outline, posterior bare area and its fine ligament margin | Packed vertex normals | 168,128 (22.0%) |
| [Z-Anatomy muscle atlas](views/muscle-updated.webp) | Anterior chest and abdominal groups, paired shoulders and back | Packed vertex normals retaining all 509 selections | 7,958,464 (26.1%) |
| [BodyParts3D brain](views/brain-updated.webp) | Major sulci, cerebellar ridges and truncated brainstem | Packed vertex normals retaining all 49 selections | 968,660 (21.9%) |
| [Spinal cord and roots](views/spinal_cord-updated.webp) | Dorsal swelling, slender ventral root and convergence at representative upper level 7 | Packed vertex normals with original shared index streams | 714,436 (26.8%) |
| [Trachea](views/trachea-updated.webp) | Proximal and both distal rims, paired posterior C-band tips | Packed vertex normals retaining the shell and all bands | 211,140 (21.9%) |

The earlier [bounded geometry reductions](../target-economy/README.md) and [stomach fold trial](../target-risk/README.md) remain rejected under their original criteria. The new trials leave the protected geometry in place and reduce a different contributor to encoded size. The source density and triangle work per draw remain. No runtime performance estimate follows from the byte comparison.

For five files, the standard glTF extension `KHR_mesh_quantization` stores the three components of each vertex normal as signed normalized bytes in a four-byte stride. The worst change of direction across the five exports was 0.389°. The [measurements](measurements.json) identify the worst mesh for each file and count every normal examined. Every other buffer view retains the same bytes. For the stomach, the texture replay verifies image modes, all decoded color channel values, retained metadata, and the byte identity of every non-image stream, including its 13 translation channels. Clean-import frames at the exterior and section settings are pixel-identical.

The [pixel comparisons](views/pixels.json) use native 640 × 640 RGBA captures before plate compression. Every matched foreground alpha value is identical. Across the five packed-normal editions, the maximum foreground color difference is one step on the 0–255 scale. The variation is shading on the original surface. The facing distal rims were inspected from opposite obliques, and the neutral cerebellar, bare-area and pectoral enlargements address the close surfaces most vulnerable to shading error.

## Rebuild and compare

Use the repository root, the hydrated [source exports](editions.json), Python 3.12 with Pillow 13.0.0, and Blender 5.2.3 LTS Release Candidate `fab76e95306d`. Each output path must be new. The source revision was `0bc388a5b48d65ddb53060840470164ff1c6ce6a`. The edition manifest pins each control independently.

```sh
python3.12 reviews/teaching-assessments/reopen-economy/repack.py .artifacts/economy-rebuild
cmp .artifacts/economy-rebuild/measurements.json reviews/teaching-assessments/reopen-economy/measurements.json
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python reviews/teaching-assessments/reopen-economy/render.py -- \
  .artifacts/economy-rebuild .artifacts/economy-frames
python3.12 reviews/teaching-assessments/reopen-economy/plates.py \
  .artifacts/economy-frames .artifacts/economy-plates
cmp .artifacts/economy-plates/pixels.json reviews/teaching-assessments/reopen-economy/views/pixels.json
```

Two fresh conversion runs produced byte-identical models and measurement receipts. Replay verifies source hashes before conversion and checks each clean import against the original scene inventory for the packed-normal models. The stomach capture uses the earlier exclusive selection definitions for both exact exports. The local Gallery is the acceptance surface for the selected files and presets. Source attribution, source-specific limits and the unchanged canonical files are linked in each edition's README.

## Local Gallery acceptance

The [browser receipt](browser.json) records Chrome 157.0.8103.80 running the assembled Gallery on loopback. The source and teaching-edition stomach presets rendered the same textured exterior and section frames. Both versions kept their original Stage links. The new stomach and lymph-node presets recovered from a forced missing-model response, displayed their exact teaching posters on direct Stage entry, and returned to their corresponding Library records.

For the five packed-normal models the [Gallery probe](../../../sites/anatomy-gallery/tools/verify_refinement_scenes.mjs) downloaded each file from its ordinary Library record and opened those exact bytes in the Stage file picker. All original selections appeared. The probe isolated the liver bare area, a pectoralis major head, one cerebellar part, the representative dorsal root and C-band 8. The receipt identifies the selected parts, model digests and tested browser.
