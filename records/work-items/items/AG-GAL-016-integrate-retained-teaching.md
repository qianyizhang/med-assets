---
description: Give retained static lessons and public experiments discoverable Gallery routes.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-016
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, evidence
depends_on: AG-GAL-013
residual_of: AG-GAL-013
residual_items: none
---

# AG-GAL-016 — Integrate retained teaching stops

## Intent

Use the [coverage ledger](AG-GAL-013-reconcile-gallery-coverage.md) to adopt already authored material in small teaching slices. Start with oral spaces and regional locators, then the three route diagrams and dental arch identification. The kidney trial and selected dental film studies belong in Experiments & Archive with dated evidence. Scope authored motion, layer editing and One Breath separately after the walkthrough.

## Local acceptance

- [x] Show the teaching task and the actual image or interaction, with bilingual copy where the owner already supplies it.
- [x] Verify exact model and source identities, no-media fallback and the dental arch interaction.
- [x] Preserve the originals and record separate-scale, illustrative or source-specific limits where the visitor sees them.
- [x] Finish static Gallery placement for the [deferred journeys](AG-GAL-013-reconcile-gallery-coverage.md#deferred-specialist-journeys). Confirm discovery, a representative source-bound view and its return link in the ordinary local build. Use existing destinations where they already serve the material.

## Context and Trade-offs

The maintainer accepted the oral-spaces and regional-locator walkthrough at `69cf94a`. The three bilingual pathways and interactive dental arch are approved for local delivery. The same batch can include small archive migrations that reuse verified media.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Codex | — | deferred | Existing teaching stops identified in the Wave 2 census. |
| 2026-11-21 | Maintainer | deferred | ready | Selected oral spaces and regional locators for the next local teaching slice. |
| 2026-11-21 | Codex | ready | wip | Delivered the selected local slice at `f4c94f5` for maintainer review. |
| 2026-11-21 | Maintainer | wip | wip | Accepted the walkthrough at `69cf94a` and approved the next local batch. |
| 2026-11-21 | Maintainer | wip | wip | At `7137a32`, approved local migration of the lymph route lesson and both skeletal relationship studies. |
| 2026-11-21 | Codex | wip | done | Verified the specialist stills and the existing film and UFF handoffs in the local walkthrough. |

## Implementation Ledger

### Oral spaces and regional locators

Use Cases now links `/#/use-cases/oral-spaces` and `/#/use-cases/regional-locators`. Head & Neck links to oral spaces. Cardiovascular, Nervous and Reproductive Body Systems pages link to their locator stops.

| Stop | Retained teaching evidence and scale |
| --- | --- |
| `oral-spaces/en` and `oral-spaces/zh` | Independent [English and Chinese r01 cutaways](../../../diagrams/oral_spaces/exports/r01/README.md). The schematic has no measured scale. The [scoped 2D finding and rejected 3D reconstruction](../../../reviews/oral_spaces/2026-10-26-r01/INDEPENDENT-REVIEW.md) keep separate outcomes. |
| `regional-locators/aortic-arch` | [Z-Anatomy r02](../../../lessons/aortic-arch-locators/README.md). Full-width overview followed by an enlarged junction, each retaining the matched Original / Updated pair. Source labels identify three direct origins and the right subclavian branch. |
| `regional-locators/pulmonary-vein` | [s1233 same-case context](../../../lessons/pulmonary-vein-context/README.md). The isolated component and contextual view stay side by side at matched scale within each row. The lower row enlarges the marked region. |
| `regional-locators/brain-source-cut` | [Reviewed front comparison](../../../reviews/brain/2026-10-29-source-cut/README.md) for the BodyParts3D atlas r2. The bracket marks an editorial source cut. The detail magnifies the retained render, and the original side-view SVGs stay with the lesson package. |
| `regional-locators/ovary-tubal-context` | [HRA ovary and tubal end](../../../lessons/ovary-tubal-context/README.md). The native overview leads to enlarged numbered views. A separate plate shows the schematic above the HRA alternative at independent scales. |

**Local verification.** At `f4c94f5079c8d816bf9c4adf39b7f1168671e8b5`, the pinned framework build, 12 Site tests, 439 offline tests and payload-integrity gate passed. Payload integrity covered 922 LFS files, 25 foundation records and 11 package checks. The eight WebPs matched the original PNG dimensions and decoded pixels. Four source GLBs, eight PNGs and both oral SVGs matched their owning receipts.

Disposable Chrome verified discovery, keyboard use, direct links and reloads, returns to the collection and related assemblies, all eight decoded plates, exact local media and GLB responses, and existing Gallery journeys. The labels were inspected at 1280 × 900 and 1024 × 768. With the arch overview WebP unavailable, Chrome displayed its retained PNG. With both formats unavailable, the junction detail, teaching copy and source links remained available, and reload restored the overview after the routes recovered. The walkthrough follow-up shortens the pulmonary-vein question and describes the ovary alternatives in their original order. The final walkthrough and captures are in `.artifacts/anatomy-gallery-teaching-stops/`.

**Legacy checks.** The [oral-spaces page](https://anatomy-verification.landy123007.chatgpt.site/review/oral-spaces-2026-10-26/) and [2D teaching-aids page](https://anatomy-verification.landy123007.chatgpt.site/review/teaching-2d-2026-10-25/) served their HTML and decoded a representative plate in both language states in Chrome. Twelve PNG/SVG files matched their recorded bytes through both historical paths and mapped object URLs. The known bronchial bookmark failure remains in the [Airway compatibility ledger](AG-GAL-013-reconcile-gallery-coverage.md#airway-review). Public Gallery handoffs and wider legacy coverage remain open.

**Review boundary.** The local slice reuses existing evidence. Anatomy and clinical review of the source models remains under their existing records. Dedicated Compare entries for these editorial witnesses can be discussed after the walkthrough. [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md) remains deferred until public cutover.

**Review follow-up.** Oral spaces and Head & Neck now carry the chosen cutaway language and originating gland or duct stop across the handoff, including after reload. The local Chrome journey also passed with a partial delivery index: an absent display entry used the retained PNG, an absent display and PNG kept the source link, and an unavailable GLB left the locator lesson usable.

### Bilingual pathway diagrams

Use Cases and Body Systems link the retained [biliary r01](../../../diagrams/biliary_pathway/exports/r01/README.md), [testis r02](../../../diagrams/testis_pathway/exports/r02/README.md) and [urinary outflow r01](../../../diagrams/urinary_outflow/exports/r01/README.md) figures. The r01 paths use lossless WebP copies and fall back to the reviewed PNGs, with original vector links. The four 1400 × 1060 display files match their respective PNGs in all decoded RGBA pixels. The r02 testis path renders the reviewed SVG bytes from each language, including its grouped transport summary. The original r01 testis files remain available to historical readers.

The pinned build, all 12 Site tests, 439 offline tests and disposable Chrome passed. Chrome decoded and matched all six figures to their review digests, opened them from Use Cases and the corresponding Body Systems detail, and kept that detail through a language change and reload. Both r01 error states kept teaching copy, attribution, the source vector and the return path, and recovered on reload. The labeled routes were readable at 1024 × 768. This verifies the local presentation and source identity.

### Dental arch identification

Use Cases links `/#/use-cases/dental-arch` with direct upper and lower starts. The [original lesson](../../../lessons/arch-identification/README.md) owns its bilingual labels, coverage receipt, crown locators, keyboard behavior and per-arch selection. The Gallery builds from that lesson. The two owner-held lossless WebPs match the 1100 × 1000 source PNGs pixel for pixel. The PNGs remain linked to their original source review and serve as the first fallback.

Chrome verified all 28 FDI labels, both crown views, patient side, all arrows and Home/End, both languages, independent selection for each arch and the four uncovered slots. A failed WebP used the original PNG. With both formats blocked, FDI and keyboard selection still worked, and retry restored the crown image and selection. The exact source check verified the GLB, both original PNGs and 28 annotated crown ray hits. The standalone Chrome journey also passed, including 320 px layout and retry. The pinned build and 12 Site tests passed.


### Experiments & Archive

| Local route | Evidence and remaining decisions |
| --- | --- |
| `/#/archive/kidney-outline-trial` | The [2026-10-30 kidney trial](../../../lessons/kidney-location/README.md) keeps the exterior, isolated shapes and equal-scale paired control. The original verified contact WebP and projected silhouette supply the crops and optional outline. The owner records a provisional visual observation. Independent review and learning-outcome evidence remain open. |
| `/#/archive/dental-video-treatments` | The [2026-11-03 experiment](../../../experiments/dental-video-treatments/README.md) plays three 48-second treatments and the synchronized comparison. The LFS exports, shared narration, matched storyboard and result manifest stay with the experiment. Direct human listening and clinical review are open. |
| `/#/archive/dental-image26` | The [2026-11-06 experiment](../../../experiments/dental-image26/README.md) plays five stories and the combined film by their exact [backup member hashes](../../../sites/body-systems-survey/backup-sha256.txt). The preview reads restored results only on loopback. The experiment owns its scripts, GIFs, frozen narration and recovery. The [Gallery delivery owner](../../../sites/anatomy-gallery/README.md#archive-media) owns the future decision about an addressable public route and rights scope. |

### Batch verification and remaining work

Tested runtime and verifier commit `cce7e55f608048ab50432bd49b3c76e042bcaeb4` incorporates the pathway commits `05ae798` and `87a325a`, and dental arch commit `eecc6a6`. The pinned HTML SHA-256 was `99044b0ee89cd2940a5ede52c87d8f7c48308378260c780c908f401a7c214e9c`. The framework build, 12 Site tests, 439 offline tests and payload-integrity passed. Payload integrity checked 928 local LFS files, 25 foundation records and 11 package checks.

Chrome passed the ordinary Gallery journey, including both new teaching slices. It verified the kidney’s original control pair and outline at equal scale, both languages, and missing/corrupt image rejection. The original standalone route also passed, and the package verifier corroborated the source crops and 180-point outline. Chrome played and sought through all ten dental films, matched full bytes and caption cues, and checked retry after a failed video. A preview with the Image 2.6 archive declarations absent kept its transcript and provenance available and still played the original dental treatments. The teaching ZIP and all 13 Image 2.6 result members matched their digests both in the archive and at the restored paths. FFmpeg decoded all ten movies. The local walkthrough and captures are in `.artifacts/anatomy-gallery-migration-batch/`.

The legacy [2D teaching-aids](https://anatomy-verification.landy123007.chatgpt.site/review/teaching-2d-2026-10-25/) and [biliary review](https://anatomy-verification.landy123007.chatgpt.site/review/biliary-label-2026-10-25/) pages both returned HTTP 200. The [known bronchial 404](AG-GAL-013-reconcile-gallery-coverage.md#airway-review) remains legacy triage. Public cutover, fresh hosted payload acceptance and [AG-GAL-014](AG-GAL-014-compact-delivery-and-recovery.md) remain deferred. One Breath, dental layer editing and authored motion retain their separate interaction and author review dependencies.

**Preview recovery follow-up.** A film missing when the preview started previously stayed unavailable after restoration. The preview now verifies the requested backup member on each request and reuses those verified bytes for that response. The same running process served exact range bytes after restore, refused same-size corruption and recovered again. The public delivery index excluded the local-only film throughout. The full Gallery browser journey and all 28 dental crown endpoint checks passed.

### Legacy teaching supplements

| Local route | Source and scope |
| --- | --- |
| `/#/use-cases/lymph-collecting-routes/en` and `…/zh` | [Refined r01](../../../models/lymph-collecting-routes/source-context-refined-r01/README.md). Exact bilingual PNGs retain all seven source routes and their cap markers. The body contour and regional ticks are illustrative. The optional dashes follow only the source-named thoracic route in the two Updated views, lower cap toward upper cap. Six routes and both Original views stay static. Caps identify source mesh limits. The lesson makes no measured-flow, lumen, registration or venous-connection claim. |
| `/#/use-cases/skeletal-relationships/second-costal` and `…/l3-l4-disc` | [2026-10-23 static review](../../../reviews/skeletal_teaching/2026-10-23/record.json). Each stop pairs front and side views, with oblique and neutral-gray images available below. Each links its own dated revision within `library/cartilage-assembly`. Diagnostic color and the bones give context. The plates supply no measurement scale and cover selected ribs/cartilage or the gross exterior disc relationship. The original cartilage-model verdict remains Needs revision. |

**Verified locally.** The lymph migration is `9716c40965980b5075b8bc9fb65462d8a4d19405`. The combined test revision is the skeletal commit `5d3d5b1df333ec451cb57d433c80e3d73dcb2899`, with HTML SHA-256 `f27426532abf0658bf3e765849e550235dd62e4f1beb8e905fb923a0ac73f683`. The pinned framework build, 12 Site tests, preview test, 439 offline tests and payload integrity passed. Payload integrity checked 998 LFS files, 25 foundation records and 11 package checks. Chrome verified the ordinary Gallery, 19 Compare entries including both UFF handoffs, the two new lessons and both exact skeletal GLBs. The teaching checks covered 1024 × 768 and 1280 × 900, discovery from Use Cases and Body Systems, direct links, reload, returns and image failure/recovery.

Chrome matched the two animated paths to their five-ring projections, checked all four cap masks and sampled moving dash offsets. The moving-phase pixel changes stayed on the two bound routes outside the cap-marker cores. Both original PNGs matched their retained hashes. Reduced motion, pause and reload produced the original static views. The initial state is static on each visit. The eight skeletal WebPs and two GLBs matched the review record. The 12 recorded part labels, roles and GLB accessor bounds agreed with the BodyParts3D source records after unit and axis conversion. The retained review supplies the earlier geometry roundtrip. Gallery verification covered the static teaching views and downloads.

**Disposition.** The [standalone lymph HTML](../../../models/lymph-collecting-routes/source-context-refined-r01/index.html) remains the package README's offline entry and the input to its source-binding checks. Its existing recipe reproduced it byte for byte from the two PNGs and retained projection. The regenerated page opened, switched language and played and paused with Chrome offline. The hosted Verification index still points to the original lymph package and declares both exact skeletal GLBs. Its costal caption leaves posterior contact unquantified, and its disc caption omits internal layers, nerves, ligaments and pathology. Keep those reader paths, the offline lesson and the exact skeletal evidence. The intermediate lymph-only preview used for this migration had no readers beyond its browser check. Its loopback process and ignored `.local/retained-supplements-lymph` build retired after the combined preview passed. Its commit and the unchanged framework, package and input locks preserve recovery. The [static-review ledger](AG-GAL-015-verify-static-reviews.md#review-follow-up--recovery-and-compaction) records the UFF bridge and the deferred FDI31 r03, spinal raster and adipose searches.

The combined walkthrough, restart command and captures are in `.artifacts/anatomy-gallery-retained-supplements/`. Publication, uploads and storage retirement have separate acceptance decisions. One Breath, layer editing and authored dental motion retain their separate interaction and author-review scopes.

**Skeletal handoff follow-up.** Following a teaching stop to its exact Library revision now preserves the originating Skeletal Body Systems detail on the explicit return, including after reload. Direct revision links still work without a referring detail. Library records show the license link when the credit has a destination. The salivary revision retains its Z-Anatomy credit. The reviewed walkthrough HTML has SHA-256 `43a83392778bd664e97b01fc4738348d9e425295e7790d24600a487171d88fe0`.

### Specialist stills

| Local route | Placement and source |
| --- | --- |
| `/#/use-cases/heart-slice` | Use Cases and Cardiovascular lead to the [original same-slice plate](../../../heart/synthetic-imaging/beating-heart/imaging/README.md) at reference frame 1. The color guide and CT-like and MRI-like presets show the same ventricles. The grayscale contrasts are arbitrary. |
| `/#/use-cases/one-breath` | Use Cases and Respiratory lead to the [original bilingual storyboard and replay](../../../lessons/one-breath/README.md). The retained capture shows the trachea dividing into the two main bronchi and omits smaller airways. The current replay source includes the longer route. The exchange diagram uses a separate scale. |
| `/#/use-cases/dental-layers` | Use Cases leads to the [control review sheet](../../../lessons/dental-layer-controls/media/control-review-sheet.jpg). The four panels show the prepared FDI31 source pose and isolated enamel, dentin and bone. The page links the exact Balanced download through its Library record. |
| `/#/archive/dental-shot-studies` | Experiments & Archive leads to the original [FDI31 source and reveal states](../../../lessons/dental-animation/fdi31-layer-reveal/README.md) and the [caries](../../../lessons/dental-animation/caries-restoration/README.md) and [periodontal cleaning](../../../lessons/dental-animation/periodontal-cleaning/README.md) posters. The existing Image 2.6 archive already serves both related subjects with separate films. The authored prototypes keep their own provenance and clinical review limits. |

The heart and breathing plates use existing delivery routes. Framework assembly copies the five smaller dental figures from their owning packages into the generated build. No new original or capture is required. The external UFF inspector bridge still opens from the exact Library revision and Compare. Interactive rebuilding and cutover remain deferred.

**Verified locally.** The rebuilt pinned framework, 12 Site tests, preview regression, repository gates and ordinary Chrome journeys passed. Chrome checked the seven displays against the exact source bytes, including the two SVG posters. It verified discovery, study API entries for the three lessons, reload, parent returns, missing and recovered indexed plates, the Balanced download link and both related film handoffs. The existing eleven systems, ten archive films and 19 Compare routes passed, including both UFF handoffs. The final HTML SHA-256 is `393040a8ef54a11678c6739cec6f1c49a59222f652724fc5cca1aa4a7068c7a4`. The walkthrough, restart command and captures are in `.artifacts/anatomy-gallery-static-placement/`.
