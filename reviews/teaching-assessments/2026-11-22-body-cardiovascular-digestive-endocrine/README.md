# Body, cardiovascular, digestive and endocrine teaching review

Codex Sol, 2026-11-22. The [assessment record](campaign-assessments.json) contains learner tasks, four axis observations, exact identities, attributable evidence and decisions for the 24 maintained starting files. The [work item](../../../records/work-items/items/TAQ-005-review-body-cardiac-digestive-endocrine.md) records the scope and disposition.

## Keep the exterior and teaching section in separate views

Use the middle panel for source shape and the right panel for the authored exercise. The left panel shows what happens when both alternatives are visible together. Each row uses one unchanged GLB at a fixed orthographic camera, scale, studio light and neutral material.

| Exact file | What to identify | Comparison |
| --- | --- | --- |
| [Gallbladder](../../../models/gallbladder/exports/metadata-cleanup-r01/gallbladder.glb) | The source sac contour, the continuous editorial cut rim, and the separately authored cystic duct. The duct is schematic. The apparent interruption where it approaches the wall does not establish a connected lumen. | [Co-visible versus isolated parts](views/12-isolation.webp) |
| [Stomach](../../../models/stomach/exports/metadata-cleanup-r01/stomach.glb) | The elongated s1233 exterior and the rugae pattern in the independent schematic section. The cut face, depth and fold layout are authored. The section omits the gastric inlet and outlet. | [Co-visible versus isolated parts](views/17-isolation.webp) |

In a clean Blender glTF import choose one alternative in the Outliner. For gallbladder, show **Gallbladder | source surface** alone for the exterior. For the section, hide it and show **gallbladder | anterior teaching section** and **Cystic duct · schematic**. For stomach, show **Stomach | source surface** alone, or hide it and show **stomach | authored closed-back teaching section** and all **Gastric mucosal fold** parts. Keep the two alternatives separate when framing or explaining the view.

The plates are a directly usable teaching improvement. The scored readability remains the all-parts initial state of the exact asset. Browser default visibility and any new GLB remain separate decisions.

## Capture and replay

The paired plates are newly captured from the hydrated starting files. Blender 5.2.3 LTS Release Candidate `fab76e95306d` opened the native Workshop and factory-reset before every GLB import. Workbench renders use flat material swatches where the import exposes a solid base color and a broad studio highlight for neutral views. Workbench displays geometric form without evaluating tissue texture, transparency, or vertex-color shaders. The main and alternate camera directions are recorded in [the render receipt](render-receipt.json). The Workshop thorax crop illustrates relative placement. Native control driving and instanced render visibility need a separate check. Animation frame numbers in the cardiac motion strip refer to frames in the imported Blender scene.

From the repository root, use Blender with the hydrated inputs. Run the local command-specific headless approval procedure where applicable. With Python and Pillow available, compose fresh plates in a new output directory.

```sh
review=reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$review/render.py" -- "$review/render-receipt.json" .artifacts/taq-005-replay
python3.12 "$review/plates.py" .artifacts/taq-005-replay .artifacts/taq-005-replay/plates
```

The render receipt records input SHA-256, cameras, visibility requests, base-triangle counts, material slots and raw-image hashes. The assessment records bind the exact delivered WebP bytes. The assessment explicitly scopes earlier owner screenshots to what they depict. In particular, parathyroid thyroid context comes from the separate [context asset](../../../models/parathyroids/exports/z-localization-r01/parathyroids_thyroid_context.glb). Separate authored whole-heart, body-shell, and static-exterior decisions also remain exact-version specific.

Retain these plates with the assessments while they support the active Library and visibility findings. Specialist review, viewer behavior, and publication require their own evidence.
