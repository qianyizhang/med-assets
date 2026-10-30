# Left kidney: locate the isolated shapes

Local EN/中文 teaching-view prototype under [collection #150](https://github.com/qianyizhang/med-assets/issues/150), based on main `cb5df4ab469ff4067cf42ecd29373d812f44906e`.
The retained contact separates exterior and isolated internal shapes by two rows.
This page asks whether placing a **2D editorial exterior outline** around the
unchanged internal tile makes its projected location easier to see.

## Decision and iteration

Retain the outline candidate for independent review. The outline makes the
top/bottom margins and the position of the internal clusters relative to the
projected exterior visible in one frame. The plain paired control shows the
same two 420-pixel tiles at equal scale; it remains available. Switching between
exterior/internal without an outline still requires remembering the exterior,
so the toggle alone has no demonstrated advantage over the paired control.
This is a visual inspection finding, not a measured learning outcome or anatomy
approval. The original accepted study is unchanged.

V1 pixels were inspected at desktop size and 320 pixels in both languages.
The English internal caption wrapped against the image at 320 pixels (37 pixels
of text in a 36-pixel box). V2 reserves 56 pixels for both captions at narrow
widths, preserving the same image position when switching. The Chinese link
label was corrected from “原始联系图” to “原始审阅拼图”. No other asset treatment
was added. Grayscale inspection retains a distinct dashed locator and readable
source shapes.

## Source and frame proof

All image content references the existing [contact WebP](../../reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/contact.webp);
no image or model binary is copied into this package. The page verifies its SHA-256
before displaying it. The [accepted record](../../reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/record.json)
binds that image to the exact r02 GLB. Current issue #150 and merged PR #7 were
read on 2026-10-30; both had empty label lists. No retired or `wontfix` work is used.

| Input | SHA-256 |
|---|---|
| r02 GLB | `8e55b5ae48821f067f41bd23ffdd668f68c7ff705cf49e9a40287042fee469fc` |
| Contact WebP bytes | `2a194bee7c66deab78bb74a090ee4f6bc44b6bcb59f9c57164100ffed506690d` |
| Historical contact PNG (not these WebP bytes) | `8479f68fd98b473ab73e55080b6aca8aba64f54391b9a8923ed5e2601ec564c3` |
| Retained 900 × 900 internal-front WebP | `b140b1200fe8947b2185da28e7dc39d27cc991facbb88d18bcb0e3bd81ef010c` |
| Render recipe | `ad77856fbe21d366dbab314fd4b390e2ef0996539425d4049c029fd556f1055a` |

[render_exact.py](../../tests/kidney_pair/recipes/render_exact.py) computes whole-model
center/span before changing visibility; all modes use the same orthographic scale
`1.18 × span` and camera for each review axis. The contact header also states
matched camera/scale. Its tiles are 420 × 420, at x = 0 / 420 / 840 and y = 112
(neutral exterior), 564 (PBR exterior), 1016 (isolated internals). Only neutral
front exterior and internal tiles are used here: full squares, no independent
centering, rescaling or mirroring. “Front” means the recorded native glTF +Z
review axis, not anatomical registration.

**The historical contact-composition script is not retained in this checkout or
the kidney import's Git history.** A full compositor replay is not claimed.
Instead, decoded source coordinates projected with the retained recipe agree
with all six neutral exterior/internal tile bounds within **1.033898 px**.
The screen-space bound check allows 2 px for raster edges, downsampling and lossy
encoding; it is not an anatomical tolerance. The 900-pixel internal front image
resized to the contact tile differs by mean **0.69593 RGB levels** (two lossy
derivatives). These checks corroborate full-frame alignment without new renders.

The dashed path follows the exterior tile's outer silhouette, sampled every four
pixel rows (180 points); [verify_source.py](../../tests/kidney_left_location/verify_source.py)
reconstructs it from pinned pixels. It traces no internal structures or collecting
routes. In the browser screenshot, it changes 1,378 background pixels and zero
foreground pixels in the source-specific internal-shape mask. That mask check is
a display observation, not anatomical segmentation.

## Run and check

From the repository root, with the retained contact payload hydrated:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/studies/kidney_left_location/`. Native radio buttons
support arrow keys; the outline checkbox supports Space. EN/中文 selection keeps
the current view and outline state. The URL variants below make comparisons
repeatable: `?view=internal&outline=0` (Original), `?view=internal&outline=1`
(Updated), and `?view=paired&outline=0` (simpler paired comparator).

```sh
python3 tests/kidney_left_location/verify_source.py
python3 tests/kidney_left_location/browser_check.py --output /tmp/kidney-location-NEW
python3 tools/verify.py offline
```

Source checks require Pillow. Browser checks require Python Playwright and local
Chromium at `/usr/bin/chromium`; the output directory must be new. No external
requests or packages are loaded by the page. Screenshots and one small hash/check
receipt are generated outside the repository, not committed as duplicate media.

Local validation: source identity/alignment passed; desktop screenshot crops have
**0 RGB difference** from their source tiles. Actual Chromium 154 checks passed
native keyboard controls, fixed image position, both languages, all three states
at 320/375 px without overflow, invalid query fallback, missing/mismatched source
rejection and recovery. Matched Original/Updated, paired control, Chinese, narrow
English/Chinese and grayscale captures are emitted by the browser check.
Repository offline validation passed **232 tests**, 26 transport manifests,
25 foundation records, 591 import references and 834 LFS pointer identities.
This is local 2D browser coverage, not a 3D runtime pass.

## Scope and attribution

[PR #7](https://github.com/qianyizhang/med-assets/pull/7)'s scope remains: exterior
and isolated pyramids/source-labeled tip surfaces only. No columns+medulla mode,
new GLB, tissue reshaping, measured depth, cutaway, collecting continuity or new
anatomical registration. Pelvis, calyces, ureter and vessels remain absent.
Original records, accepted assets and prior evidence are untouched; independent
review and any public delivery are still pending. Nothing is pushed or published.

Kristen Browne and Heidi Schlehlein (2024), *3D Reference Organ for Kidney,
Female, Left v1.3*, HRA / HuBMAP, [DOI](https://doi.org/10.48539/HBM449.JPXL.964),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
See the unchanged [attribution](../../models/kidney_left/ATTRIBUTION.md). This page
adds display cropping, controls and an explicitly editorial locator to retained
r02 pixels. No publisher endorsement or clinical/anatomical approval is claimed.
