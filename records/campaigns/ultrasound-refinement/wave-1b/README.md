# Wave 1B · s1233 right kidney

The long-axis right-kidney chapter of the local abdominal survey opens a registered s1233 teaching exemplar at its saved stop. The candidate Gallery carries the matched evidence and exact `anatomy:s1233:kidney-right@r01:kidney-right` download. **Lead decision · Adopt r01 for orientation at frame 12. Hold the continuous-tissue caliper teaching claim. Wave 2 was held at Wave 1B close. [Wave 2A](../wave-2a/README.md) records the subsequent abdominal exterior decisions.** Final scores for locating both poles and relating the medial recess to the scan are **4/3/3/4** for fidelity, form, readability and economy. The ultrasound workbench's four-top-score qualification remains unearned.

## Independent review of the exact previous export

The lead examined the previous standalone sweep mesh (`58d9a1d8…`, 23,156 triangles) and r01 (`1b6ac9ee…`, 4,800 triangles) under identical clay lighting, scale and cameras, then opened each at the same saved sweep pose and tested the currently delivered survey chapter. The previous chapter itself used the 107 mm schematic. The frozen CT half-label surface in the original three-way plate is a separate anatomical reference. [Exact previous vs r01, including frame 12](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/previous-vs-r01.webp)

- **Fidelity 4.** Both renal poles and the deep medial indentation persist on the protected cuts. At frame 12 the previous mesh spans 103.5 mm, r01 spans 103.3 mm, and the reference spans 104.3 mm. The geometry improvement is in surface finish and economy. Both mesh spans already agreed closely with the reference.
- **Form 3.** The previous inferior surface breaks into stacked horizontal bands. They largely disappear on r01. The lower outer face still has a shallow diagonal furrow and uneven relief. Their anatomical significance is open.
- **Readability 3.** I could trace the upper and lower ends and find the medial opening on the reverse oblique view. The registered overlay made its extent clear on the grayscale scan. The default oblique scene shows the probe, overlying liver and part of the kidney, but the recess is hard to identify there. This limits the builder's proposed readability score of 4.
- **Economy 4.** The reimported r01 uses 79% fewer bytes and triangles than the previous delivery. Across the recorded 24 directions its projected silhouette stayed within 0.71 pixel of the pre-decimation surface at the declared teaching zoom.

The two standalone players served the pinned previous and r01 mesh bytes, identical poses, and byte-identical frame-12 B-mode and tissue images. The current chapter adds a labeled span. About 63 mm of its straight line lies in the recess outside the kidney label. Its endpoints can teach exterior orientation. A continuous-tissue chord needs a separately evidenced acquisition. The lead was independent of the builder and had seen its proposed scores before inspecting the exact pair.

To reproduce the new plate, serve the previous and current deliveries from separate loopback roots. Run [compare-players.mjs](compare-players.mjs) with those URLs and a scratch directory. Run [render_clay.py](render_clay.py) through Blender with the frozen reference NPZ, r01 mesh, `SCRATCH/clay` and `--previous PREVIOUS_MESH`. Run [comparison_plate.py](comparison_plate.py) with `SCRATCH` and an output directory. The [review record](../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/reviews.json) pins the resulting WebP. The lead rebuilt the local Gallery, checked the displayed disposition and readability score, decoded and verified all four witnesses, and downloaded the exact mesh with the study server stopped. A fresh focused chapter run also reproduced the original final measurement receipt byte for byte.

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

- Build the kidney with the [asset recipe](../../../../models/kidney_right_s1233/README.md#replay). Recreate the frozen arrays with [Wave 1 freeze](../wave-1/README.md#reproduce-the-trial) and keep the sealed Wave 1 delivery with the previous sweep mesh.
- Rebuild the standalone track with `build_abdomen.py "$S1233_CASE" "$STUDY_STAGE/sweeps" --track kidney-right` into a complete staging tree. Assemble with `assemble_tours.py "$STUDY_STAGE" --delivery "$STUDY_DELIVERY"`. For fresh live evidence, serve the candidate and frozen baseline on loopback and run `node records/campaigns/ultrasound-refinement/wave-1b/player.mjs "$STUDY_URL" "$BASELINE_URL" "$CAPTURES"` using the approved disposable Chrome harness. The command writes `live-identity.json` beside the captures directory.
- Build the [Gallery candidate](../../../../sites/anatomy-gallery/README.md#restore-and-build-locally) and stop the study server. Run [gallery.mjs](gallery.mjs) with the Gallery preview URL and a scratch screenshot path. Use the project's disposable Chrome harness settings.

Run one command from the repository root with the pinned [sweep replay environment](../../../../experiments/ultrasound-sweep/README.md#replay). The paths below use the retained local inputs. Choose a fresh output directory and use the output from `player.mjs` to bind a new browser run.

```sh
PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}" \
  python3.12 records/campaigns/ultrasound-refinement/wave-1b/measure.py \
  .artifacts/us-wave1/reference.npz .artifacts/us-wave1b/replay \
  .artifacts/us-wave1b/receipt-replay \
  --baseline-delivery .artifacts/us-wave1/delivery \
  --study-delivery .artifacts/us-wave1b/delivery \
  --live-identity .artifacts/us-wave1b/live-identity.json
```

[measure.py](measure.py) checks the reimported mesh and the delivered pose, skin contact and authored calipers. It derives `previousSweep` from the earlier mesh and checks `liveBrowser` against the actual delivered files and the focused browser receipt. It writes `sections.npz` and the final `measurements.json` only after its SHA-256 matches the review pin. [render_clay.py](render_clay.py) takes the frozen NPZ, actual packed mesh and scratch output directory through headless Blender. [witnesses.py](witnesses.py) uses the sections, clay renders and browser captures.

| Check | Basis |
| --- | --- |
| Each direction globally and in three protected planes | The Wave 0 packet freezes a p95 limit of 1.5 mm and a maximum of 3 mm. Each protected chord must be within 1.5 mm of its frozen reference. |
| Saved frame and mesh integrity | Both poles must stay in the sector and raster. The first skin hit must be within 1.5 mm of the saved contact. Require a single closed outward shell and a turning-silhouette departure of at most one teaching pixel. |
| Wave 1B cap contours | Apply the same section distance limits to the superior and inferior 5 mm cap regions as a retrospective check. Wave 1A's original point-extremum failure remains recorded. Principal-axis span, lateral sections and length outside the outline are measured context for lead review. |
| Existing Wave 1B recipe checks | The verifier retains the ±3% volume limit and 2,000–5,000 triangle band already used by this replay. |

## Verification results

- **AssetKit and replay** · Two clean replays produced the same packed SHA-256. Sync verified the recorded bytes, hydrated check-port accepted the exact export, and native show, impact and both consumer bundles resolved it. Validate, economy, review check, Ruff, ty and the AssetKit tests passed.
- **Receipt replay** · Using the frozen arrays, saved replay mesh and focused Chrome receipt, the final JSON reproduced byte for byte. A disposable copy shortened 2% along the frozen saved chord failed the −1.5 mm plane chord gate with a 2.71 mm error and produced no receipt.
- **Ultrasound study** · The complete staging tree assembled. The organ playable, case data, case geometry and compact assembly checks passed. Disposable Chrome exercised all four abdomen exam tours and study playback. The focused check confirmed chapter isolation, saved calipers and exact served scan bytes, 3D recovery state with a missing or valid-size corrupt mesh, and sibling-edit review currency.
- **Gallery and repository** · The pinned candidate built offline. With the study server stopped, Chrome opened the card, decoded and hashed all four witnesses, reloaded the exact revision and downloaded the verified mesh. Repository offline and hydrated payload-integrity gates passed.

The study-stage files, replay work, diagnostic sculpts and large captures are under ignored `.artifacts/us-wave1b/`. Keep the exact mesh, source recipe and four pinned WebPs with their active readers. The Gallery rehearsal is local.
