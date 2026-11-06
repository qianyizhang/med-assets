# Urinary region: readability decisions

**Current accepted scope:** V3 makes the two ureters easier to trace at the native
353 × 271 teaching size. Independent review found a valid small readability
improvement and requested no further iteration. Geometry, stroke widths, IDs,
labels, hit areas and coordinate data are unchanged. No anatomical, clinical,
accessibility or browser-runtime approval follows.

| Date | Version | Decision / state | Evidence |
| --- | --- | --- | --- |
| 2026-10-28 | V1 | Rejected presentation: vessels at `.18` and skeleton at `.55` lost useful renal branches/pelvic landmarks. | [V2 review](2026-10-28-context-r02/review.json) retains baseline/trial identities. |
| 2026-10-28 | V2 | Retain subdued context: skeleton `.75`, renal vessels `.28`, two broad trunks additionally `.64` (combined `.1792`). Independent acceptance remained pending at this step. | [Technical checks](2026-10-28-context-r02/technical-receipt.json): reversing four opacity attributes restores exact baseline XML; all 196 paths and 54 IDs unchanged, +42 bytes. |
| 2026-10-28 | V3 | Accept the small improvement: darken only two ureter strokes to warm ochre; keep V2 vessels discernible. Exact native baseline/V2/V3 comparison inspected independently. | [Current review](2026-10-28-context-r03/review.json) binds SVG and private comparison hashes; reversing two colors restores V2 XML. |

[Issue #124](https://github.com/qianyizhang/med-assets/issues/124) owns the decision.
The comparison images remain private, including the 79,483-byte V3 comparison.
The earlier Library image handoff was blocked before upload preparation. No new
image or publication authorization is implied. Packaged raster previews describe
the earlier version; use the current SVG. These are historical review results,
not a claim of fresh execution or remote publication.

## Reproduce a comparison

Export baseline `f2b6c8e` and the current
[`urinary.svg`](../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/urinary.svg)
with the same Inkscape renderer, fonts and opaque white background. Use width
`353` for native size or `1059` for 3×. Crop the latter at pixel bounds
`[177,138,489,768]` for ureter detail (source box `[230,412,104,210]`).
Chinese fixtures replace each text node with its existing `data-zh` value;
grayscale converts the same export. The author inspected matched EN/中文 native,
3×, detail and grayscale output; the V3 review reused those checks.

Inkscape ignores the existing hover/transition CSS and shadow filters. Those
behaviors were not changed or validated, and no interaction code changed.
Current source integrity is checked by `python3 tools/verify.py offline`.

[NIDDK's urinary tract explanation](https://www.niddk.nih.gov/health-information/urologic-diseases/urinary-tract-how-it-works)
was consulted for the existing teaching focus; no reference image was copied.
Source attribution and the package's simplified educational limits remain.
