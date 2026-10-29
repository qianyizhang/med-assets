# Hypothalamus → stalk → pituitary

A separate teaching exterior resolves the intersecting stalk envelopes in the
retained [hypothalamus](../../../models/hypothalamus/README.md) and
[pituitary](../../../models/pituitary/README.md) source exports. The originals and
their source coordinates remain unchanged. Related: [issue #146](https://github.com/qianyizhang/med-assets/issues/146).

| Original | Updated |
| --- | --- |
| ![Original whole: two overlapping source envelopes](../../../reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/original-whole.png) | ![Updated whole: one continuous exterior](../../../reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/updated-whole.png) |
| ![Original stalk: intersecting colored surfaces](../../../reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/original-junction.png) | ![Updated stalk: inferred blended join](../../../reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/updated-junction.png) |

Matched offline Cycles renders of freshly imported GLBs, not browser screenshots.
Coral = hypothalamic envelope; amber = inferred join; teal = pituitary envelope.
Colors are teaching cues, not tissue segmentation.

- **Delivered:** [130,668-byte GLB](hypothalamus-pituitary-teaching.glb), one connected exterior in the retained source frame.
- **Reviewed:** whole model and two junction angles; no blocking visible gap or pinch. A small front-stalk crease remains in the enlarged view.
- **Limited:** low-detail atlas localization shapes; no lobes, nuclei, vessels, axons, measured junction boundary, physiology or clinical approval. Browser/runtime remains unverified. This does not change gallery defaults.

The [primary imaging paper by Satogami et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7964128/)
supports the funnel-like stalk connection from the hypothalamic median eminence to
the gland. It does **not** validate this union, smoothing, color boundary or its
dimensions. [OpenStax §17.3](https://openstax.org/books/anatomy-and-physiology-2e/pages/17-3-the-pituitary-gland-and-hypothalamus)
provides teaching context; no source artwork was copied. Internal subdivisions
are deliberately outside this derivative's scope.

## Use and reproduce

The GLB has no external buffers/textures and can be imported directly. Its native
source-frame location is retained, so frame the selected object in a viewer.
Carry [ATTRIBUTION.md](ATTRIBUTION.md) with redistributed files.

From a repository checkout with Git LFS installed, hydrate the two existing
source GLBs and this package/evidence. No private bundle or external atlas archive
is required:

```sh
git lfs install --local
git lfs pull --include='models/hypothalamus/exports/source-candidate-01/*.glb,models/pituitary/exports/source-candidate-01/*.glb,assemblies/hypothalamus-pituitary/teaching-stalk-r01/*.glb,reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/*.png'
python3 tests/hypothalamus_pituitary/verify_package.py
```

Recipe prerequisite: **Blender 4.3.2**, no third-party Python modules. Use new
output paths. The exact input hashes are enforced before creating output.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python assemblies/hypothalamus-pituitary/teaching-stalk-r01/build.py -- \
  --root . --out /tmp/pituitary-stalk-new
blender --background --factory-startup --python-exit-code 1 \
  --python tests/hypothalamus_pituitary/check_export.py -- \
  --candidate /tmp/pituitary-stalk-new/hypothalamus-pituitary-teaching.glb \
  --expected-sha256 31ddd537a8aa3ac7dcd75a9a9789132fb10bcfeccb4149e14443d845fd7fb373 \
  --out /tmp/pituitary-stalk-new/export-check.json
```

The recipe unions the three retained source shells and smooths only a bounded
stalk band. Geometry operations run in local millimetres, then return to the
unchanged source frame. Continuous vertex colors avoid implying serrated tissue
borders. The band and smoothing are authored presentation choices, not inferred
histology or a fitted clinical measurement.

Optional matched rerender (not needed to inspect retained evidence):

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tests/hypothalamus_pituitary/render.py -- \
  --root . --candidate /tmp/pituitary-stalk-new/hypothalamus-pituitary-teaching.glb \
  --out /tmp/pituitary-stalk-new/renders --baseline
```

See the [review receipts](../../../reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/README.md)
for exact identities and the separate technical, visual, anatomical and runtime status.
