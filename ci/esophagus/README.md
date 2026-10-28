# Issue 102 target-viewer extension (WIP)

This isolated module extends the reviewed `ci/glb_runtime_probe.py` and `.mjs`
architecture. It is not wired into that harness yet. No browser was launched,
protected workflow dispatched, model staged, or Site published for this change.
Parent independent review is required before shared integration, merge or dispatch.

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
this change does not add it. **Remote baseline availability is unresolved.**
A future authorized run must obtain exactly the pinned baseline through the
reviewed source path or stop inconclusive. Local bytes do not prove remote input
availability. No new public payload staging or LFS transport is proposed.

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
restore must reproduce the transverse framebuffer exactly. Grayscale comes
from actual lit `readPixels`, with explicit display-luma coefficients, followed
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
size gates. Runtime evidence remains unrun until the reviewed harness invokes
this module and all 18 captures pass. Source attribution is retained from the
canonical package and PR #108 labels. Geometry, anatomical/clinical acceptance,
visual acceptance, software CI runtime, supported product viewer and publication
remain separate gates. This probe does not verify native UI or the whole Site.

## Minimal integration proposal (not applied)

See `integration.patch` for the bounded shared wiring against merged
`55b81bb39e17a5ec12b87eefc4f1af2745f68c8e`. It is review material only, intentionally
not applied: another worker owns the shared lymph/runtime paths. Parent must
reconcile it with that worker's changes and independently review the final diff.
The patch adds this exact baseline as an eighth bounded download, reconstructs
only inside the runner, registers the candidate for same-origin serving, appends
18 frame IDs and dispatches esophagus frames to this verifier. Existing input
hashes, 10 MiB download / 4 MiB POST limits and security gates stay intact.

Sparse checkout needs the two existing esophagus replay inputs. Provenance must
include this module, fixture and both replay inputs. No protected dispatch is
part of this PR. A passing offline suite is not media-byte, actual-pixel,
remote-availability or runtime evidence; keep issue #102 open.
