# Exact-source software-CI render evidence

**Scoped pass, not a general runtime or anatomy pass.**

[Run 39937314430](https://github.com/qianyizhang/med-assets/actions/runs/39937314430)
used stock headed Firefox 157.0 + Mesa software rendering and exact Three r180.
Both exact source hashes in `record.json` loaded and rendered. Fourteen real
canvas/display captures matched RGB pixels exactly. Lymph capsule hide changed
28,083 pixels and restore returned exactly. Full-heart 0.2/0.4 s changed
14,642/15,918 pixels; valve-only diagnostic changed 11,405/7,788 pixels.
All 2,552 recorded morph evaluations matched independent source expectations
with zero error; 0.8 s, exact loop return, paused state and visibility restoration
returned to their expected pixels.

These are deterministic scene API/mixer checks, **not native UI clicks, production
whole-site interaction, hardware performance, anatomy or clinical validation**.
The requested four phases miss the early atrial peak. The isolated valve images
are diagnostic, not a complete heart. Lymph key 7's identity conflict remains.
Existing review gates are unchanged.

`record.json` is the concise scope contract. `frame-results.json` retains actual
morph/visibility evidence; source/browser/code bindings and an independent
post-download PNG/weight recheck are separate JSON files. `images/` contains
unmodified original canvas PNGs and actual displayed-canvas crops. Full browser
screenshots, logs, profiles and ephemeral loopback/temporary paths are intentionally
excluded. The original verified CI archive remains retained locally; this bundle
does not depend on the three-day hosted artifact surviving.

This supplemental evidence remains bound to the exact sources and recorded test
conditions. Every retained file is catalogued in MANIFEST.json.
