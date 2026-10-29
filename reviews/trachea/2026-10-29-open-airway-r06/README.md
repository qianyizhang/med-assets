# Trachea r06: open airway teaching views

**A substantial teaching derivative of the retained closed cast.** The proximal
mouth and two branch outlets are open; the cutaway reveals the continuous Y-shaped
cavity. The original r05 model is preserved. Related issue: [#133](https://github.com/qianyizhang/med-assets/issues/133).

![Before closed cast; current open shell and cutaway](comparison-whole.svg)
![Matched proximal detail](comparison-proximal.svg)

These are **geometry-bound SVG projections, not screenshots or Cycles renders**.
They use the exact baseline/current exports, matched cameras and scale, with
simplified visibility and illustrative shading. They do not reproduce all raster
occlusion. Actual Cycles PNGs were separately inspected and retained locally;
[raster bindings](raster-bindings.json) keep their versions and hashes distinct.

| Gate | Result | Remaining limit |
|---|---|---|
| Actual pixels | Independent pass with limitations; V7 whole/proximal and V6 bifurcation/outlet detail | Coarse source, authored shell and cuts |
| Geometry/export | Both V7 exports pass topology and shell self-contact screens | Finite precision; band overlaps intentional |
| Airway continuity | All three opening seeds connect; 10,484 connected air samples | 1.2 mm sampled screen, not flow or caliber validation |
| Replay | Both final GLBs reproduced byte for byte | Existing hydrated r05 input; no fresh-checkout test |
| Anatomy | Public-reference screening of the teaching relationship | No specialist/clinical approval or measured tissue layers |
| Runtime/delivery | Recipe, SVG proof and text receipts | GLBs local/unpublished; gallery and runtime unchanged |

The V7 band-cap setback removes the proximal rim hatching. V6 and V7 shell
positions, normals, indices and node transforms are identical, permitting reuse
of the cavity check without relabeling V6 images. See the
[identity receipt](reused-shell-evidence.json), [independent review](independent-review.md),
[technical summary](checks.json) and [projection bindings](projection-bindings.json). The independent
[presentation check](projection-review.md) also passed at teaching scale; final SVG
CSS factoring preserves every reviewed path, color and stroke.
Whole-model status remains **Needs revision**; no accepted-count increase.

<details><summary>Iteration and reproducible evidence</summary>

- Early iterations exposed seam topology, poorly chosen cuts and shell contacts.
  V2–V5 failed the contact screen and remain retained locally as failed trials.
- V6 passed the geometry/connectivity screens and exposed a readable bifurcation.
  Independent pixels identified a hatched proximal strip from coplanar band caps.
- V7 sets those display caps back 0.05 mm. The reviewer found a clean continuous
  rim and no whole-view regression; no further visual correction was requested.
- Keep the cast distinct from the inferred wall. Source-normal offsets and
  explicit cut constraints addressed self-contacts; increasing numerical tolerance
  was not used to pass failed geometry. Geometry identity bounded reused evidence.

The original host is an already preprocessed TotalSegmentator display cast.
[Attribution](../../../models/trachea/exports/open-airway-r06/ATTRIBUTION.md)
retains CC BY 4.0 and the original Apache 2.0 label notice. The primary teaching
reference is [OpenStax A&P 2e §22.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system).
Shell thickness, local reductions, interior color, C-bands and cuts are authored.

See the [build recipe](../../../models/trachea/exports/open-airway-r06/README.md)
and [targeted checks](../../../tests/trachea_open_airway/README.md).
Local receipt paths identify preserved review files, not public download links.
Issue #133 stays open for remaining model/gallery delivery; this draft does not
publish GLBs, change the gallery or grant clinical/runtime approval.

</details>
