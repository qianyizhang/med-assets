# Exact camera views after orbit interaction

Private source-bound repair for [#190](https://github.com/qianyizhang/med-assets/issues/190).
The canonical viewer enables damping, then assigns a recorded pose and calls
`controls.update()`. Residual rotation and pan from the previous drag are applied
to the newly assigned pose and continue to move it on subsequent updates.

## Change

`clearPendingOrbit()` uses public controls APIs: temporarily disable damping,
call `update()` on the old pose to consume and clear pending input, then restore
the prior damping setting in `finally`. The caller subsequently imposes the same
recorded or generic camera pose as before. Only those two integration points are
added; no undocumented control fields are read or mutated. Ordinary damping and
interaction continue after reset. The transient old-pose update occurs in the
same synchronous Fit call before the requested pose is imposed; no render is
introduced between them.

Camera position/target/up/span/zoom logic, source-view visibility, transforms and
model bytes remain unchanged. Invalid source-view requests still return before
this operation. No fit-distance, framing tolerance or anatomical claim changes.

## Binding and application

The applicator accepts exactly canonical v40, or the exact lifecycle-v2 output
from the existing package. It rejects other source bytes, existing reset modules
and repeated application. Lifecycle composition also requires the exact existing
lifecycle module. Apply to an independent source copy:

```sh
python3 gallery/candidate-lifecycle/r01/apply.py PATH_TO_CANONICAL_REVIEW
python3 gallery/candidate-camera/r01/apply.py PATH_TO_REVIEW
```

The first command is optional when testing the camera patch alone. No script
fetches source, pushes, publishes or deploys a Site. Applying the older lifecycle
patch after this camera patch is intentionally rejected; the supported composition
order is explicit rather than weakening either source guard.

| Identity | SHA-256 |
| --- | --- |
| Canonical input | `9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b` |
| Camera-only output | `89c6c906a06c1765e0b25615e86d4d511dfb5d99e08685b1a85812b5259ecf8f` |
| Existing lifecycle input | `d11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e` |
| Lifecycle + camera output | `855b9555acad27bdeb29876d02e3a72216fd659ed772dfa29cd166e16ffc9dc7` |
| Camera module | `dcce015f6b0778337756ceaaa1f64aabed7e5db0137b17b62290e8bc4138be0f` |

## Evidence and replay

The retained witness is `blood_cell_study_authored__r05`, `study-front.png`, from
canonical review-data SHA-256
`a9ed5c5621899b8d99054848d7e8ef3574ffe16cb1cd0c414b6e1711522550f2`.
Its exact camera tuple is in
[`witness.json`](../../../tests/candidate_camera/witness.json); the generic Fit
bounds and node objects in the CPU test are explicitly synthetic controls fixtures.
No model geometry is loaded. Actual canonical Fit code and the actual pinned
OrbitControls mouse handlers execute through minimal DOM event doubles.

Original: no drag then Front is 0 degrees error. An 80 px horizontal drag at a
640 px control height gives 2.132765 degrees immediately after Front, rising to
40.785812 after 60 updates in the local reproduction. These are CPU camera-pose
measurements, not rendered or actual-browser evidence.

```sh
python3 -m unittest discover -s tests -p test_candidate_camera_patch.py -v
python3 tests/candidate_camera/run_cpu.py --vendor-dir PATH_TO_EXACT_VENDOR --baseline
python3 tests/candidate_camera/run_cpu.py --vendor-dir PATH_TO_EXACT_VENDOR
python3 tests/candidate_camera/run_cpu.py --vendor-dir PATH_TO_EXACT_VENDOR --lifecycle
python3 tools/verify.py offline
```

The baseline command is expected to fail (5 pass / 9 fail); both updated CPU runs
pass all 14 cases. Coverage includes no-drag, rotation/pan followed by recorded
Front or generic Fit, wheel zoom, 60 subsequent updates, repeated view changes,
normal post-reset interaction/damping, disabled damping, visibility and transforms.
The seven required offline source tests cover identity, exact two-anchor diff,
deterministic application, rejection without writes and lifecycle composition.

Vendor retention is bounded: Three module/core hashes reuse existing
`ci/glb-runtime-fixture.json`; `vendor-binding.json` pins the separately fetched
current OrbitControls bytes. No duplicate large vendor payloads are tracked.
`run_cpu.py` requires already-acquired exact files and validates every size/hash
before private staging; it downloads nothing. Upstream Three.js MIT notices remain
in staged bytes; the existing fixture pins the upstream license. CPU bare-`three`
resolution is explicitly mapped to those bytes, not borrowed from another viewer.
Actual browser import-map mapping remains unverified.

Actual browser gesture/rendering, WebGL and device integration remain unverified.
No new visual appearance, model/anatomical revision, clinical approval or Site
deployment is claimed. Existing lifecycle acceptance and its limitations remain
separate. No previous snapshots or immutable evidence were rewritten.
