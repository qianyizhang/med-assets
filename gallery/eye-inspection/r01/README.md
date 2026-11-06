# Eye anterior-segment inspection (#99)

A bounded exact-source consumer recipe for the v47 gallery. The isolated r03
editorial cutaway gains whole/cutaway selection, shared camera/zoom, bilingual
limitations and guarded failure/retry. Whole mode is a seven-component study,
not a complete eye. No geometry, materials, model manifest or review gate is
changed; the separate whole-body `draft_eyes` entry remains unchanged.

The reviewed v47 change is incorporated in retained Site v50. The historical
applicator and application-only preservation tests are retired. The current
candidate is owned by `tests/viewer/candidate.js`; its exact helper identities and
Site source commit are bound by
[`tests/viewer/source.json`](../../../tests/viewer/source.json). Change the owning
Site source before refreshing this fixture; this repository does not deploy it.

## Model delivery remains separate

The unchanged immutable manifest serves whole r01 only when selected. Cutaway
uses the exact same-origin path in `record.json`; an authorized delivery must
separately supply its existing 6,139,756-byte gzip (SHA-256
`d57b6728b35179c85a6b22019566db5890e8f50ee386d96e987846a8e6939a84`).
Decoded r03 is 12,061,144 bytes, SHA-256
`1fe679f0f2386f2f19cf5c8ffebaffa0bc6ec0d9bd4fd0f97bd32bdc873905c1`.
No model or duplicate image payload is retained by this recipe.

## Checks and limits

- `python3 tests/viewer/run.py --suite eye` runs explicit media-free suites;
  `python3 tools/verify.py offline` includes them through `tests/test_viewer.py`.
- Current candidate composition now runs camera/zoom retention, lazy switching,
  failed-switch recovery/retry and disabled controls offline with synthetic
  transport/parser doubles. Transport integrity is separate from those state tests.
- `python3 tests/viewer/run.py --suite eye --whole-fixture EXACT_WHOLE_GZIP`
  adds the actual pinned whole-model transport/hash/embedded-GLB/camera check and
  reruns composition with actual whole bytes. No cutaway-byte check is claimed by
  that command. Missing/wrong fixtures fail, never skip.
- Source suites are selected by file, without rewriting their text. Every run has
  private staging and source-byte preflight. Compact records and the immutable
  manifest entry are test inputs, not replacements for the production manifest.

Site integration separately passed 68 Node checks, six DOM suites and a build;
repository offline checks remain a separate gate. Actual browser rendering,
orbit, layout, keyboard/AT, runtime performance and anatomical/clinical approval
remain unverified. Historical r01 static evidence is not a fresh r03 rendering:
[retained multiview](../../../reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/display/final-multiview.webp).

The reviewed helper, source-bound record, compact fixtures and original attribution
remain. Historical r01 media are not fresh r03 evidence. No optical, whole-eye or
new anatomical validity claim is made.
