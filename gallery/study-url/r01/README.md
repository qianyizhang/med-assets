# Keep the selected study in its copied URL (#207)

The study dropdown previously showed Aorta while retaining an Adrenals URL. Opening that URL selected the wrong study. The bounded fix validates the selected candidate, then replaces the current hash before showing it. Unknown or empty values cannot rewrite the route. No new history entry.

## Exact delivery choices — use only one
- On frozen combined #205/#206 Site head `827ff6549279568562718617ab4677551fbc5523`: `python3 apply.py REVIEW_DIR --mode combined`. Writes only review.js.
- On exact production v45 `c671a87e28332763d1d1d8df07b6291fd21de45d`: `python3 apply.py REVIEW_DIR --mode v45`. Composes #205/#206/#207 in one preflight, writes 3 reviewed files.
- References preserved hash-pinned comparison-navigation/r01 payloads rather than duplicating them. All input, payload and final hashes are checked before any write. Reapply, wrong source, or tampered payload fails without mutation. Do not sequentially apply standalone #205/#206 recipes.

## Intentional change and unchanged behavior
Dropdown candidate hashes intentionally now track the shown study. Original/Updated content, geometry, labels, approval status, language disclosure/layout restoration, Compare/Back focus, filters, scroll, lazy media loading and runtime routes are otherwise unchanged. Native select focus stays on the select. Back still returns to its overview origin; filtering and hidden-origin fallback are covered by the preserved #206 DOM suite.

## Evidence
`dom.mjs` runs against actual Site source: set GALLERY_ROOT to its absolute directory and HAPPY_DOM_MODULE to an already-installed HappyDOM module. It checks repeated selections, both language directions, hash reopening, exact direct-link startup via INITIAL_HASH, invalid/empty refusal, focus and unchanged history length. Fetch is stubbed to local review-data.json only. The same test fails on frozen #205/#206 at the stale Aorta hash assertion.

This is DOM simulation and offline technical evidence, not actual browser/assistive-technology/WebGL validation or anatomical review. No deployment, Blob operations, new dependencies, remote media downloads or clinical promotion. Frozen prior receipts remain unchanged.
