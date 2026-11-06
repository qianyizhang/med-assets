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

## Current source

The camera helper and the retained `gallery/eye-inspection/r01/candidate.js`
match Site v50 source commit `51c0039a8647d10aa35e45358da353966284e8af`
exactly (read-only source comparison, 2026-11-06). The candidate's existing
`binding.json` owns its identity; no second candidate snapshot is needed.
The historical v40/lifecycle-v2 applicator has been retired. Change the owning
Site source, then refresh the retained fixture after review.

The current candidate includes lifecycle, context recovery and inspection code.
The CPU camera suite executes its actual Fit body with the pinned Three/OrbitControls
and an ineligible inspection fixture. Separate inspection suites own knee/eye
behavior. Public HTTP byte readback returned 403; source equality is not a new
live-browser, WebGL or BFCache pass.

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
python3 tools/verify.py offline
```

The baseline command is expected to fail (5 pass / 9 fail); the incorporated-source CPU run
passes all 14 cases. Coverage includes no-drag, rotation/pan followed by recorded
Front or generic Fit, wheel zoom, 60 subsequent updates, repeated view changes,
normal post-reset interaction/damping, disabled damping, visibility and transforms.
The offline source binding checks the retained candidate and camera helper.
Historical patch-application/refusal tests were retired with their applicator;
source-hash refusal remains in the CPU runner.

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
