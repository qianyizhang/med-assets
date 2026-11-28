# Ultrasound Anatomy asset refinement and qualification

**Decision · Keep the s1233 liver sweep on `r01`. Wave 0 audited all 28 sweeps and 410 exam chapters.** The [Wave 1 kidney trial](../records/campaigns/ultrasound-refinement/wave-1/README.md) proposes holding the replacement for lead review. Its pole positions exceeded the frozen tolerance. The survey still presents the 107 mm schematic. Per-chapter mesh review binding passed the sibling-edit and invalidation checks.

The campaign aims to improve anatomy where it changes what a learner can see, identify or measure in a specific sweep or exam chapter. AssetKit owns reusable 3D exports, provenance and coordinate frames. The lesson owns acquisition, display, placement, saved poses and teaching claims. The ultrasound workbench owns its ratings. Gallery presents accepted work through its own maintained surfaces.

## Local liver pretrial

The learner task was to distinguish the broad right lobe from the narrower left extension. The experiment asked whether the superior dome could lose its stepped appearance while preserving the inferior cleft. The source was the pinned TotalSegmentator s1233 liver mask on its 1.5 mm grid. The comparison used the half-label surface, three neighboring axial slices through the visible cleft, and the actual imaged sectors at liver sweep frames 12 and 13. The axial mark identifies a surface indentation. There is no separate structure label for it. [Owning package](../models/liver_s1233/README.md) · [Decision and tolerances fixed before shaping](../records/campaigns/ultrasound-refinement/pretrial/decision-before-candidate.md)

| Measurement | Active r01 | Candidate | Decision |
| --- | ---: | ---: | --- |
| Dome roughness, RMS height residual | 0.357 mm | 0.123 mm | 66% reduction, above the 20% target. Terraces softened under matched lighting. |
| Worst contour error across the three cleft slices | 1.115 mm | 1.115 mm | Both p95 and maximum held on each slice. |
| Imaged sector p95 / maximum, frame 12 | 1.590 / 7.870 mm | 1.590 / 7.870 mm | Within the relative tolerance. |
| Imaged sector p95 / maximum, frame 13 | 1.595 / 9.105 mm | 1.595 / 9.105 mm | Existing local discrepancy remains. |
| Whole surface, sampled bidirectional p95 / maximum | 0.661 / 3.236 mm | 0.872 / 3.236 mm | p95 rose 0.212 mm, within the predeclared 0.30 mm margin. |
| Newly reversed triangle normals | 0 | 42 | Failed the zero-reversal gate. Connectivity and triangle count matched. |
| Largest vertex displacement | 0 mm | 1.000008 mm | Serialized coordinates also narrowly exceeded the 1.0 mm cap. |

The original recipe reproduced the active bytes. A disposable native revision reproduced the candidate bytes and passed AssetKit identity verification. Each built player fetched its intended liver mesh once. Both decoded the B-mode and tissue overlay at frames 12 and 13 and the acquired comparison at frame 12. All 49 poses, 49 scan images and 49 tissue overlays matched across deliveries. The player samples the case CT and masks for these images. A new mesh can improve the 3D view while those images legitimately stay identical. The acquired comparison is a different case. It cannot establish millimetre agreement for s1233.

**Disposition · Keep r01 at its existing 3/3/4/4 for this task.** The failed candidate earns no new rating or consumer pin. A future attempt should first locate the reversed faces and address local folding, then repeat the same comparison. A smoother dome alone does not establish better lobe identification. The two worst section errors lie about 59 mm inside the sector and persist on the unclipped planes. Their anatomical significance is open. [Measurements, identities and matched views](../records/campaigns/ultrasound-refinement/pretrial/README.md)

## Regional pretrial baseline

At source revision `199d2836`, the local assembly from the retained regional staging tree emitted **17 standalone sweep entries, 32 case tours with 410 chapters, and 34 teaching tours including two composed tours**. The 17 are the sweeps present in this delivery. Standalone tracks supplied by other staging inputs need their own recorded inventory. Detailed geometry tracing in this pretrial covered the liver only. [Emitted sweep IDs and review audit](../records/campaigns/ultrasound-refinement/pretrial/audit.json)

| Retained review family | Authored rows | Four evidenced top scores in retained rows | Rows matching this delivery | Matching rows with four top scores |
| --- | ---: | ---: | ---: | ---: |
| CT originals | 7 | 1 | 7 | 1 |
| Echo | 1 | 0 | 1 | 0 |
| Organs | 19 | 1 | 0 | 0 |
| Vascular | 26 | 0 | 0 | 0 |
| Pregnancy | 18 | 13 | 0 | 0 |
| **Total** | **71** | **15** | **8** | **1** |

The seven original reviews match emitted mesh digests. Echo matches its family recipe. The other 63 rows retain earlier family recipe hashes. Eleven organ rows lack a readability observation. Organ and vascular reviews also list 45 and 35 additional uses respectively. Count each authored assessment once, then report uses separately. A prior review can guide inspection. A new claim requires the emitted geometry or recipe, task, witnesses and applicable rubric to agree. Refresh an observation against the current delivery before changing its fingerprint. [Review loader](../lib/med_assets/ultrasound_review.py) · [Workbench reader](../experiments/ultrasound-sweep/development/assets.js)

## Phase 0 · Audit before dispatch

The final local assembly contains 28 standalone sweeps, 32 case tours with 410 chapters, and the separate bilateral carotid survey. **All 71 authored reviews match the emitted identities.** Fifteen have four evidenced top scores, 44 are fully scored below that target, and 12 have an unrated axis. The 17-sweep pretrial matched eight reviews. Restoring the pregnancy sweeps raised that to 26. Restoring the bilateral survey brought the organ and vascular family fingerprints back into date while the 410 chapter bindings and standalone mesh digests stayed identical. The bilateral survey is a dependency of those fingerprints and adds zero standalone sweeps to this count. [Assembly and review evidence](../records/campaigns/ultrasound-refinement/wave-0/assembly.json) · [Wave 0 ledger](../records/campaigns/ultrasound-refinement/wave-0/README.md)

To repeat the audit, reconcile the expected sweep IDs with the emitted IDs: 17 regional sweeps plus 11 early, first-, mid- and late-pregnancy sweeps. Reconcile the 32 case tour IDs and their 410 chapter IDs independently. Record source revision, staging inputs, inventory digest and every missing or unexpected ID. Report a partial audit if any expected route is absent. Trace each proposed packet from the learner task through its chapter or standalone sweep, runtime geometry source, rendered part and review binding. The [abdominal](../experiments/ultrasound-sweep/development/assets-abdomen.js) and [exam](../experiments/ultrasound-sweep/development/assets-exams.js) workbench lists supply leads. Confirm each one against the current reader. The pretrial count alone cannot establish chapter coverage.

The lead owns the campaign ledger under `records/campaigns/ultrasound-refinement/`. Key each use by case and chapter (or standalone sweep), part and task. Keep the deterministic generator (`audit.mjs`), compact decision/summary ledger, assembly receipt and the full audit's SHA-256 and byte count in Git; keep multi-megabyte raw per-frame occurrence dumps in ignored `.artifacts/` per [retention](WORKFLOW.md#retention) unless a named offline reader requires the raw file directly. Retain the following independent facts so a governed mesh with a stale review and a procedural acquisition state both have clear dispositions.

| Ledger field | Record |
| --- | --- |
| Geometry and source | Actual renderer, part and source identity. Record primitive or coarse voxel explicitly, alongside case-derived mesh, reusable external mesh, other procedural geometry, volume-derived image, acquisition state and missing structure. Name the reader for each claim. One chapter may use several representations. |
| Consumer and placement | Exact native export key and emitted digest where present, or the recipe-backed reader. Record subject, coordinate frame, registration evidence and saved frame. |
| Review currency | Current, earlier identity, missing evidence or unrated. Record task, rubric, identity, observations, witnesses and any additional uses. |
| Decision and owner | Keep, refine, reuse with evidenced placement, source/rebuild, or hold. Give the blocker, owner and the observation that would resolve it. |

Before authoring, query `uv run assetkit --native-only find <structure>`, inspect `uv run assetkit gaps --prefix ultrasound:`, and check the owning workbench and actual scene. An empty gap query can coexist with declared workbench gaps. The 15 legacy sweep requirement sets describe lesson needs. Retire a projection only after its reader has an owned replacement or its owner retires the lookup. [Adapter owners and removal conditions](../records/campaigns/assetkit-migration.md#remaining-adapters-and-retirement-conditions)

## Qualification and acceptance

Use the [four-axis rubric](guides/asset-quality.md) and [ultrasound review contract](gallery/use-cases/ultrasound-anatomy.md#development-review). The workbench reserves **Qualified** for four evidenced 4/4 scores on the exact task and identity. Keep zero distinct from unrated. Gallery applies its own maintained-register target. An asset can be accurately registered, in use and still provisional.

| Axis | Evidence for the packet |
| --- | --- |
| Fidelity | Pin the reference, units, protected landmarks, crop, poses, sampling method and tolerances before generating candidates. For a spatial surface, report bidirectional p95 and maximum globally and through each protected section. Check saved caliper positions and chord lengths where the task uses them. State the limits of the reference. |
| Form | Compare overview and decisive detail from two useful directions at fixed scale, camera and lighting. Inspect the delivered mesh for new degeneracy, reversed faces, pinching or lost detail. Test manifold closure where the structure should be closed. Reimport the actual export. |
| Readability | Name what the learner must distinguish. Show the exact 3D scene and matching acquisition frame at teaching zoom, with probe contact, section, registered overlay and any saved calipers. For acquisition-only claims, test the maneuver, image or measurement with the owning reader. |
| Economy | Record triangles, delivered bytes and the consuming bundle. Compare the lightest candidate that preserves the protected feature. Use mesh budgets as guidance for the actual viewer. |

Hold a candidate if its reference or spatial placement cannot support the claim, a protected gate fails, an identity mismatches, or a saved acquisition breaks. Close a schematic use only when the owner names the task it supports and a reviewer verifies that task in the chapter. Keep the representation visible in the ledger. Registration by itself confers no anatomical rating. The lead independently inspects the worker's measurements and witnesses before recording **adopt for the named task**, **keep baseline**, or **hold pending evidence**. Grant a higher rating only with new axis-specific observations. [Scan-surface refinement](guides/scan-surface-refinement.md#decide-whether-to-ship)

### CT-derived assets

Treat a CT segmentation mask as an **anatomical reference** for placement, proportion, orientation and key landmarks — **not** a pixelated voxel surface to copy vertex-for-vertex. Raw `1.5 mm` marching-cubes meshes carry visible axial terraces and `23k–123k` redundant triangles that fall short of the [visual quality target](guides/visual-quality-target.md) on **Form** and **Economy**.

Follow [scan-derived surface refinement](guides/scan-surface-refinement.md) to actively smooth, sculpt, close spurious holes and retopologize/decimate each target into a clean, organic, low-poly teaching mesh (typically `~1.5k–6k` triangles for a single solid organ) while preserving its case spatial registration, overall span and protected scan-plane landmarks. Changing mesh connectivity is expected; verify orientation, manifold closure, zero degeneracy/self-intersections and protected-section contours directly on the clean-reimported export. Avoid brittle voxel-clone traps (no single-vertex `argmax(axis)` cap-displacement gates on blunt poles; localize any 2D section maxima without sector clipping). Record transferable lessons in [scan-surface-refinement.md](guides/scan-surface-refinement.md) and keep asset-specific parameters with the package recipe.

### Review binding before parallel mesh work

The [workbench](../experiments/ultrasound-sweep/development/assets.js) matches standalone reviews to individual mesh digests and keeps the [family recipe](../lib/med_assets/ultrasound_review.py) for earlier modeled reviews. Changing only the liver in the disposable trial changed the organ-family fingerprint. The baseline mismatches alone cannot identify which input changed historically.

For an upgraded chapter, the player declares each emitted part in the chapter's `reviewMeshes`. The part's declaration carries the actual emitted `path`, applied `placement` and the delivered `inputs` that control the claim. Include the saved pose, acquisition, scan, overlay and render inputs when the claim depends on them. Assembly computes `meshSha256` from the packed file and `chapterSha256` from those scoped inputs, the saved frame, observation and measurement. The workbench checks both digests, the rubric and the served mesh bytes. An authored review applies to one case, chapter and part and keeps its own task and witnessed evidence. Earlier procedural and acquisition reviews retain their recipe binding until their observations are checked against a fresh delivery. [Wave 1 regression evidence](../records/campaigns/ultrasound-refinement/wave-1/README.md#verification)

## AssetKit admission and retention

For an adopted reusable 3D asset, record its canonical package, three-segment asset ID, revision, export, path, SHA-256, bytes, triangles, parts, frame, source, license and replay inputs. A packed single-part mesh can identify its part without a named node selector. A voxel export needs its `voxelGrid.case`, `shape` and `rasMmFromVoxel` checked against the owning case. Other spatial handoffs need evidenced units, axes and placement into the consumer frame. [Record contract](MIGRATION_SPEC.md#record-contract) · [Registration guide](../src/assetkit/README.md#register-a-package)

Replay into a fresh output, obtain the expected identity independently, then prove that the owning consumer fetches those bytes. Bind mesh-backed observations to the emitted mesh digest and recipe-backed observations to their actual recipe. Pin decisive review images using the owning review format. Keep the accepted export, editable source or deterministic recipe, owner record, credit and decision evidence. Use ignored scratch for exploratory meshes, screenshots and staging trees. Preserve superseded bytes or evidence while a release, reader or rollback depends on them. Check `uv run python tools/verify.py retained <path>` before retirement. [Retention](WORKFLOW.md#retention)

## Wave plan

The lead owns shared readers, track manifests, review registries, final ratings and integration. Each worker owns one scoped package and its candidate evidence. The brief names the task, baseline identity, source, protected landmark, tolerances, affected chapters and exact acceptance commands. The receipt returns the replay identity, measurements, matched views, gate results, limits and a proposed disposition. Wave 0 ends with an audited inventory and a brief. Starting any geometry comparison, changing the chapter renderer or building a Gallery progress card requires Wave 1 authorization.

| Wave | Scope | Exit decision |
| --- | --- | --- |
| 0 · Audit | Reconcile intended stages, reviews and chapter uses. Existing native curation already exposes the HRA, s1233 liver and echo pilots. Demonstrate an actual missing reader before extending it. | Lead presents an evidence-backed first brief, baseline and stop condition for approval. |
| 1 · First chapter replacement | Sculpt/refine and retopologize the s1233 right kidney from its CT reference (`~2k–5k` clean triangles, smooth organic exterior, preserved poles and medial recess) and replace the 107 mm ellipsoid in `abdomen-survey / abd-right-kidney`, proving full AssetKit admission, per-chapter `meshSha256` review binding and the first offline Gallery Development Before → After card. | Independently adopt, keep or hold the refined export. Expand to parallel Wave 2 workers once one end-to-end sculpted adoption loop proves a clear teaching and visual upgrade. |
| 2 · Missing anatomy and pathology | Prioritize verified gaps by learner impact and available reference. Candidates include hepatic veins and caval junction, gallbladder wall/lumen, renal collecting system, AAA wall/thrombus, carotid branches/plaque, thyroid/breast lesions, pregnancy landmarks and valve leaflets. | Each family demonstrates source provenance, placement and the intended lesson behavior. Track unsupported claims explicitly. |
| 3 · Shared props, Gallery and retirement | Consider reusable probes when readers need the same governed export. Complete offline Gallery discovery for accepted work and retire legacy projections as their named readers migrate. | Built Gallery resolves exact revisions and witnesses with the study server stopped. Verify retention and rights for included materials. [Gallery work item](../records/work-items/items/AG-GAL-032-ultrasound-asset-discovery.md) |

For the hepatic-vein/IVC junction, the s1233 liver exterior cannot supply a separate vein label. Require an evidenced source and registration, or keep the junction open. HRA and other subjects can serve as anatomical references with their own provenance. For a mobile calculus, pre/postvoid state, ectopic pregnancy, nuchal translucency, Doppler or valve motion, first identify whether the evidence gap is geometry, state change, acquisition or a measurement. A static mesh covers only the claim its reader demonstrates.

## Visual progress and counters

Once an adopted packet exists, expose the matched overview and detail, protected section, saved acquisition and review on the workbench and Gallery Development view. Each card names the task, exact revisions, frame, observations and measured deltas. Retain a static witness for the built Gallery. An acquired comparison carries its source, rights and relationship to the study. Keep held trials visibly distinct from adopted work. [Gallery collection pages](gallery/use-cases/README.md#collection-pages)

Generate counters from the same dated delivery and ledger. Report native chapter coverage against audited chapters, qualified current tasks against reviewed current tasks, and pending or prior reviews against all in-scope tasks. Publish the numerator, denominator and unaudited count. Track confirmed rebuilds and remaining description-only readers separately. The 15 historical top scores and the 410 emitted chapters are different populations.

## Verification gates

**Per admitted export.** Use the package's clean replay command first. Preview record sync and inspect the plan. Applying a reviewed plan requires `--apply --expect-plan <planToken>`. Supply selector expectations for formats with named parts. Independently pinned identity inputs to the hydrated check are required.

```sh
uv run assetkit sync <package>/asset.record.json
uv run assetkit check-port <asset-id>@<rev>:<export> \
  --record <package>/asset.record.json --path <payload> \
  --sha256 <replay-sha> --bytes <replay-bytes> --triangles <replay-triangles>
uv run assetkit validate
uv run assetkit --native-only show <asset-id>@<rev>:<export>
uv run assetkit --native-only impact <asset-id>@<rev>:<export>
uv run assetkit economy
uv run assetkit bundle <consumer>
```

**Per affected lesson.** Rebuild from the named staging inputs. Validate the owning review package against the emitted identity. Exercise its family playable test, saved frames and actual browser requests. Use the registered AAA acquisition checks when AAA is in scope. `assetkit review check` validates the maintained teaching register and scorecard. The ultrasound workbench validator and delivery comparison establish ultrasound review currency.

**At an authorized wave close.** Run the repository checks below and the gates for each changed family. Supply the prepared staging tree to `verify_assembly.py`, the assembled delivery directory to the geometry check, and its served URL to browser tests. Record revision, staging coverage, failed or skipped checks and remaining blockers. Verify the built Gallery with the study server stopped when a packet changes Gallery discovery or evidence.

```sh
uv run ruff check src/assetkit
uv run ruff format --check src/assetkit
uv run ty check src/assetkit
uv run pytest src/assetkit/tests -q
uv run assetkit review check
uv run python tools/verify.py offline
uv run python tools/verify.py payload-integrity
python3.12 experiments/ultrasound-sweep/cases/verify_cases.py
python3.12 experiments/ultrasound-sweep/verify_assembly.py "$STUDY_STAGE"
node experiments/ultrasound-sweep/tours/verify-case-geometry.mjs "$STUDY_DELIVERY"
node experiments/ultrasound-sweep/tours/verify-case-tours.mjs "$STUDY_URL" "$EXAM_CAPTURES"
node experiments/ultrasound-sweep/cases/verify-browser.mjs "$STUDY_URL" "$REVIEW_CAPTURES"
```
