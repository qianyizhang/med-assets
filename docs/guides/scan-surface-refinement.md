# Refine a scan-derived teaching surface

Use **scan-derived surface refinement** for the whole job. **Re-sculpting** describes a hands-on change to form, such as restoring a pinched fold. The same refinement can be made with a brush or a reproducible local filter. The deliverable is an interpreted teaching surface, a retained case reference and evidence for the features the learner should see. See [Visual and geometric quality target](visual-quality-target.md) for the expected appearance and [CT-to-mesh refinement best practices](ct-to-mesh-best-practices.md) for recommended SDF, fairing, sculpting and retopology pipelines.

## Before shaping

Write down the learner’s action, the closest intended view and the feature most likely to disappear. For the adrenal these were locating the glands relative to the kidneys, inspecting an isolated gland, and following a narrow cleft into its lower rim. Those choices determine where to spend the modeling effort.

Keep the original volume, segmentation and derived mesh identities distinct. Record which you actually inspected, the spacing along each axis, units, orientation, laterality and source terms. A low-resolution CT can establish broad placement; a label boundary also reflects partial-volume effects and segmentation decisions. When only the mask or mesh survives, call it the **case reference** and bound claims accordingly. Use another specimen to understand how an organ folds or catches light. Use the case reference to position this individual’s fold.

## Make the smallest change that solves the visual defect

| What you see | How to decide | What to do |
| --- | --- | --- |
| A staircase along a broad curved face | Inspect the full-resolution render and turn the mesh under neutral light. Check where the steps fall relative to the acquisition planes. | Smooth the broad face in physical units. Use a smaller neighborhood at a thin end or rim. Keep the original overlay visible while editing. |
| A cleft, branch or thin wall | Cut a plane through it and inspect adjacent source slices. Check the depth of the cleft, the span of the tip or the openness of the route, whichever matters to the lesson. | Protect the local contour. If global smoothing steals the feature, go back to the source in that region and blend the correction into the surrounding surface. |
| A dark hole or an apparent join | Isolate the part, inspect the reverse side and section it. A kidney recess has a back wall; a through-tunnel can exist in a closed mesh. Check adjacent parts together. | Preserve a supported opening and its clearance. For an uncertain opening, record any illustrative closure against the part and retain the traced version. |
| A waxy or toy-like finish | Compare identical framing and lighting with a neutral material, then with the teaching finish. Watch the highlight cross a known fold. | Correct the shape first. Tune base color, roughness and highlight width until the landmark reads. Identify illustrative color and check the export under the viewer’s own lights. |

A finer working grid can make interpolation smoother. Its spacing describes the computation; the original spacing describes what was sampled. For adjoining labels, inspect their shared boundary after smoothing. 3D Slicer documents local smoothing, shrinkage under Gaussian smoothing and joint smoothing for adjacent segments. [Slicer smoothing methods](https://slicer.readthedocs.io/en/latest/user_guide/modules/segmenteditor.html#smoothing)

## Budget the delivered view

Compare the refined mesh with a lighter copy of **the same shape and finish**. Keep camera, crop, output dimensions and visible parts fixed. Start with broad context surfaces, then reduce the target until an identifiable feature changes. Check the turning silhouette in pixels at the intended zoom and the protected feature in millimetres. Record per-part triangles, material primitives and whole-export bytes; textures and vertex attributes can outweigh the triangles saved. If both versions answer the question equally well at that view, ship the lighter one. Measure load time or frame time in the target viewer when making a performance claim. [Soft mesh budgets](asset-quality.md#soft-mesh-budgets)

## Decide whether to ship

Clean-import the actual export. Check part identities, laterality, relative placement, openings and any changed contacts. Compare it with the case reference in both directions and record a typical and worst surface distance. **Check the protected landmark in its own plane.** On a narrow fold, the nearest triangle can lie across the gap or in a neighboring slice. A good whole-organ distance or volume match can conceal a shortened fold.

Keep a matched overview, a decisive close-up in neutral and finished materials, and the local source overlay. Record the editorial changes, the feature that justified the chosen budget, and the largest remaining discrepancy. Apply the existing [teaching-asset rubric](asset-quality.md) to the named use.

**Adrenal example.** The earlier model’s right cleft looked plausible in the render. Across nine nearby sections its worst local contour error reached **6.55 mm** against the label-derived reference. Refining that region brought the maximum to **1.23 mm**. For the right gland, 500 triangles still worked at overview scale, but the lighter outline moved **2.24 pixels** at the shoulder in the oblique close-up. The delivered gland uses 1,500 triangles. Those measurements explain this asset’s choices; each new organ needs its own protected feature and viewing distance. [Case sections](../../reviews/endocrine-locator/adrenal-study-r05/case-sections.png) · [Scored comparison and measurements](../../reviews/endocrine-locator/adrenal-study-r05/README.md)
