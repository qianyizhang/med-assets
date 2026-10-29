# Stalk relationship review

**V2: continuous exterior, with disclosed inferred geometry.** Related:
[issue #146](https://github.com/qianyizhang/med-assets/issues/146).

| Original | Updated |
| --- | --- |
| ![Original whole](renders/original-whole.png) | ![Updated whole](renders/updated-whole.png) |
| ![Original stalk overlap](renders/original-junction.png) | ![Updated inferred join](renders/updated-junction.png) |
| ![Original side junction](renders/original-junction-side.png) | ![Updated side junction](renders/updated-junction-side.png) |

Actual matched 900 × 1000 Cycles views, after clean GLB import. Baseline is the two
retained PR #24 exports in their shared source frame, with matched illustrative
colors. These are offline model renders, not browser screenshots. Coral =
hypothalamic envelope; amber = inferred join; teal = pituitary envelope.

- **🟢 Technical:** exact GLB reimport, one closed connected surface, 5,370 triangles, positive volume, no zero-area faces or nonadjacent contacts detected by the bounded finite-precision screen. Exact-byte recipe replay and source/overwrite guards passed.
- **🟢 Visual:** independent review passed with limitations across whole/front/side views. The intersecting source surfaces are resolved; a small front-stalk crease remains visible at detail scale.
- **🟡 Anatomy:** primary-reference support for the connection only. Union, smoothing and colors are authored teaching choices; no lobes/nuclei or measured tissue boundaries are claimed.
- **🟡 Runtime:** browser/intended-consumer interaction was not run. This receipt provides no runtime, specialist or clinical approval; gallery defaults are unchanged.

The [source package](../../../assemblies/hypothalamus-pituitary/teaching-stalk-r01/README.md)
contains the final GLB, recipe, source/reference links and attribution.

<details>
<summary>Exact receipts and iteration</summary>

- Base revision: `384b785c5f647234077dc34dcae56fbb10b6178c`.
- Final GLB: **130,668 bytes**, SHA256 `31ddd537a8aa3ac7dcd75a9a9789132fb10bcfeccb4149e14443d845fd7fb373`.
- [Build record](build-record.json): exact sources, union and localized blend, native frame, zero smoothing movement outside the chosen band. The maximum 0.936 mm in-band change describes this edit, not an anatomical tolerance.
- [Export check](export-check.json): exact GLB reimport and finite-precision topology/contact screen. It is not an exhaustive mathematical or anatomical proof.
- [Recipe check](recipe-check.json): byte-identical Blender 4.3.2 replay, same-size wrong-source refusal, existing-output refusal and identical V1/V2 decoded triangle positions.
- [Raster bindings](renders/raster-bindings.json): six image sizes/hashes, model hashes and matched cameras. Render recipe is [here](../../../tests/hypothalamus_pituitary/render.py).
- [Independent review](independent-review.md): actual pixels, source identities and metadata inspected by a separate reviewer. No duplicate renders or topology tests were run by the reviewer.
- V1's geometry already resolved the overlap, but lighting washed out region colors, polygon material borders looked jagged and inherited extras misidentified the combined model. V2 reduced matched light energy, used continuous vertex colors, and replaced stale extras. Failed V1 artifacts remain separate from this accepted package.
- [Satogami et al., 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC7964128/) supports the stalk connection and taper, not this derivative's dimensions or surface shape. No figures were copied.
- Local commands: package identity check and required `python3 tools/verify.py offline`; the latter is metadata/pointer sanity, not hydrated media or runtime validation. CI status belongs to the exact PR head.

</details>
