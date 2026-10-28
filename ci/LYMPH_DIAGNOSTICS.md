# Bounded lymph normal/facing diagnostics (#101)

This follow-up extends the 21-state probe reviewed at `55b81bb`. It does not
reinterpret run 40624597742 as proof of all normal/winding correctness. That run
passed its finite-normal, framebuffer/display and state checks; observed
back-normal speckling occurred in both source and candidate.

The new probe retains those checks and uses exactly four fixed source-bound
cameras: front `[1,.5,2]`, right `[2,.5,-1]`, reverse `[-1,-.5,-2]`, left
`[-2,.5,1]`. Each samples source and candidate with front/back normal materials.
These are model-coordinate labels, not anatomical orientation claims. There are
37 frames total (21 existing + 12 orbit diagnostics + 4 mutation/restoration).

Loaded referenced normals receive per-mesh finite, near-zero (`length <= 1e-6`)
and nonunit (`abs(length - 1) > 1e-3`) counts, min/max lengths, triangle counts,
exact degeneracy counts, and normal corners opposed to oriented triangles.
The 1e-3 tolerance allows float export/loading noise; it is a technical validity
bound, not a source-direction fidelity or medical criterion. All loaded normal
components still must be finite. Source zero/nonunit values remain observations;
the compact candidate must have no invalid referenced normals. Opposed corners
and degeneracies are descriptive in both: smoothing, folded/open surfaces or
source duplicate faces can produce them. They do not identify anatomical outward
orientation or diagnose the cause of pixel speckling.

Each diagnostic frame records actual final-draw WebGL culling enabled/mode/front
face. The host checks back-face culling, consistent front/back switching, the
fixed camera directions and common source bounds/scale. This samples renderer
state; it does not attest every draw call or all possible views.

Two genuine negative controls operate on cloned attributes of the loaded compact
candidate: negate normals, then separately reverse triangle indices. They do not
edit RGB arrays or exported models. Each must change at least 100 pixels (maximum
RGB channel difference > 2) against the original front-normal frame, checked
independently by the host. This is a coarse sensitivity floor, not an image-quality
threshold. Restoring the original attribute objects must produce zero changed
pixels at the existing tolerance. A no-op mutation or imperfect restore fails.
All control frames retain GL, visibility, transform and actual display checks.
The ordinary candidate SHA identifies the input; control frames are explicitly
labelled as deliberately mutated in memory.

After a successful reviewed run, `lymph-diagnostics.svg` has 20 labelled tiles
(four views × source/candidate × front/back, then four controls/restorations).
`lymph-diagnostics.json` binds raw readback and thumbnail hashes, normal reports,
independent control counts, attribution, scope and sheet hash. Original full
canvas/display captures and receipts remain available for pixel checks. No new
model files are uploaded. Existing source/candidate/intermediate hashes, 10 MiB
network cap, temporary model storage and manual main-only workflow remain intact.

Shared source/candidate artifacts suggest an inherited property or shared renderer
behavior; they do not distinguish those explanations by themselves. Compare mesh
diagnostics and actual paired pixels before calling an anomaly a regression.
Source vascular identity remains unresolved. Technical validity, sampled software
runtime behavior, teaching/visual disposition and anatomical/clinical acceptance
remain separate gates. No model/Site publication or canonical promotion.

Validation before dispatch: `python3 tools/verify.py offline`,
`node --test tests/runtime_receipts/test_lymph_diagnostics.mjs`, and JavaScript
syntax checks. Python tests reject invalid receipts, wrong culling/cameras,
no-op controls and imperfect restoration; JavaScript tests exercise normal audit
and attribute/index mutations. These CPU tests do **not** establish real renderer
sensitivity. Keep the PR draft for independent parent diff review; do not dispatch
the modified runtime until that review and authorization are complete.
