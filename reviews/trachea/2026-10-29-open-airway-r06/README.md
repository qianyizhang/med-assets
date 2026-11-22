# Trachea r06: open airway teaching views

**A substantial teaching derivative of the retained closed cast.** The proximal
mouth and two branch outlets are open; the cutaway reveals the continuous Y-shaped
cavity. The original r05 model is preserved. Related issue: [#133](https://github.com/qianyizhang/med-assets/issues/133).

![Before closed cast; current open shell and cutaway](display/comparison-whole.webp)
![Matched proximal detail](display/comparison-proximal.webp)

These WebPs display the geometry-bound SVG projections of the exact
baseline and current exports. The projections use matched cameras and scale, with
simplified visibility and illustrative shading. They do not reproduce all raster
occlusion. Actual Cycles PNGs were separately inspected and retained locally;
[raster bindings](raster-bindings.json) keep their versions and hashes distinct.

The exact originals are available from the Gallery as the [whole SVG](https://med-assets-model-survey.landy123007.chatgpt.site/assets/9776415517ac344631ba0d6ecfe00149fb87406b1fd0f681178a6613c55b9676/comparison-whole.svg)
and [proximal SVG](https://med-assets-model-survey.landy123007.chatgpt.site/assets/f0d26593e064d41f581f69041ae4d92188cae3ba2ff4ec4e05db9d79d25c29d8/comparison-proximal.svg).
The [pinned Git source](https://github.com/qianyizhang/med-assets/tree/503c33f1dadf403faaec373c1a11a8b40dc523d6/reviews/trachea/2026-10-29-open-airway-r06)
records the delivered SVGs.

| Gate | Result | Remaining limit |
|---|---|---|
| Actual pixels | Independent pass with limitations; V7 whole/proximal and V6 bifurcation/outlet detail | Coarse source, authored shell and cuts |
| Geometry/export | Both V7 exports pass topology and shell self-contact screens | Finite precision; band overlaps intentional |
| Airway continuity | All three opening seeds connect; 10,484 connected air samples | 1.2 mm sampled screen, not flow or caliber validation |
| Replay | Both final GLBs reproduced byte for byte | Existing hydrated r05 input; no fresh-checkout test |
| Anatomy | Public-reference screening of the teaching relationship | No specialist/clinical approval or measured tissue layers |
| Delivery | Exact GLBs delivered in PR #134; static Airway gallery v7 delivery recorded in [#133](https://github.com/qianyizhang/med-assets/issues/133) | Historical delivery evidence; no fresh remote availability check |
| Runtime | Live 3D unverified | Static gallery checks do not establish WebGL or clinical acceptance |

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
and [targeted checks](../../../models/trachea/recipes/open-airway/README.md).
Local receipt paths identify preserved review files, not public download links.
[Issue #133](https://github.com/qianyizhang/med-assets/issues/133) closed after bounded
asset and [static gallery](https://anatomy-airway-review.landy123007.chatgpt.site/review/trachea-r06/)
delivery. Its recorded EN/中文 browser checks and exact download hashes are historical,
not a new availability, live 3D or clinical pass.

</details>

## Restore the exact SVGs offline

The two `.svg.br` files contain the original SVGs losslessly. They are sufficient
to restore the historical paths in a fresh checkout. The loopback Gallery
preview serves the verified original SVG bytes at the ordinary digest URLs.
The displayed WebPs supply the README and Gallery image previews.

From the repository root with Node 24 or later, run the following before any
historical replay or transport check that needs the original paths.

```sh
node reviews/trachea/2026-10-29-open-airway-r06/restore-projections.mjs --output .
```

Use another existing directory with `--output` to restore there. The restorer
checks [decoded sizes and SHA-256 hashes](projection-bindings.json), preserves
exact existing files, and refuses conflicting bytes or links below the output
directory. Use the [transport guide](../../../transport/README.md#public-r2-downloads)
for the historical revision selector.
