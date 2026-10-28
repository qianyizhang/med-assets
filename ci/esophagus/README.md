# Issue 102 target-viewer extension (WIP)

This isolated module extends the reviewed `ci/glb_runtime_probe.py` and `.mjs`
architecture, integrated against PR #111 merge
`f082ed38af36bedcbbb425272eb5252e725c57f7`. Its 18 states follow the existing
37 lymph/heart states, for 55 total. The subsequent combined run failed at anchor
3; see the repair record below. This repair and its local CPU regression launch no
browser and dispatch no protected workflow. Parent independent review is required
before merge or rerun; no model or Site publication is included.

## Verified input and replay

The already-hydrated local baseline was accessible and independently hashed:
201,328 bytes, `e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5`.
The merged PR #106 replay reproduced the 201,344-byte candidate
`c7ec6420edbd62f94b85610e1c51f6fa4dd31dc008248c19a9731ac5cef0c311`.
This module independently checks five mesh/material/number mappings, 7,700
triangles, unchanged non-color JSON and byte-identical BIN
`53fbd63b3632950d18da9edbf6293489cab43a2aa529eac7113b809921680701`.

The immutable existing GitHub media URL in `fixture.json` uses an already
allowlisted runtime host, but the 2026-10-28 read-only request failed at the
execution environment proxy: `Tunnel connection failed: 403 Forbidden`.
No payload was returned, no retry or alternate route was attempted. The existing
baseline Site in the transport manifest uses a host outside the runtime allowlist;
this change does not add it. The parent independently verified that run
40633821427 subsequently downloaded and reconstructed the exact pinned inputs
on its Actions runner. The earlier local proxy restriction remains; no denied
source download was retried. A future authorized run must still verify exact
input bytes or stop inconclusive. No new public staging or LFS transport is proposed.

Local technical replay (new output directory only):

```sh
python3 ci/esophagus/probe.py --input /path/to/exact-baseline.glb --output /tmp/esophagus-NEW
python3 -m unittest discover -s tests -p test_esophagus_runtime.py -v
node --check ci/esophagus/probe.mjs
python3 tools/verify.py offline
```

## Runtime contract and evidence

`runEsophagus` receives the existing Three r180 renderer, GLTFLoader, scene,
camera, check and snapshot functions, plus this fixture. It changes no browser
launch, download, CSP, origin, POST, timeout, security or provenance policy.
The module exercises 18 deterministic API states: baseline/candidate oblique,
transverse and five isolated layers each; candidate EN and 中文 numbered
grayscale; adventitia hidden and restored. The loaded materials retain their
exported double-sided flag, metalness, roughness and linear RGBA. Numbered
transverse anchors must raycast to the corresponding loaded compartment.

Candidate and baseline isolated-layer frames must differ in actual pixels;
restoration requires zero pixels whose maximum RGB channel difference exceeds
2 on the 8-bit scale against the transverse framebuffer. This permits differences
of up to 2 per channel; it is tolerance-bounded restoration, not byte identity.
Grayscale comes from actual lit `readPixels`, with explicit display-luma coefficients, followed
by neutral numbered badges; it is not inferred from JSON colors. The server
independently validates grayscale pixels outside bounded badge regions and
captures the visible Xvfb display, retaining the reviewed >=98% match within
3 channel levels. The full display includes the bilingual legend, candidate
notice, context and source attribution. DOM string and bounds checks cannot
certify Chinese font glyphs or number legibility: independent actual-pixel review
of both full display images remains mandatory. No accessibility pass is claimed.

`validate_frame` alone is a semantic/pixel contract, not a runtime pass.
`capture_snapshot` adds actual display matching using the existing XWD/PNG
helpers. It must be reached through the shared global sequence, origin and
size gates. Full esophagus runtime verification remains incomplete until all 18
captures pass; the failed run completed only its first 14 esophagus captures. Source attribution is retained from the
canonical package and PR #108 labels. Geometry, anatomical/clinical acceptance,
visual acceptance, software CI runtime, supported product viewer and publication
remain separate gates. This probe does not verify native UI or the whole Site.

## Integrated shared wiring

The shared diff adds the exact baseline as an eighth bounded download, reconstructs the candidate only
inside the temporary runner directory, serves it through the existing same-origin
file map, appends 18 frame IDs, and routes only those frames to this verifier after
the global sequence check. The original 37-state prefix, lymph diagnostics imports,
normal controls, file-map entry, provenance and completion fields are retained.

Sparse checkout includes the existing `tests/esophagus_wall` replay directory.
Provenance includes this module, fixture and both replay inputs. The original
seven resource records and fixture file remain unchanged; 10 MiB download and
4 MiB POST limits, host allowlist, source hashes, manual/main-only dispatch,
read-only token, pinned actions, time limits and three-day retention are unchanged.
The workflow does not upload temporary GLBs. No protected dispatch is part of this
PR. A passing offline suite is not media-byte, actual-pixel, remote-availability
or runtime evidence; keep issue #102 open.

## Integrated validation — 2026-10-28

- The integrated temporary reconstruction reproduced the same 201,328-byte
  baseline and 201,344-byte candidate identities, five meshes and 7,700 triangles.
  Existing output and corrupted baseline checks remain in place; temporary model
  files were removed when the local check ended.
- 18 esophagus contract/negative tests passed. These include preserved 37+18
  ordering, sequence-gated dispatch, retained lymph diagnostics, original input
  records, corrupt reconstructed candidate rejection, all five isolated-layer
  pixel comparisons, grayscale derivation and badge/anchor checks, labels and
  display mismatch. Python restoration accepts channel differences of ±2 and
  rejects ±3; the unchanged shared JavaScript comparison was checked at the same
  boundaries without running a browser.
- Full offline gate: 146 tests, 25 transport manifests, 25 foundation records,
  591 import references and 673 LFS pointer identities passed. The 18-test
  esophagus suite is also required by the offline minimum-count guard.
- The existing four lymph JavaScript normal/winding tests passed. Python
  compilation, shared/module JavaScript syntax and whole-branch whitespace
  checks passed. Runtime and Chinese-glyph acceptance remain unrun.

Remaining: parent review of the integrated diff, verified remote baseline input,
authorized protected software-CI execution, independent review of captured
numbers/EN/中文 glyphs and palette discrimination, and any separate supported
product-viewer gate. This PR stays draft.

## Anchor repair after run 40633821427

The combined run on `dc5d46c78ccce6f429c7fb4f4313425dee977761` stopped after
51/55 captures at the anchor assertion, before grayscale/EN/中文 and hide/restore.
The retained run is a failure, not a full acceptance. Job logs and artifact
metadata were read through the GitHub connector. The connector supplied artifact
12792368383 (10,441,486 bytes; ZIP SHA-256
`7d190fb05e5a03c5908d39b309df1ed3c4b5f89a2918eec615fbb3817087891c`), but transferring
that ZIP to this executor was blocked by its proxy with HTTP 403. No bytes were
received and no transfer retry or alternate route was attempted. The 51-capture
localization was supplied by the parent's independent artifact review.

A local regression using the exact baseline/candidate and pinned Three r180
GLTFLoader reproduced anchor 3's miss. The other four anchors hit their expected
object UUIDs; all five objects were visible and double-sided. Anchor 3's continuous
ray at `x=5.51091059616309e-19`, `z=-0.009000000000000001` lies on the cap's
triangulation seam and returns zero intersections. This is a subpixel ray/edge
numerical failure, not evidence of malformed anatomy or a missing rasterized
compartment. The parent separately verified all five projected pixels are inside
the correct isolated rendered regions.

The repaired check casts through the center of the already-selected display
pixel. Anchor positions and projected pixels stay unchanged, including anchor 3
at `[256,116]`. Its ray now hits the original inner-circular mesh at distance
`0.27749999821186067`, face 767. The exact hit-object identity assertion remains;
wrong-compartment and hidden-object negative controls must fail. Failure messages
now retain anchor ID, expected and actual name/UUID/visibility/material side,
hit distance/point/face, world/NDC/pixel coordinates, ray and camera position.
No mesh, material, source hash, visibility state or pixel tolerance is repaired.

The earlier offline tests checked Python evidence contracts and fabricated
receipts; they never loaded the GLB and exercised Three's projection/raycast.
The new regression closes that specific gap with six real-loader CPU cases:
original failure and repaired mapping on both pinned exports, wrong-compartment
rejection with diagnostics, and hidden-compartment rejection. It also checks
unchanged loaded geometry arrays. The local runner verifies all five reviewed
Three files by size/SHA-256 before import, rebuilds the exact palette candidate
in temporary storage, and has no network path:

```sh
python3 tests/runtime_receipts/run_esophagus_anchor_regression.py \
  --vendor-root /path/to/verified/three/vendor \
  --input /path/to/exact-baseline.glb
```

Missing dependencies fail; nothing is skipped. Local selection for this change:
these six actual-loader tests, the 18 existing esophagus contract/negative tests,
JavaScript syntax, and the repository's lean offline integrity checks. The
unrelated model builds are outside scope. Full rendered grayscale/label/display
validation remains blocked by the missing local browser stack and Actions-only
entrypoint; see [the separate local-mode review](LOCAL_RUNTIME_REVIEW.md).
No protected rerun or heavier web CI is part of this repair. Keep WIP until the
required local display scope is resolved and the parent reviews the change.
