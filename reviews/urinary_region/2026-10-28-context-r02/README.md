# Urinary region · clearer ureters

**Before:** broad red/blue background vessels compete with the thin gold ureters
at the native 353 × 271 size, also in grayscale.
**Current:** both ureters are easier to trace while kidney connections and pelvic
context remain visible. This is a regional presentation change, with no new anatomy.

- V1 faded all vessel context to `.18` and skeleton context to `.55`; the small
  renal branches and pelvic landmarks became too faint.
- V2 retains skeleton context at `.75`, renal vessel context at `.28`, and applies
  `.64` additional opacity to its two broad trunks (combined opacity `.1792`).
- All 196 paths, 54 IDs, label text/anchors, organ attributes, definitions,
  viewBox/clip and coordinate data are unchanged. The exact XML is identical after
  reversing these four opacity attributes. Payload change: **+42 bytes**.

The [review receipt](review.json) binds the baseline, V1, current SVG and local
image hashes. [Technical checks](technical-receipt.json) record XML and pixel
comparisons. The images are retained locally under the receipt's relative paths;
they are not part of this repository delivery. No image-publication permission is
inferred. Packaged raster previews remain historical; use the current SVG.

Author pixel review covers matched EN/中文 native and 3× overviews, ureter detail
and grayscale. No independent review, browser consumer/runtime pass or clinical
approval is claimed. Inkscape ignores existing hover/transition CSS and shadow
filters; those behaviors were not changed or validated. No interaction code was
changed, and there is no affected product E2E journey in this static SVG package.

The existing teaching focus was checked against
[NIDDK's urinary tract explanation](https://www.niddk.nih.gov/health-information/urologic-diseases/urinary-tract-how-it-works).
No reference image was copied. Existing source attribution and simplified
educational limitations remain in the package; the detailed atlas and other
illustrations are unchanged.

## Reproduce matched exports

From the repository root, export the baseline at `f2b6c8e` and the current file
with the same renderer, fonts, white background and width. Example:

```sh
git show f2b6c8e:body/2d-v4/whole-body-anatomy-v4-spatial/regions/urinary.svg > /tmp/urinary-before.svg
inkscape /tmp/urinary-before.svg --export-width=1059 --export-background=white --export-background-opacity=1 --export-filename=/tmp/urinary-before.png
inkscape body/2d-v4/whole-body-anatomy-v4-spatial/regions/urinary.svg --export-width=1059 --export-background=white --export-background-opacity=1 --export-filename=/tmp/urinary-current.png
python3 tools/verify.py offline
```

Use width `353` for native size. For detail, crop the 3× overviews at pixel bounds
`[177,138,489,768]`, equivalent to source box `[230,412,104,210]`. Chinese fixtures
replace each text node with its existing `data-zh` value. Grayscale is a diagnostic
conversion of the same exports, not an accessibility certification.
