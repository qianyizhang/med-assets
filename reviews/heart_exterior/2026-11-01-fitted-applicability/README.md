# Exact fitted-heart visibility applicability

| Original: fitted artifact, all source meshes | Updated: native opaque-exterior rule in memory |
| --- | --- |
| ![Original whole view](images/original-whole-front.png) | ![Updated whole view](images/updated-whole-front.png) |
| ![Original seam detail](images/original-seam-front.png) | ![Updated seam detail](images/updated-seam-front.png) |

Same exact fitted input, frame 0, camera, scale and lighting per pair. These are
reviewed Blender 4.3.2 renders, reused without rerendering. Updated hides the
source-defined internal members in memory; no fitted GLB derivative was exported.

- **Result:** the reserved exact-fitted applicability check for #150 passes with
  limitations. Compared with repository source `6912d439…`, exact fitted input
  `17b26d14…` preserves the full BIN, meshes, accessors, morphs, materials, 228
  animation channels and all original 248 nodes. Only a uniform pedagogical-fit
  parent and its scene-root reference differ.
- **Checks:** all 247 meshes at all 25 encoded keys match the documented fit
  transform, with maximum absolute per-coordinate difference
  `1.2907732452327458e-9 m` (about 1.29 nm), within the `1e-7 m` Blender
  floating-point tolerance. Loop coordinates close exactly. Applying the native
  123-hidden / 124-exterior classification in memory preserves all retained
  exterior coordinates at every key. An independent reviewer verified identities,
  units, graph/channel equality, all four images and recomputed all 247 meshes at
  keys 0, 9 and 24. No correction required.
- **Visible benefit:** removes source-hidden cords/leaflets from opaque exterior
  presentation. The wall opening geometry and remaining gap are unchanged;
  removing internal occluders exposes more background. No wall healing, geometry
  repair or complete anatomical exterior is claimed.
- **Conditions and limits:** opaque exterior only (`cut < .5 and mode < 1.5`).
  Cutaway and transparent modes retain internal members. The fit is explicitly
  pedagogical, not anatomically registered. Anatomical fit, underlying RV
  inlet/apparatus geometry, clinical validity and live WebGL remain unverified.
  Fixed-view t=0 appearance evidence does not establish all-time visual quality.
- **Delivery and retention:** four distinct overview/detail comparison images are
  the only binary additions. Original models, prior derivatives and private
  investigation history remain intact. This evidence package changes no Site,
  consumer, model or existing source rule. Related #158 remains completed; the
  separate segmented-source-heart work in #179 is outside this scope.

[Exact identities, render bindings, animation results and review](applicability.json)
retain the bounded evidence. [Earlier source applicability boundary](../2026-10-30-native-visibility-r01/provenance-and-applicability.md)
records why the exact fitted bytes were previously unverified. This record resolves
that technical correspondence question; it does not promote the other gates or
close the collection issue.
