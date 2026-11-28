# Wave 1 · Right-kidney long axis

**Proposed disposition · Hold pending lead review.** The existing s1233 surface rendered both poles at frame 12. Its superior and inferior extrema each moved about 3 mm from the frozen half-label endpoints, above the 1.5 mm limit. The survey still teaches the 107 mm schematic measurement. [Wave 0 brief](../wave-0/right-kidney-brief.md)

![Gold half-label and cyan mesh cuts on the saved plane and the two parallel planes](protected-planes.webp)

The saved half-label chord is **104.3 mm**. Both endpoints fall inside the 133 mm sector. About **62 mm** of the straight line lies outside the label within the medial recess visible in this section. The corresponding mesh-extrema chord is **103.5 mm**. The 3 mm shifts are predominantly along the contour. The outlines stay close and the poles remain visible, so the evidence does not justify a local surface refinement. The lead can judge the suitability of this plane and these landmarks for the named teaching task. [Matched surface views](matched-surfaces.webp) · [Live frame 12](live-frame-12.webp)

## Measurements

Distances are in millimetres. The left and right values in each distance cell are half-label to mesh and mesh to half-label. The positions of both directional maxima are recorded in RAS millimetres. [Frozen reference](reference.json) · [Measurements](measurements.json)

| Region | p95 | Maximum | Superior / inferior pole shift | Chord error |
| --- | ---: | ---: | ---: | ---: |
| Whole surface | 0.62 / 0.55 | 1.46 / 1.07 | | |
| −1.5 mm | 0.66 / 0.60 | 0.94 / 0.89 | 3.00 / 3.00 | 0.57 |
| Saved plane | 0.61 / 0.54 | 1.21 / 0.82 | 3.00 / 3.02 | 0.83 |
| +1.5 mm | 0.66 / 0.54 | 1.42 / 0.88 | 3.00 / 3.00 | 0.57 |
| Frozen limits | 1.50 | 3.00 | 1.50 each | 1.50 |

- The reference is an unsmoothed 0.5 isosurface from the pinned mask on the s1233 voxel grid. The pole markers use the superior and inferior RAS extremes of the largest closed contour. The script picks the vertex nearest the midpoint if an extremum is flat. All three CT sections and the raw reference mesh were frozen before candidate evaluation.
- Source sampling uses deterministic lattices at 0.5 mm or finer. Distances are to the nearest triangle globally and nearest line segment in each plane. The packed mesh has one closed, consistently oriented component with Euler characteristic 2, zero degenerate triangles, and zero intersections between nonincident triangles. The first skin hit is less than 0.001 mm from the saved contact.
- The exact mesh is 416,840 bytes and 23,156 triangles. Fresh replay reproduced all 105 files in the stage sweep. The compact assembly had zero mesh or scan byte delta. Its two changed files are the workbench review readers. [Replay and evidence identities](receipt.json)
- The disposable Chrome preview mounted the s1233 standalone player at the exact normal survey chapter and frame. Its calipers reproject the frozen endpoints at the source raster scale. The mesh, poses, B-mode and overlay had the expected served identities. Other routes stayed on their own acquisitions. [Served paths and identities](live-identity.json)

## Verification

Tested locally on the Wave 1 diff from `6265fcdf`, with the hydrated repository, sealed Wave 0 stage, Python 3.12, Node 24 and Chrome for Testing 158. Full command output is retained locally under `.artifacts/us-wave1/`.

| Gate | Result |
| --- | --- |
| Fresh `build_abdomen.py … --track kidney-right` | `kidney-right: fitted-atlas, maximum incoming-ray error 0.000 mm`. The staged and rebuilt files matched. |
| `verify_assembly.py` | `Compact delivery and 46 independent assembly failure paths passed.` The added chapter fixture also checks sibling stability and invalidation after mesh, placement and pose edits, plus missing and corrupt files. |
| `test-playable.mjs` and `verify_cases.py` | Organ playable passed. Worked-case replay, SVG parsing, family coverage and invalid-input checks passed. |
| `verify-case-geometry.mjs` | Passed organ, vascular, pregnancy and echo pose checks. Largest sampled organ contact residual was 1.14 mm. |
| `verify-case-tours.mjs` | `3 canonical exam tours, 45 sections, 1125 committed frames passed.` |
| `verify_playback.mjs` | `Camera presets, playback layout, 28 sweep routes, and asset recovery passed. Maximum shift: 0 px.` |
| Targeted Chrome preview | Loaded frame 12 and scrubbed frames 11–13. Missing and corrupt mesh tests retained B-mode and showed the unavailable exemplar state with the 107 mm schematic fallback. A sibling edit preserved workbench currency. Changed mesh bytes or placement made it prior. |
| Source input grid | Original mask bytes paired with an affine shifted 1.5 mm were rejected with `Unexpected grid: kidney_right.nii.gz`. |
| AssetKit | `validate` returned `status: ok` and no warnings. `economy` passed. `review check` validated 130 accepted assessments. Lint, format, types and 81 tests passed. Read-only `sync` and hydrated `check-port`, native `show`, `impact` and `bundle` passed with the existing s1233 liver export as the control. Kidney admission gates require a lead-approved export and consumer pin. |
| Gallery | No Gallery files changed. The adopted progress-card and built Gallery check are outside this held disposition. |
| Repository offline | `PASS offline: 465 Python tests; 4 Gallery Node suites; accepted teaching, maintained register and scorecard; 26 transport manifests; 25 foundation records; 390 import references (25 documented updates); 1710 LFS pointer identities.` |
| Repository hydrated payload integrity | `PASS payload-integrity: 1710 local LFS files / 1157436815 bytes, 25 foundation records, 13 package checks. No dental suite, reconstruction, visual/anatomy/runtime or remote-availability claim.` |

The frozen reference, measurements and two rendered comparison WebPs also reproduced byte for byte from a fresh scratch directory. The live screenshot composite binds the captured WebP to this run's evidence receipt.

## Reproduce the trial

Use the source case and versions in the [sweep replay guide](../../../../experiments/ultrasound-sweep/README.md#replay). The `measure.py freeze` command takes the s1233 case directory, sealed compact Wave 0 delivery and a fresh scratch directory. Put `experiments/ultrasound-sweep` on `PYTHONPATH` for the owning recipe imports. Run `measure.py evaluate` with the same arguments to compare the exact mesh and exercise the grid guard. `witnesses.py` takes scratch, delivery and a witness output directory.

For the disposable live preview, assemble the compact study, serve it on loopback and run `node player.mjs STUDY_URL SCRATCH WAVE0_STAGE` in the approved Chrome for Testing environment. The script injects the preview in its disposable browser context. Production routes serve the schematic at the saved survey stop. The witness script uses the PNG crops from that browser run to produce the final WebP.

The CT and kidney label come from TotalSegmentator v2.0.1, case s1233, by Jakob Wasserthal and contributors at University Hospital Basel. Source credit and terms travel with these derived witness images. The fitted exterior uses BodyParts3D. The B-mode is simulated and the medial recess is a contour feature. The trial does not characterize cortex or sinus segmentation, disease, or clinical measurement accuracy. [TotalSegmentator notices](../../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md) · [BodyParts3D exterior](../../../../models/skin/exports/bp3d-envelope-r01/README.md)

Keep fresh replay trees, the raw reference surface and captures under ignored `.artifacts/us-wave1/`. The tracked WebPs are the decisive witnesses for the held trial. Review scratch retention by 2026-12-28.
