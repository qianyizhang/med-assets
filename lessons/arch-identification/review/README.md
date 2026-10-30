# Issue 174 · Identification plate review

Owner/task: dental teaching worker, `arch-identification-174`, 2026-10-30.
Base: `cb5df4ab469ff4067cf42ecd29373d812f44906e`. Scope is one standalone
2D EN/中文 lesson; existing atlas geometry, historical receipts and other lessons
are unchanged. Current PRs were rechecked before implementation; no `wontfix`
work was selected.

| Original | Updated |
| --- | --- |
| [Unlabelled upper source image](../../../reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media/upper-occlusal-teeth.png) | [Upper EN offline plate](updated-upper-en.png) |
| [Unlabelled lower source image](../../../reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media/lower-occlusal-teeth.png) | [Lower 中文 narrow offline plate](narrow-lower-zh.png) |

Updated images are actual **Inkscape renders of the shared SVG component**.
The image camera, source pixels, aspect and endpoint coordinates match the live
component; surrounding labels are review captions. These are not HTML/browser
screenshots. The [fallback view](missing-lower-zh.png) also uses the live SVG.

## V1 → V2 findings

Inspected the actual original upper/lower PNGs and six V1 offline renders.
V1 exposed opaque black hit areas in Inkscape, top-edge crowding in narrow
views, and overlapping fallback rows. V2 uses explicit zero fill opacity,
inset top tags, and screen-size-based fallback spacing. Inspected five updated
views: upper EN and lower 中文 at 640 px; both at 292 px; missing lower 中文.
Labels and leaders are legible and separated at those sampled sizes. Visible
crown endpoints were inspected; roots remain visible in the source images.
The final label selected in the narrow lower view is FDI 47, patient right.

## Checks and exact limits

- **Source binding passed:** [source-check.json](source-check.json) checks all
  28 canonical source names/hashes → FDI → recorded camera identities. Both
  PNGs and the GLB match original receipt hashes. Native 30-node transforms
  remain identity. Object-centre reproduction error is at most 0.00022408 px.
  Each manually chosen visible-crown endpoint hits the expected front-most
  tooth triangle among that view's 14 teeth. This is not crown segmentation.
- **UI/static checks passed:** 10 Node/jsdom tests cover 28 IDs in each language,
  both orientations, class/side/arch text, crown-target click dispatch,
  keyboard traversal/focus/wrap, language and per-arch retention, stale image
  errors, image failure/retry, and label bounds/separation at 240, 292, 360,
  499, 500, 640 and 1000 px. The actual UI handlers run; jsdom does not lay out
  HTML/CSS or reproduce browser image loading.
- **Existing offline gate passed:** `python3 tools/verify.py offline`: 232 tests,
  26 transport manifests, 25 foundation records, 591 import references and
  837 LFS identities (834 existing + three review captures). That gate does not hash hydrated media;
  the scoped source check above does.
- **Browser blocked:** normal Chromium through Playwright 1.57.0 failed at
  startup because `/usr/lib/chromium/chrome-sandbox` was owned by `nobody:nogroup`
  rather than root. No browser launched. Sandbox was neither disabled nor
  changed. Actual HTML/CSS desktop/narrow reflow, browser image error/retry,
  focus/accessibility exposure and image rendering remain unverified. The
  checked-in browser journey is pending. There is no WebGL requirement.
- **Anatomy remains unapproved:** existing adjacent contacts fail, bite is
  unvalidated and fine crown morphology is limited. 18/28/38/48 remain
  unavailable source coverage. No repair or new anatomy is claimed.

See [evidence.json](evidence.json) for exact code/render hashes, tool versions,
and retained V1/V2 identities. Technical, offline visual, browser, clinical and
publication results remain separate.

## Retention

Canonical source: existing two PNGs, source coverage/camera receipts and r02 GLB.
The application uses relative references; it carries zero copied media/model
payloads and zero copied source inventories. Only three new raster review views
are retained here: desktop annotation, reversed/narrow Chinese orientation and
image-failure selection. They are unique review evidence, not application inputs.
Original images are linked, not copied. Other V1/V2 renders remain in the worker
evidence directory; the capture recipe and hashes retain their identities.
No model, historical receipt, global ledger, workflow or security setting changed.

Next: review the bounded draft and run the supplied browser journey in an
already-authorized environment with a working sandbox. Keep issue #174 open for
that browser acceptance. No merge, Site publication or collection promotion.
