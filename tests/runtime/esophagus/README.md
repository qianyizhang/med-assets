# Esophagus runtime probe · issue 102

- **Goal** · Verify the exact palette candidate in the guarded Three r180 software renderer. [Fixture and source identities](fixture.json).
- **Current evidence** · Pinned-byte reconstruction and local real-loader CPU anchor repair. Full display, Chinese glyphs and supported product-viewer acceptance remain unverified.
- **Guard** · [Main-only runtime workflow](../../../.github/workflows/firefox-glb-runtime.yml). Keep download/origin, sequence, size, timeout and sandbox checks. [Local display proposal](#local-display-proposal).

## Verified input and replay

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Baseline | 201,328 | `e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5` |
| Replayed candidate | 201,344 | `c7ec6420edbd62f94b85610e1c51f6fa4dd31dc008248c19a9731ac5cef0c311` |
| Shared BIN | | `53fbd63b3632950d18da9edbf6293489cab43a2aa529eac7113b809921680701` |

- **Replay outcome** · Five mesh/material/number mappings, 7,700 triangles, unchanged non-color JSON and identical BIN. Existing-output and corrupted-input cases fail closed.
- **Source access** · Local proxy returned HTTP 403 on 2026-10-28. Actions run 40633821427 downloaded and reconstructed the pinned input. Local access and any future run require their own evidence.

```sh
python3 tests/runtime/esophagus/probe.py --input "$baseline_glb" --output "$fresh_output"
python3 -m unittest discover -s tests -p test_esophagus_runtime.py -v
python3 tests/runtime_receipts/run_esophagus_anchor_regression.py \
  --vendor-root "$pinned_three_vendor" --input "$baseline_glb"
```

## Runtime contract and evidence

| Gate | Acceptance |
| --- | --- |
| Shared sequence | Retain the original 37 heart/lymph states and append all 18 esophagus states. Temporary replay and same-origin serving. Shared global sequence gates every capture. |
| Esophagus frames | Baseline/candidate oblique, transverse and five isolated layers each. Candidate EN/中文 numbered grayscale and adventitia hide/restore. Preserve actual exported material properties. |
| Frame behavior | Isolated views differ in actual pixels. Restoration error is ≤2 per RGB channel. Grayscale comes from lit framebuffer luminance. Numbered anchors hit the matching loaded compartment. |
| Visible display | Grayscale validation outside badges, XWD visible-display match ≥98% within 3 channel levels, and independent review of numbers, palette discrimination and EN/中文 glyphs in full captures. |
| Scope | Semantic/CPU checks cover specific contracts. Full software runtime requires all captures. Intended-viewer behavior, accessibility, anatomy and publication have independent gates. |

## Integrated validation — 2026-10-28

- **Base** · PR #111 merge `f082ed38af36bedcbbb425272eb5252e725c57f7`. Pinned temporary reconstruction, 18 contract/negative cases, four lymph normal/winding cases and the offline gate passed locally.
- **Boundaries checked** · 37+18 order, sequence dispatch, lymph negatives, source identity, corrupt candidate rejection, five isolated comparisons, grayscale, badges/anchors, labels and display mismatch. Restoration accepted ±2 and rejected ±3.

## Anchor repair after run 40633821427

- **Failed runtime** · [Run 40633821427](https://github.com/qianyizhang/med-assets/actions/runs/40633821427) at `dc5d46c78ccce6f429c7fb4f4313425dee977761` reached 51/55 captures before anchor 3. Grayscale, bilingual and hide/restore captures remained incomplete.
- **Evidence access** · Artifact `12792368383`, 10,441,486 bytes, SHA-256 `7d190fb05e5a03c5908d39b309df1ed3c4b5f89a2918eec615fbb3817087891c`. Local proxy blocked ZIP transfer. Independent review supplied failure localization and verified each anchor pixel inside the correct isolated region.
- **Cause** · Continuous anchor 3 ray landed on a tessellation seam with zero intersections. Other four rays hit their expected visible double-sided objects.
- **Repair** · Cast through the chosen display pixel center. Anchor 3 stays at `[256,116]` and hits inner-circular face 767 at distance `0.27749999821186067`. Preserve source, geometry, material, state and pixel tolerances. Keep exact hit-object checks and camera/ray/UUID diagnostics.
- **Local retest** · Six CPU cases with both pinned GLBs and five size/hash-pinned Three files. Reproduces the old miss, verifies repaired mapping and unchanged geometry, rejects hidden or wrong-compartment hits.
- **Completion gap** · Independently review authorized full display evidence and any applicable supported product viewer.

## Local display proposal

- **Status** · Future local mode requires review. The existing probe requires the guarded Actions entry point. The inspected unprivileged Linux executor lacked packaged Firefox, Xvfb and an active display.
- **Prerequisites** · Reviewed Firefox/Xvfb stack, package and syspref provenance, readable policies, required fonts and a working unprivileged sandbox. Keep browser/profile isolation and warning checks.
- **Acceptance** · An explicitly approved local entry point verifies already-present pinned public inputs by size and hash, reconstructs in temporary storage and uses the same origin/CSP, limits, WebGL readback, XWD comparison and bounded receipt verifier. Retain failure receipts.
- **Coverage** · All 18 esophagus captures, including live anchors, grayscale, bilingual legends and hide/restore. The 55-state shared probe covers wider changes and lymph negatives. Each bounded mode needs its own expected sequence and verdict.
