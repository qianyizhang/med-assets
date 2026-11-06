# Spleen source-surface locator · #200

A bounded identification aid for the already accepted HRA female r03 exterior. The original geometry is not repaired, replaced or newly accepted. Numbers identify the source's 5 named surface patches, not independently validated anatomical boundaries.

## Original / Updated
- Original: unchanged exact r03 freshly rendered under matched neutral lighting; not the historical PNG.
- Updated: the same PNG with numbered source-patch anchors. Original/Updated use identical geometry, material, camera, zoom and lighting.
- Detail A: identical source-pixel crop `(380,430,220,250)` at 1.4×, marked by the same rectangle in both overviews.
- The opposite view is derived by `position = 2*target - obliquePosition`; it is not an original source-confirmed evidence camera. Its source evidence filename/hash fields are intentionally absent.
- Hidden or too-small patches are unmarked. Anchors require a depth-visible ID-mask interior radius ≥15px. The opaque ID pass is diagnostic only, not the delivered appearance.

## Source and attribution
Exact decoded GLB: `4e2637cf6c844aef85ab77c2c1049d4e7647348a13c34d784795b98825f7c8c7`, 278,576 bytes. Stored gzip: `394995cd76c086b23cd63d94aacdc3f424da533933003b779a7028e12c7052bf`, 219,888 bytes.

Kristen Browne; Heidi Schlehlein. HRA Female v1.10: https://doi.org/10.48539/HBM637.DWBM.744 . CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . Added locator labels and matched rerenders; no provider endorsement.

| Number | Exact source label | 中文简释 | Source identifier |
|---|---|---|---|
| 1 | gastric surface of spleen | 脾胃面 | FMA:15837 |
| 2 | diaphragmatic surface of spleen | 脾膈面 | FMA:15828 |
| 3 | colic surface of spleen | 脾结肠面 | FMA:15838 |
| 4 | hilum of spleen | 脾门 | UBERON:0001248 |
| 5 | renal surface of spleen | 脾肾面 | FMA:15839 |

These names/identifiers are embedded in exact source nodes. Chinese labels are display translations. No internal red/white pulp, vessels, anatomical correspondence, population representation or clinical claim is added. Open source annotation patches remain open; no holes filled or shapes reshaped.

## Replay
Requires Blender4.3.2, Python3 with NumPy/Pillow/SciPy, Inkscape1.4, DejaVu Sans and Noto Sans CJK SC. All inputs must already be authorized and local. No network or package installation is performed by these scripts.

```sh
blender -b -t 4 --python-exit-code 3 --python render.py -- --source /exact/source.glb --output /new/render-directory
python compose.py --render-dir /new/render-directory
python check.py --render-dir /new/render-directory
```

Wrong source SHA, source labels/ontology or camera hash fail before output creation. Existing render/comparison outputs are refused. Optimized Python (`-O`) is refused. Keep originals and failed drafts distinct.

## Evidence boundaries
- Technical: source/camera and render-byte pins; 5 unchanged geometry/transform records; source materials restored; 15 visibility/anchor decisions; 6 bilingual matched panels; exact crop mapping; refusal tests.
- Visual/usefulness: independent actual-pixel review of matched overview, exact detail and complementary views; marker numbers remain interpretable without color-coded anatomy.
- Anatomy/clinical: unreviewed. Source labels are not ground truth verification.
- Live runtime: not tested; this is an offline static locator, not a WebGL improvement.
- Delivery: draft package contains 6 final PNGs plus recipe/checks/compact records. Embedded-raster SVGs are replay intermediates retained privately, not duplicate public payloads. Public transport, Site and merge outcomes remain separate; no successful publication is claimed here.

`render-receipt.json` binds reused V1 neutral renders. V2 changes captions, honest derived-view metadata, input guards and exact detail/locator layout only. Failed harsh-lighting and overflow-layout drafts remain separately retained.
