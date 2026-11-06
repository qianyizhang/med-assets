# Eye anterior-segment inspection (#99)

A bounded exact-source consumer recipe for the v47 gallery. The isolated r03
editorial cutaway gains whole/cutaway selection, shared camera/zoom, bilingual
limitations and guarded failure/retry. Whole mode is a seven-component study,
not a complete eye. No geometry, materials, model manifest or review gate is
changed; the separate whole-body `draft_eyes` entry remains unchanged.

Run `python3 gallery/eye-inspection/r01/apply.py REVIEW_DIRECTORY` against a
fresh authorized source copy. All ten input identities, new-module absence,
the isolated record and all six output identities are checked before writes.
Unknown source revisions, duplicate records and reapplication are refused.
The record is appended without rewriting prior records semantically. Existing
lifecycle, context-loss, knee, camera reset and supplement-routing source are
retained. Applying the recipe does not publish anything.

## Model delivery remains separate

The unchanged immutable manifest serves whole r01 only when selected. Cutaway
uses the exact same-origin path in `record.json`; an authorized delivery must
separately supply its existing 6,139,756-byte gzip (SHA-256
`d57b6728b35179c85a6b22019566db5890e8f50ee386d96e987846a8e6939a84`).
Decoded r03 is 12,061,144 bytes, SHA-256
`1fe679f0f2386f2f19cf5c8ffebaffa0bc6ec0d9bd4fd0f97bd32bdc873905c1`.
No model or duplicate image payload is retained by this recipe.

## Checks and limits

- `python3 -m unittest discover -s tests -p test_eye_inspection.py`: six required
  Python cases including 14 actual-source Node checks, no media/network.
- `python3 tests/eye_inspection/run.py --whole-fixture EXACT_WHOLE_GZIP` adds
  three actual viewer-composition cases using a separately retained pinned
  whole fixture. This is CPU/DOM/renderer-double evidence, not browser pixels.
- The original reviewed eye test sources are retained; the offline runner
  explicitly selects 14 non-payload cases. Two byte-level model cases and the
  historical Site-Git preservation case are not counted by that runner.
- Compact fixtures contain only the selected study/record and one immutable
  manifest entry. The production helper is byte-bound; the full production
  manifest is never replaced by the compact test map.

Site integration separately passed 68 Node checks, six DOM suites and a build;
repository offline checks remain a separate gate. Actual browser rendering,
orbit, layout, keyboard/AT, runtime performance and anatomical/clinical approval
remain unverified. Historical r01 static evidence is not a fresh r03 rendering:
[retained multiview](../../../reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/display/final-multiview.webp).

The output source and compact records are canonical replay inputs consumed by
the applicator and focused tests; existing shared lifecycle/contract fixtures
are reused. Source attribution and inherited omissions are preserved in the
record. No optical, whole-eye or new anatomical validity claim is made.
