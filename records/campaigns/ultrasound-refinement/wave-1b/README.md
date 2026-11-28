# Wave 1B · s1233 right kidney

The long-axis right-kidney chapter of the local abdominal survey opens a registered s1233 teaching exemplar at its saved stop. The candidate Gallery carries the matched evidence and exact `anatomy:s1233:kidney-right@r01:kidney-right` download. The review proposes fidelity 4, form 3, readability 4 and economy 4 for the named task. Lead review owns the teaching disposition and final scores.

| Evidence | Observation |
| --- | --- |
| [Matched clay views](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/matched-surfaces.webp) | The schematic has a 107 mm chord. The CT half-label surface carries 23,400 triangles. The r01 surface keeps both poles and the medial recess with 4,800 triangles. Local relief remains near the inferior outer surface. |
| [Protected CT sections](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/protected-planes.webp) | Bidirectional p95 and max are at most 0.97 and 2.69 mm globally, and 1.21 and 2.36 mm in the saved and adjacent planes. Cap contour max is 1.19 mm. |
| [Saved survey frame](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/live-frame-12.webp) | The refined calipers measure 103.3 mm at frame 12, compared with 104.3 mm from the CT half-label outline. About 63 mm of the straight chord crosses the medial hilar recess. |
| [Measurements and topology](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/measurements.json) | The reimported shell has Euler 2, outward winding, no open or nonmanifold edges, no degenerate faces, and no intersecting nonincident pairs. Enclosed volume rises 0.02%. Principal span is 105.1 mm versus 106.8 mm from CT. Full projected silhouettes differ by at most 0.71 px at 3 px/mm across 24 orthographic views. |
| [Exact export and replay](../../../../models/kidney_right_s1233/README.md) | The previous standalone sweep carried 23,156 triangles and 416,840 bytes. r01 has 4,800 triangles and 86,432 bytes, a 79% reduction on both measures. |

## Saved acquisition

Frame 12 retains the shared sweep pose and its simulated B-mode, tissue overlay and acquired comparison. A parallel plane 15 mm away gives a solid chord of about 91 mm on the source outline. Nearer sections that retain about 100 mm either cross the recess or have small additional components. A new acquisition at the lateral offset would need its own seated probe pose, field and review. At frame 12 the chapter identifies the 103.3 mm result as a pole-to-pole span across the medial hilar recess.

The survey chapter uses a separate subject for teaching. The short-axis chapters, limited-pancreas visit and obstruction simulation use their existing procedural acquisitions. The original worked plate and baseline remain available for comparison. The source label resolves the exterior and its recess. The model and simulated scan support spatial orientation.

## Build and verify

The visual baseline is `a9ec4877`, verified against the frozen Wave 1 page, schematic plate and CT reference. The branch advanced to `e091ee5b` during the task, consolidating the scan-surface guide. Wave 1B builds on that documentation commit. Its [review record](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/reviews.json) pins the witnesses, measurements, exported chapter placement and unchanged rubric.

- Build the kidney with the [asset recipe](../../../../models/kidney_right_s1233/README.md#replay). Recreate the frozen arrays with [Wave 1 freeze](../wave-1/README.md#verification). Put `experiments/ultrasound-sweep` on `PYTHONPATH` and run [measure.py](measure.py) with the frozen `reference.npz`, replay directory and fresh scratch output.
- Rebuild the standalone track with `build_abdomen.py "$S1233_CASE" "$STUDY_STAGE/sweeps" --track kidney-right` into a complete staging tree. Assemble with `assemble_tours.py "$STUDY_STAGE" --delivery "$STUDY_DELIVERY"`. For the matched live evidence, run [player.mjs](player.mjs) with candidate and baseline loopback URLs and a scratch capture directory. [render_clay.py](render_clay.py) consumes the frozen NPZ, actual packed mesh and a scratch output directory through headless Blender. [witnesses.py](witnesses.py) combines the results.
- Build the [Gallery candidate](../../../../sites/anatomy-gallery/README.md#restore-and-build-locally) and stop the study server. Run [gallery.mjs](gallery.mjs) with the Gallery preview URL and a scratch screenshot path. Use the project's disposable Chrome harness settings.

## Verification results

- **AssetKit and replay** · Two clean replays produced the same packed SHA-256. Sync verified the recorded bytes, hydrated check-port accepted the exact export, and native show, impact and both consumer bundles resolved it. Validate, economy, review check, Ruff, ty and the AssetKit tests passed.
- **Ultrasound study** · The complete staging tree assembled. The organ playable, case data, case geometry and compact assembly checks passed. Disposable Chrome exercised all four abdomen exam tours and study playback. The focused check confirmed chapter isolation, saved calipers and exact served scan bytes, 3D recovery state with a missing or valid-size corrupt mesh, and sibling-edit review currency.
- **Gallery and repository** · The pinned candidate built offline. With the study server stopped, Chrome opened the card, decoded and hashed all three witnesses, reloaded the exact revision and downloaded the verified mesh. Repository offline and hydrated payload-integrity gates passed.

The study-stage files, replay work, diagnostic sculpts and large captures are under ignored `.artifacts/us-wave1b/`. Keep the exact mesh, source recipe and three pinned WebPs with their active readers. The Gallery rehearsal is local.
