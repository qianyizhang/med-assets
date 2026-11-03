# Source-bound right-elbow legend correction (#209)

The preserved contact sheet incorrectly labels blue as meniscus/labrum. Exact retained export cd6cd488… binds its blue/teal transparent material to Articular capsule of elbow joint.r; see source-proof.json. Correction follows source metadata, not independent clinical anatomy validation.

Consumer change: visible EN/中文 notice FIRST in the exact contact image's figcaption. Shared captionHTML covers its current/legacy gallery occurrences. Identity requires evidence ID, WebP hash and model hash together; wrong or unrelated records receive no notice. Old image remains explicitly historical, with its mistaken legend disclosed. Images, models, data, captions of other evidence and approval gates unchanged.

## Guarded delivery
Run python3 apply.py REVIEW_DIR. Exact evidence-view.mjs and review-data.json hashes are verified, then complete output hash, before the sole evidence-view.mjs write. Reapply, wrong input or tampered output fails before mutation.
Both fresh v45 c671a87e28332763d1d1d8df07b6291fd21de45d and frozen208 0b58535cf7ed6300c1e9ace4441de24cfec3e3e1 have identical pinned inputs and are replay-tested. This independent patch does NOT silently install sibling205–208 repairs or overwrite review.js. To deliver208+209, apply to exact208 tree; do not blindly sequence standalone205/206 recipes.

## Verification
- Source-proof JSON pins retained export, selected material-to-node binding and exact contact image; no model/image binaries bundled.
- Actual-source DOM tests all exact contact occurrences in EN/中文/EN, visible-first notice, unchanged image paths, no media fetch.
- Unit tests reject wrong evidence ID/model/image hash and assert every other evidence record is unmodified.
- Frozen208 negative demonstrates missing correction.
- Strict migration-preservation guard pins209 evidence module then reverses only exact helper/caption addition to prior module hash.
- Offline MuPDF HTML print rendering can show readable bilingual correction beside preserved evidence, but is NOT browser CSS, interactive WebGL or anatomical validation. Actual browser remains unrun.
- Original renderer/PNG/native scene unavailable in bounded migration; no deterministic source replay or new render claimed.

## Verified composed205–209 delivery order
For a fresh exactv45 directory: first run gallery/evidence-locale/r01/apply.py REVIEW_DIR --mode v45 (the composed205–208 recipe), then run this209 apply.py. Independent replay matched all4 final files. Do not reverse this order: the208 recipe pins the original evidence-view.mjs and correctly rejects the209-modified module. This is an explicitly verified composition, not sequential standalone205/206 recipes.
