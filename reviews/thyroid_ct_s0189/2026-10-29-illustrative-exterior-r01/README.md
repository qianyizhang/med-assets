# Thyroid: reduced surface corrugation

![Original and updated oblique overview and ridge detail](comparison.png)

*Matched offline Cycles exports, original left / updated right. Native pixels;
illustrative color. These are not browser screenshots.*

- **Positive:** repeated ridges soften while broad depressions, unequal lobes,
  deep U-shaped recess and narrow bridge remain readable.
- **Checks:** clean GLB reimport; one closed component; 4,172 vertices / 8,340
  triangles; zero detected nonadjacent contacts. Replay is byte-identical.
- **Independent review:** [pass with limitations](independent-review.md) across
  five matched view pairs. No further smoothing requested.
- **Pending:** exact same-sample tracheal relationship, clinical validity and
  live runtime remain unverified. [#148](https://github.com/qianyizhang/med-assets/issues/148)
  stays open; this draft addresses its isolated-exterior scope.

Takeaway: a useful separate illustrative exterior, with the original retained.

<details>
<summary>Identities, scale, recipe and checks</summary>

Candidate: `4c2dee513f713fd8d649e7d1928ba3859ce1d25e81468e707b65a5fbeeee216a`,
152,124 bytes. Source: `4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883`,
151,580 bytes, baseline revision `384b785c5f647234077dc34dcae56fbb10b6178c`.

[Recipe and rationale](../../../models/thyroid_ct_s0189/illustrative-exterior-r01/README.md)
· [attribution](../../../models/thyroid_ct_s0189/illustrative-exterior-r01/ATTRIBUTION.md)
· [review gates](review.json)
· [build](build-record.json)
· [export/reimport](export-check.json)
· [replay](replay-check.json)
· [failure guards](failure-guards.json)
· [V1 finding and V2 fix](failed-v1-record.json).

The source is TotalSegmentator v2.0.1 s0189, a public clinical-source sample, not a
normal atlas. Existing 1.5 mm label-spacing/unit caveats remain. Blender's
Laplacian Smooth applies localized weights without adding topology. Measured
maximum movement is 0.609 mm, RMS 0.205 mm and central-band maximum 0.279 mm.
Fresh-import volume change is +0.00056%. These describe this operation, not
anatomical accuracy tolerances. Materials and source metadata are retained.

The silhouette evidence is the matched whole/oblique/reverse/side views and
reported source/candidate bounds. No source-variation normalization is intended.
The builder also inspected a grayscale conversion of the oblique pair: the same
ridge reduction and gross shape remain readable without relying on color.

Geometry checks use clean Blender reimports without seam welding. Nonadjacent
triangle contacts are screened with a BVH and finite-precision separating-axis
test; they are not an exact-arithmetic or anatomical proof. Same-case trachea is
absent from the retained export and local context; no unrelated trachea is used.

Reproduce the affected integrity check and validate hydrated evidence from the
repository root:

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/thyroid_exterior/check_export.py -- --root . --candidate models/thyroid_ct_s0189/exports/illustrative-exterior-r01/thyroid-illustrative-exterior.glb --expected-sha256 4c2dee513f713fd8d649e7d1928ba3859ce1d25e81468e707b65a5fbeeee216a --out /tmp/thyroid-export-check.json
python3 tests/thyroid_exterior/verify_package.py
python3 tools/verify.py offline
```

Use a new receipt path. The package validator checks actual hydrated source/GLB
and all ten PNG hashes, matched cameras, source metadata/material and receipt
bindings; it does not rerender or promote visual/runtime approval. The repository
offline gate separately checks text/pointers and existing tests, not all media.

</details>

<details>
<summary>Other matched views and original pixels</summary>

[Raster bindings](renders/raster-bindings.json) · [comparison binding](comparison-binding.json).
All views use the same camera, scale, lighting and unchanged material within each
pair. View names refer to the comparison setup, not independently verified axes.

| View | Original | Updated |
| --- | --- | --- |
| Whole | [PNG](renders/original-whole.png) | [PNG](renders/updated-whole.png) |
| Oblique | [PNG](renders/original-oblique.png) | [PNG](renders/updated-oblique.png) |
| Ridge detail | [PNG](renders/original-ridge-detail.png) | [PNG](renders/updated-ridge-detail.png) |
| Reverse | [PNG](renders/original-reverse.png) | [PNG](renders/updated-reverse.png) |
| Side | [PNG](renders/original-side.png) | [PNG](renders/updated-side.png) |

The earlier retained oblique camera settings were unavailable. These new matched
views expose the same class of repeated ridge artifact on the exact retained
source. V1's wrong-face weighting and weak comparison setup were rejected; its
failed artifact and pixels are retained separately, not delivered as the candidate.

</details>
