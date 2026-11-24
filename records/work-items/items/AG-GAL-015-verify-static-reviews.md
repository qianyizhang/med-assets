---
description: Carry the remaining static hosted findings into revision-specific Gallery reviews.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-015
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, evidence
depends_on: AG-GAL-013
residual_of: AG-GAL-013
residual_items: none
---

# AG-GAL-015 — Integrate retained static reviews

Start with the static Anatomy Verification pages in the [coverage ledger](AG-GAL-013-reconcile-gallery-coverage.md). Add exact Library handoffs and revision-specific Compare pages for biliary and abdomen labels, bronchial r09, head labels, polish and the spinal relationship study. Route oral spaces and 2D teaching aids to [the teaching item](AG-GAL-016-integrate-retained-teaching.md). Carry marrow, pelvic and dental tool or specimen reports in separate collection slices. Keep the FDI31 interface review distinct from Balanced.

- [x] Bind each view to the original artifact, finding, attribution and gate scope. Identify supplement, rejected and incomplete dispositions.
- [x] Verify direct Gallery journeys and record legacy candidate, evidence-order and file dispositions for the migrated studies.
- [x] Record any workflow that needs a live selector, source recovery, or another rebuilt interaction for its own review.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Codex | — | deferred | Remaining static reviews identified in the Wave 2 census. |
| 2026-11-21 | Codex | deferred | wip | Maintainer approved the local batch after review of `7f24bb6`. |
| 2026-11-21 | Codex | wip | done | The ordinary build, browser journeys and exact local payload checks passed. |

## Implementation Ledger

### Anatomy Verification

Start at Compare. The [saved review registry](../../../sites/anatomy-gallery/app/src/content/gallery/static-reviews.json) owns the `compare/<id>` and appendix section IDs. The original biliary teaching plates already have the bilingual routes under Use Cases. The independent stomach-label finding opens in Compare as `abdomen-label-r01`. Head locator r01, bronchial r09 and spinal r03 have their own review pages. The polish appendix retains its parathyroid, bronchial r07 and esophagus sections, each with an exact Library handoff. Spinal r04 keeps its draft candidate and geometry projections separate from the r03 stills.

The Verification directory also exposes four scoped static supplements. Compare carries the right Achilles context, independent marrow container/micro-CT witness, adipose regional reconstruction and rejected whole-mouth trial. The first three link their own exact Library records. The mouth review retains the combined still and the two diagnostic artifact identities from the original record.

The prior adrenal and trachea r05 pages remain the existing Compare destinations. The separately published salivary and Airway studies retain their current Gallery records.

### Body & Heart

Compare carries the exact marrow cutaway r05 and two separate pelvic studies. The marrow composite and both pelvic composites use full width. Their native views retain the source order and the disclosed differences in pose, registration or scale. The corresponding Library records link back to each study.

### Dental Review

The local Compare entries cover the UFF proxy/endpoint finding, the FDI31 interface-locked candidate and rejected simplifications, the BodyParts3D dental-set contact failure, the earlier FDI31 r03 source-layer still, cotton tweezers r04 and mouth mirror r01. The labelled arches already have a Use Cases lesson. The Balanced specimen stays on the existing Library card. Its branch of the lineage is separate from both the interface-locked candidate and the older layer study.

The tool models and seven original figures passed exact legacy readback. Their studio renders support recognizable static form. The loopback preview reads the exact recovered GLBs and original PNGs from the [pinned local cache](../../../sites/anatomy-gallery/README.md#legacy-dental-review-media). The prepared-layer PNG uses the same cache. The Library records the original r03 GLB identity and its unavailable state. Compare can still open the supported still and its bindings.

### Existing Gallery coverage

| Legacy material | Use the existing destination |
| --- | --- |
| Biliary teaching diagram, English and Chinese | `/#/use-cases/biliary-pathway/en` and `/zh`. The stomach-label witness has its separate Compare page. |
| BodyParts3D adrenal candidate, salivary r02, trachea r05 and the separate Airway reviews | Existing Compare records and their Library handoffs in the [collection ledger](AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger). |
| Oral spaces and the regional teaching aids | [Use Cases](AG-GAL-016-integrate-retained-teaching.md#oral-spaces-and-regional-locators) owns the cutaways and regional locators. The rejected whole-mouth review has a distinct finding. |
| Dental labelled arches and the Balanced retirement handoff | `/#/use-cases/dental-arch` and `/#/library/swirendo_fdi31`. The broader contact checkpoint opens in Compare. |

### Remaining source and interaction work

| Study or workflow | Owner and acceptance needed |
| --- | --- |
| UFF hard-tissue and void inspection | [UFF package](../../../reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/README.md) and Gallery Stage. The exact-revision Library page and Compare now link the verified historical inspector. A Gallery-native implementation still needs shared scene support for two independent visibility controls, source-X clipping, saved state and loss feedback. See the [hosted control check](../../../reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/README.md#hosted-inspector-follow-up--2026-11-21) before scheduling that work. The static extraction and negative endpoint evidence are locally available. |
| FDI31 prepared incisor r03 | [SWIRendo pilot owner](../../../docs/dental-atlas/pilot-ingestion.md). Recover the historical 13,239,300-byte GLB with SHA-256 `23e59040c6c2497ef864cf229d90dbd9e347489f1c9f4a8860bd48422cc2ec21` from an original pilot workspace or an identified backup containing the derivative. The source dataset ZIP contains segmentations. The matched layer PNG and its source bindings are available. |
| Spinal r04 native raster set | [Spinal review owner](../../../reviews/spinal_cord/2026-10-29-authored-roots-r04/README.md). The locally delivered SVG projections bind both exact exports. Use the original six raster files with their recorded camera and hashes if a later study needs shading or occlusion judgments. |
| Adipose historical derivative | [Adipose package owner](../../../models/adipose-context/r01/README.md). Locate the historical derivative and corroborate its identity if a future comparison requires it. The Gallery opens the r01 source-scene reconstruction and its four unchanged pads. |
| Eye, knee and pharynx inspection, heart phase/slice and studio | Existing [Verification](AG-GAL-004-consolidate-legacy-packages.md) and [Body & Heart](AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) owners. Preserve viewer and candidate state, decide which controls to rebuild, then verify equivalent behavior before cutover. |

The legacy Verification directory readback exposed 69 asset rows, 38 candidate viewer rows, four context supplements, one negative supplement, one two-part teaching supplement and one technical runtime witness. Candidate rows and their application state remain with the [existing integration](../../../tests/viewer/README.md) except for the saved finding handoffs above. Their historical review gates and evidence order remain with that owner.

### Legacy pages and files

These are page and file observations from 2026-11-21. The existing hosts retain their addresses. Redirects, publication and storage retirement have their own acceptance decisions.

| Collection | Old page or fragment disposition |
| --- | --- |
| Verification directory and ledger | The [directory](https://anatomy-verification.landy123007.chatgpt.site/review/) and its accounting route responded. Keep the existing asset and candidate anchors and API for active viewer consumers. Static supplement readers enter via `#asset-draft_muscle`, `#asset-draft_bone`, `#asset-draft_adipose` and `#asset-draft_mouth`. Map their scoped findings to the respective local reviews at cutover. |
| Verification teaching supplements | [AG-GAL-016](AG-GAL-016-integrate-retained-teaching.md#legacy-teaching-supplements) verifies the local lymph source-route lesson and both skeletal relationship studies in Use Cases. The [heart and lymph CI witness](../../../reviews/runtime/2026-10-23-software-ci-heart-lymph/README.md) remains runtime evidence. |
| Biliary and abdomen | The old `biliary-label-2026-10-25/#biliary` belongs with the lesson. Its `#label` belongs with `compare/abdomen-label-r01`. The probed standalone `abdomen-label-2026-10-25/` spelling returned 404. |
| Other Verification pages | The r09 bronchial, head-label, polish and spinal r03 pages returned 200. Preserve the separate polish anchors `#parathyroids`, `#bronchial` and `#esophagus`. The spinal r04 candidate bookmark also returned HTML. Its gzip payload decoded to the exact 2,663,288-byte GLB. |
| Body & Heart | The [marrow, penile components and urethral context](../../../docs/gallery/existing-visualizations.md#hosted-page-readback) pages returned 200. Their old baseline/Studio links remain distinct from the new revision pages. |
| Dental | The [homepage](https://anatomy-dental-review.landy123007.chatgpt.site/) returned 200 and contains `#fdi31-interface-locked`, `#set-checkpoint`, `#prepared-layer-research` and `#technical`. The interface payload directory returned 404 as an HTML page while its exact model and four files passed readback. Both tool pages and the UFF inspector returned 200. The r03 PNG and SVG had live standalone URLs. |
| File contracts | The 96 retained image and model addresses from the named review deliveries and 16 supplement file addresses matched their pinned identities. Recheck preserved media responses when changing their hosting. [Legacy file delivery](../../../transport/README.md#legacy-file-addresses) owns exact-byte consumers and [page handoffs](../../../docs/gallery/routes-and-api.md#legacy-page-handoffs) own bookmark changes. |

The repository keeps original witnesses, old manifests, review bindings and package history at their existing owners. New WebPs are display copies. Raster originals retain decoded-pixel equality with their new WebPs. The spinal r04 WebPs rasterize the pinned vector projections and link the original SVGs. Recovered legacy tool assets live in the ignored preview cache. The public delivery index and hosting lifecycle have separate owners.

### Verification trachea r05 hosted control

On 2026-11-22 the Verification r05 page and its `page.js` returned 200. The script resolves `record.json` and `PAYLOAD-HASHES.json` against `payload/reviews/trachea/2026-10-25-host-conforming-cbands-r05/`. Both actual requests returned 200 JSON. The 2,863-byte record matches the [local record](../../../reviews/trachea/2026-10-25-host-conforming-cbands-r05/record.json) at SHA-256 `a2a520098de0587fdd95a4ea489d74c93b5d70850ceacccb0117ee8908fe5fc7`. The 4,098-byte inventory at SHA-256 `dab80367f1e940f24f2aac1634816909cfae0a23a41d14add6a26df568a56d95` contains all eight [transport manifest](../../../transport/manifests/8b443938d5dea33128fe52fe7ee664b1801992705704e04703a05714ba110bc8.json) size and digest pairs. The earlier 404s came from probes at the review page root.

All eight original media URLs returned 307 to another origin. Each final response matched the exact bytes, including the 707,132-byte GLB and seven original PNGs. The guarded downloader rejects the cross-origin redirect. Keep the original host and manifests while the Verification owner evaluates same-origin service or an approved consumer migration. The Head & Neck and Airway handoff keeps this third host out of its routing. The candidate Gallery's r05 Compare and Library routes delivered the distinct closed-cast revision and exact local evidence. [Joint release rehearsal](AG-GAL-013-reconcile-gallery-coverage.md#2026-11-22-joint-release-rehearsal)

### Local verification

The batch delivery source was `71011798b46b73528d4bd98a398cca3d1098d437`. Its HTML SHA-256 was `eb9eec71d1b180619bf6ca88e77d13d4c957d4f35273e1a79e1068603a307e3e`. The collection commits are `6853292` for Verification, `2b7e8f3` for Body & Heart, `5c3d7fc` for Dental Review and `951c90c` for the Verification supplements. The dental recovery follow-up is `ee856d0`.

- The pinned framework build, 12 Site tests and preview regression passed.
- Chrome discovered 19 Compare entries, including the three direct polish-section links, and verified 182 distinct display, source and export identities. It checked reloads, evidence order, actual download, original-image fallback, unavailable evidence and exact revision returns.
- The ordinary Gallery browser suite passed the four surfaces and the existing teaching and archive journeys. Its old 96-entry assertion needed the new 99-entry expectation. UFF, cotton tweezers and mouth mirror were found through Library search.
- Payload integrity passed with 439 offline tests, 1,000 indexed LFS files, 25 foundation records and 11 package checks. The isolated UFF dental gate passed seven tests, including the exact GLB identity.
- The preview cache recovered all ten pinned legacy Dental Review payloads from an empty directory. A same-size altered file was refused and restored to its original identity.

The retained walkthrough opens at `http://127.0.0.1:8891/#/compare` after starting the loopback preview. The ignored bundle at `.artifacts/anatomy-gallery-static-reviews/` holds the restart command, screenshots and local and legacy readback receipts. Review that bundle and its generated build retention on 2026-12-21.

### Review follow-up · Recovery and compaction

The original render binding names the r03 model `A_1_31_T2_SEG_na__layered.glb`. The delivered interface-locked GLB has the same basename and a different SHA-256 (`c0884a6b…`). The public repository LFS endpoint returned 404 for the exact r03 object and the live Site index had no matching declaration. A bounded search of checkout, temporary and download candidates, including seven relevant ZIP or tar archives, found neither the r03 bytes nor the six native spinal rasters matching their receipts. The original adipose derivative identifier was absent from the local Git object database. Reopen recovery when an original reviewer workspace, matching archive member or new consumer of those witnesses is identified.

At the `7137a32` review, the maintainer deferred all three searches pending new evidence and retained the [verified external UFF inspector](../../../reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/README.md#hosted-inspector-follow-up--2026-11-21) as the bridge from the exact Library revision and Compare.

The upper and lower dental contact views now use the same display files as the dental arch selector. For each plate both WebP encodings and the retained PNG decoded to identical 1,100 × 1,000 RGBA pixels. The retired pair accounted for 624,976 bytes in the working tree and two local delivery entries. Neither retired digest appeared in the live 1,001-entry index. Original PNGs and exact export identities stay with their owners.

The polished local HTML has SHA-256 `73cdf764b07d74ce36d378bcada598beb5f8b6ba465cb33ccc995dd0689e4cdb`. Disposable Chrome checked all 19 Compare entries, 182 identities, both UFF inspector links and the ordinary Gallery journeys. The build, 12 Site tests, 439 offline tests, 998 indexed LFS payloads and seven focused dental tests passed.

## 2026-11-22 collection checks

The protected `caa7510` Gallery build (HTML SHA-256 `63cd67c70ca3783d48cb12d4a17fa2f12e775314fa261c0c70eb66d4ec6d828e`) passed the existing 19-entry static review regression in disposable Chrome. It checked 216 display, original evidence and model identities, reload, return navigation and missing-image recovery. The specialist still test matched all seven files, the Library and parent returns, and both archive film handoffs. The local FDI31 notice exercise also checked the missing-index download error and exact recovery.

| Collection | Local destination and hosted disposition |
| --- | --- |
| Anatomy Verification | The local Compare and Use Cases mappings above cover the static reports. The hosted directory and same-origin accounting redirect returned 200. Keep the directory, candidate links and eye, knee and pharynx inspection paths for their legacy selection and viewer state. The earlier static findings and teaching entry points returned HTML. The standalone abdomen-label spelling returned 404. The linked biliary page remains the combined entry and the local abdomen Compare route retains the separate finding. Trachea r05 rendered its evidence and language switch in Chrome, with all eight downloads and the original directory return present. The live guarded GLB GET stopped at the cross-origin redirect. |
| Dental and FDI31 | Local Compare, Library, the arch and layer lessons, and the shot archive remain available. Both UFF links reach the external inspector. Chrome loaded the pinned model route and exercised both visibility buttons, clipping position and reload defaults. The published retirement notice opened the published FDI31 entry in Chrome. Both direct and in-card downloads matched the 2,052,220-byte Balanced GLB. The Dental homepage fragments for the interface and prepared layers are present. Their standalone directory URLs returned 404, while the interface GLB and original evidence, tool payloads and prepared-layer still matched their pins. Keep the missing r03 GLB and other deferred sources on the recovery list above. The ten [locked tool and prepared-layer originals](../../../sites/anatomy-gallery/app/src/content/assets/legacy-dental-assets.json) total 8,550,761 bytes across the legacy host and local recovery cache. Public Gallery delivery of those exact routes is a separate dependency. |
| Body & Heart | Local Compare opens the marrow r05 and two pelvic studies, with exact Library models, original evidence and returns. Cardiovascular opens the original reference-frame-1 plate. The three legacy review pages, cardiac imaging, connected systems and studio returned 200, including the studio after a transport retry. All 19 scoped review files and the studio's pinned 8,180,452-byte motion GLB matched. Chrome confirmed phase and slice controls on the cardiac page and switched between the Studio's Atlas and Assets tabs. Keep the specialist phase, slice and studio journeys under their existing owner. |

The new public readback matched 63 pinned asset URLs. The published Gallery study API still returned 404 while its 1,001-entry asset index returned 200. The local and hosted receipts use `.artifacts/gallery-collection-readback/`. Keep the public releases and specialist hosts under their existing owners. The tracked Gallery inputs and tracked LFS bytes did not change in this check.
