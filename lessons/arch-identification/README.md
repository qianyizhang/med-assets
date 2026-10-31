# Arch identification · EN / 中文

A standalone teaching plate for [issue #174](https://github.com/qianyizhang/med-assets/issues/174).
Select an arch and a numbered crown locator to read its source-labelled FDI,
arch, patient side and class. Arrow keys follow the displayed arch; Home/End
select its ends. Each arch remembers its own selection when language or view changes.

From the repository root, run `python3 -m http.server 8765 --bind 127.0.0.1` and
open `http://127.0.0.1:8765/lessons/arch-identification/`. No build, 3D runtime,
remote service, or runtime package is needed. Serve the repository root so the
relative media, coverage and attribution links resolve. The two existing PNGs
must be hydrated; unavailable images retain an FDI selector and a retry action.

## Sources and limits

The page reads the canonical [coverage receipt](../../docs/dental-atlas/set-coverage.json)
and references the original [crown-facing images](../../reviews/teeth_gums/2026-10-26-set-contact-checkpoint/README.md).
No model or image bytes are copied or changed. Patient right is screen left in
the upper image and screen right in the lower image. Slots 18/28/38/48 have
unavailable source coverage; this says nothing about a patient's missing teeth.

Each editorial endpoint was chosen on the inspected crown pixels, then checked
against the nearest visible triangle under the exact recorded camera. Object
centres are only a camera consistency check: they can project onto roots. Leaders
are locators, not tooth outlines, crown segmentation, contact validation, or
professional anatomy approval. The source still has failed adjacent contacts,
unvalidated bite and limited fine morphology. No anatomy or tooth repair is added.

BodyParts3D © DBCLS, CC BY 4.0 per the retained
[canonical attribution](../../models/teeth_gums/exports/r02/ATTRIBUTION.md).
Historical source-header terms remain in that attribution; no new licence is
asserted for the collection. See [review](review/README.md) for current evidence.

## Scoped checks

From the repository root, with Node 22+ and Python 3.11+:

```sh
npm install --prefix /tmp/arch-identification-qa --cache /tmp/arch-identification-npm-cache --ignore-scripts --no-audit --no-fund jsdom@26.1.0
NODE_PATH=/tmp/arch-identification-qa/node_modules node --test lessons/arch-identification/tests/plate.test.mjs
python3 lessons/arch-identification/tests/verify_sources.py
python3 tools/verify.py offline
```

The first suite runs the actual UI handlers in jsdom: all 28 IDs in both
languages, patient sides, keyboard/focus, state retention, image failure/retry,
and SVG layout bounds. It does not lay out HTML/CSS or execute a browser engine.
The source verifier needs the original hydrated GLB and two PNGs; it checks exact
hashes, source metadata, native transforms, camera projections and 28 ray hits.
Ordinary offline verification has its existing repository scope and does not
subsume these lesson checks.

For offline visual review, use a new output directory:

```sh
node lessons/arch-identification/tests/capture.mjs /tmp/arch-review-new
inkscape /tmp/arch-review-new/updated-upper-en.svg --export-type=png --export-filename=/tmp/arch-review-new/updated-upper-en.png
```

The capture function uses the exact live SVG component with relative image
references. Its surrounding labels are review captions, not screenshots of the
HTML shell. It emits desktop, narrow and fallback views for inspection.

For a supported local browser, install `playwright-core@1.57.0` in the temporary
QA prefix, keep the local server running, and run:

```sh
NODE_PATH=/tmp/arch-identification-qa/node_modules node lessons/arch-identification/tests/browser.mjs http://127.0.0.1:8765/lessons/arch-identification/ /tmp/arch-browser-new
```

This journey tests both languages, all IDs and both keyboard orientations,
320 px HTML layout, image failure and retry, and saves actual screenshots. It
requires the normal Chromium sandbox and fails without it. Never disable that
sandbox to manufacture a pass. Current browser coverage is blocked as recorded
in the review; the script is a pending journey, not a result.
