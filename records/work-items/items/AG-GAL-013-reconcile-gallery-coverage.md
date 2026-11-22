---
description: Carry each public viewing experience from the census into a migration or retirement decision.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-013
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, repository, evidence
depends_on: AG-GAL-003
residual_of: none
residual_items: AG-GAL-015, AG-GAL-016
---

# AG-GAL-013 — Account for the remaining gallery experiences

## Intent

Start after the local Head & Neck journey passes. Its public cutover can remain pending during Wave 2. Use that migration to triage the remaining collections and deliver the next light migration. Keep the ledger here as collections move.

## Acceptance Criteria

- [x] Reconcile the [dated census](../../../docs/gallery/existing-visualizations.md) with current package owners and the [collection destinations](../../../docs/gallery/migration.md#destinations). For each public experience, record its owner, old entry points, Gallery destination or retirement reason, and work item or acceptance evidence. Group duplicate entry points under the same experience.
- [x] Select and migrate the next collection that can reuse its present assets. Check its visitor task, exact Library revisions or parent exports, old bookmarks and file responses. Distinguish local acceptance from published readback. Retire superseded presentation files once readers and recovery have been checked.
- [x] Assign remaining light migrations to bounded items. Bring candidate rebuilds and their observed gaps to the Gallery walkthrough before setting their scope. Confirm that each publicly listable model in the collection maps to a Library lineage and revision, including unavailable exports. Report partial and missing ratings against this inventory. Link the remaining work for campaign closeout.

## Context and Trade-offs

Start with the existing collection owners for Anatomy Verification, Body & Heart, Airway, Dental and Body Systems. A published retirement notice such as FDI31 needs a destination check. Internal render tools and historical evidence keep their package owners.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Codex | — | deferred | Carry each public viewing experience from the census into a migration or retirement decision. |
| 2026-11-20 | Codex | deferred | wip | Head & Neck passed locally. Airway reviews and the coverage ledger are ready for the walkthrough. |
| 2026-11-22 | Codex | wip | done | Gallery release and both independent public handoffs passed readback. |

## Implementation Ledger

Head & Neck and Airway passed [public readback](#public-release-and-readback). They first passed [owner-only staging](#owner-only-staging--2026-11-22). Both [private legacy handoffs and their rollbacks](#legacy-host-release-rehearsal) passed. The [whole-Gallery release assessment](#whole-gallery-release-assessment) owns the public decision and the accepted walkthrough limitations. The ledger records destinations and specialist deferrals.

### Collection ledger

The dated census remains at its original revision. Use the sections below to follow the implemented dispositions and the next scoped work.

| Experience and owner | Old entry points | Gallery disposition and remaining acceptance |
| --- | --- | --- |
| [Model Survey and FDI31 retirement](../../../sites/anatomy-gallery/README.md#fdi31-prepared-specimen) | [Survey](https://med-assets-model-survey.landy123007.chatgpt.site/), family and FDI31 bookmarks, [focus retirement notice](https://dental-fdi31-focus-review-oct28.landy123007.chatgpt.site/fdi31/) | Asset Library, exact Balanced download, rubric and Experiments & Archive. [Wave 1](AG-GAL-001-name-and-verify-gallery.md). This wave read the 200 notice and verified both link destinations and the exact public Balanced GLB. |
| [Adrenal reviews and pilot](AG-GAL-002-absorb-adrenal-pilot.md) | Prior pilot's three bookmarks and Anatomy Verification candidate | Library, Use Cases, Compare and Stage round trips passed locally. Duplicate pilot retired in Wave 1. |
| [Head & Neck salivary review](../../../reviews/salivary_glands/2026-10-26-native-scoped-r02/README.md) | Home and review roots, annotation, native views, diagnostic and file bookmarks | [Head & Neck](AG-GAL-003-migrate-head-and-neck.md) owns the exact links, local verification and public v2 handoff. |
| Airway Review, owned by the [bronchial](../../../models/bronchial_tree/exports/authored-central-fairing-r13/README.md), [trachea](../../../reviews/trachea/2026-10-29-open-airway-r06/README.md) and [nasal](../../../reviews/nose_sinuses/2026-10-26-nih3d-airspace-r01/README.md) packages | [Bronchial homepage](https://anatomy-airway-review.landy123007.chatgpt.site/), [trachea r06](https://anatomy-airway-review.landy123007.chatgpt.site/review/trachea-r06/), [nasal airspace](https://anatomy-airway-review.landy123007.chatgpt.site/review/nasal-airspace-2026-10-26/) | Next light migration, verified on public Airway v8. |
| [Anatomy Verification](../../../tests/viewer/README.md) | [Review directory](https://anatomy-verification.landy123007.chatgpt.site/review/), [ledger](https://anatomy-verification.landy123007.chatgpt.site/review/accounting.html), candidate/supplement bookmarks, biliary and abdominal labels, bronchial r09, head labels, oral spaces, polish, spinal relationships, 2D teaching aids and trachea r05 | Compare reuses the adrenal and trachea r05 records and carries the remaining static findings and supplements from [AG-GAL-015](AG-GAL-015-verify-static-reviews.md). That item maps old page fragments and file URLs. Eye, knee and pharynx interaction choices go to the walkthrough, with test and review ownership in [AG-GAL-004](AG-GAL-004-consolidate-legacy-packages.md). |
| Body & Heart, owned by the [heart](../../../heart/) and [body](../../../body/) packages | [Cardiac imaging](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/), connected systems, 3D studio, marrow cutaway and the two pelvic review pages [listed in the census](../../../docs/gallery/existing-visualizations.md#hosted-page-readback) | Body Systems is the local teaching index. The studio and phase/slice interaction are [deferred](#deferred-specialist-journeys). The three scoped marrow and pelvic reports are available in [local Compare](AG-GAL-015-verify-static-reviews.md#body--heart). |
| Dental Review, owned by the [Dental Review Site](https://anatomy-dental-review.landy123007.chatgpt.site/) and the retained [UFF](../../../models/dental_specimens/uff_tomo1b/exports/r01/README.md) and specimen packages | [UFF review](https://anatomy-dental-review.landy123007.chatgpt.site/), UFF inspector, cotton tweezers, mouth mirror and earlier FDI31 interface evidence | The [static findings](AG-GAL-015-verify-static-reviews.md#dental-review) open in Compare. The loopback preview recovers both exact tool deliveries. The exact UFF revision and its Compare entry link the verified external inspector. Historical FDI31 r03 recovery awaits new evidence. |
| [Body Systems](../../../sites/body-systems-survey/README.md) and its local reference, surface, baseline and loopback reports | Dated report, optional same-case s1233, 3D launches, surface reports and adrenal blind study | Eleven systems render under Use Cases. Retain package-owned reports and receipts. [AG-GAL-005](AG-GAL-005-separate-body-systems-replay.md) owns display and replay, and [AG-GAL-006](AG-GAL-006-refresh-legacy-comparison.md) owns any editorial trial selected after the walkthrough. |
| Standalone teaching, owned by [lessons](../../../lessons/) and [diagrams](../../../diagrams/) | Arch identification, aortic locators, brain, ovary/tubal, pulmonary vein and the bilingual diagrams in the [census](../../../docs/gallery/existing-visualizations.md#standalone-lessons-and-diagrams), plus the Verification teaching supplements | [AG-GAL-016](AG-GAL-016-integrate-retained-teaching.md) records locally verified oral spaces, four locators, four bilingual pathways including lymph, interactive dental arch identification and the [skeletal relationship plates](AG-GAL-016-integrate-retained-teaching.md#legacy-teaching-supplements). One Breath, dental layer controls and authored dental shots are [deferred for rework](#deferred-specialist-journeys). The 2D atlas remains the regional source. |
| Package views, trials and archives, owned by [assemblies](../../../assemblies/), [reviews](../../../reviews/) and [experiments](../../../experiments/) | Kidney tiles, comparison plates, dental films/timing, FDI36 trial and dated planning reports | The local Experiments & Archive contains the [kidney outline trial, four dental treatment films and six restored Image 2.6 films](AG-GAL-016-integrate-retained-teaching.md#experiments--archive). Image 2.6 remains loopback-only. See the [public result](#public-release-and-readback) for the retained journeys. Retain rejected witnesses, authoring rigs, render checks, Object Library recovery and capture harnesses with their owners. They have no visitor route requirement. |

### Deferred specialist journeys

The maintainer deferred the interaction work on 2026-11-21. Place existing evidence in the ordinary Gallery now. Reopen a journey when the walkthrough identifies a teaching question worth rebuilding.

| Journey | Current material and disposition |
| --- | --- |
| Body & Heart studio and synchronized cardiac slice | The [imaging package](../../../heart/synthetic-imaging/beating-heart/imaging/README.md) owns the synthetic volumes and same-slice plate at reference frame 1. Use Cases and Cardiovascular lead to the plate at `/#/use-cases/heart-slice`. |
| One Breath phase and route controls | The [lesson](../../../lessons/one-breath/README.md) owns both languages, [storyboard](../../../lessons/one-breath/review/offline-storyboard.png) and replay. Use Cases and Respiratory lead to the original bilingual storyboard at `/#/use-cases/one-breath`. |
| Dental layer editing and authored shots | The [layer lesson](../../../lessons/dental-layer-controls/README.md) owns the review sheet at `/#/use-cases/dental-layers`. The [authored shot packages](../../../lessons/dental-animation/) own both FDI31 states and the two schematic posters at `/#/archive/dental-shot-studies`. The existing film archive serves the related cavity-filling and gum-disease films. |
| UFF native inspector | The exact specimen and Compare already show the static findings and link to the verified external inspector. Keep that bridge until a replacement or retirement is selected. |

[AG-GAL-016](AG-GAL-016-integrate-retained-teaching.md) owns local placement of the stills. [AG-GAL-017](AG-GAL-017-local-and-remote-storage-cleanup.md) owns the cleanup batch.

### Airway Review

The canonical journey starts at `/#/use-cases/airway`, also reached from the Respiratory Body Systems page. The public-mode cards lead to the nasal source specimen, trachea r06 and bronchial r13 reviews. In loopback the bronchial card opens the r14 first-fork lesson, which links the original r13 separately. The trachea review links the r05 cast as a distinct exact revision. Existing review images and geometry-bound projections supply the evidence and retain their original scope.

| Review | Library family and exact revision | Exports and rating |
| --- | --- | --- |
| `/#/compare/bronchial-r13` | `bronchial_tree/authored-central-fairing-r13` | Central fairing GLB, [11/16 for tracing the central fork](AG-GAL-018-reconcile-library-revisions.md#teaching-assessment-pilot). Family also lists the r09 frozen comparison input, r07 junction repair and r01 metadata cleanup by their exact files. |
| `/#/compare/trachea-r06` | `trachea/open-airway-r06` | Open and cutaway GLBs, Unrated. |
| `/#/compare/trachea-r05` | `trachea/host-conforming-cbands-r05` | Closed cast GLB, Unrated. Family also lists the r01 metadata cleanup. |
| `/#/compare/nasal-airspace-r01` | `nose_sinuses/nih3d-airspace-r01` | Airspace GLB, Unrated. Mucosa, bone and conchae have no export in this study. |

The frozen seed lists nine GLBs across the three families. The four original Airway review records cover five files (bronchial r13, both trachea r06 exports, trachea r05 and nasal r01). The other four are bronchial r07, r09 and metadata-cleanup r01, and trachea metadata-cleanup r01. R09 has its own Compare review and r07 is a separate study in the polish appendix. All five original review exports were available locally. The original reviews were unscored. The later teaching pilot assessed r13 for tracing the central fork.

Disposable Chrome opened the Respiratory link, exercised the three Airway review pages, decoded their retained displays, followed the revision handoffs and hashed the exact downloads. It followed r06 to the separately labeled r05 and back to r06. Seven lossless WebPs use the existing evidence; PNG derivatives preserve decoded pixels and SVG derivatives preserve the exact input digest and record their projection scope. Original published files and externally hosted pages remain under their existing owners. No duplicate tracked Airway shell was present to retire.

On 2026-11-20 the legacy home, nasal, trachea r06 and Verification r05 pages returned HTML. The direct bronchial review directory returned 404 while its homepage and individual payload URLs remained available. All thirteen Airway manifest objects and both separately linked r06 model URLs matched their expected identities after retry. The large bronchial GLB needed a longer read after returning a partial body.

The 2026-11-21 local teaching walkthrough reconfirmed HTTP 404 at the [legacy bronchial review bookmark](https://anatomy-airway-review.landy123007.chatgpt.site/review/bronchial-r13/) and 200 at the [legacy Airway homepage](https://anatomy-airway-review.landy123007.chatgpt.site/). The local Gallery's `/#/compare/bronchial-r13` loaded its evidence and the exact Library handoff. The rehearsal below supplies its compatibility candidate.

### Wave 2 review

The bronchial r13 Library entry and Airway card now use the retained r13 whole-tree view. Compare still opens with the frozen r09 close-up. The salivary r02 Library entry uses its front view of the exact glands-and-ducts export.

The assembly check reads the original transport manifests for bronchial r13, nasal airspace r01 and trachea r05, and the trachea r06 build record for its open and cutaway exports. Substituting a same-size model digest in the delivery index failed for each of the five exports. The ordinary build, twelve Site tests, local Chrome journey and payload-integrity gate passed.

### 2026-11-22 joint release rehearsal

Both collections passed the local rehearsal. The [private Gallery results](#owner-only-staging--2026-11-22) record the first hosted rehearsal. The [whole-Gallery release assessment](#whole-gallery-release-assessment) gives the current public release gates.

The Gallery source is `caa75100d141b42794c7bbbb142668c3a241b295`, following the clean `bdf5661` visitor walkthrough. The HTML is **4,811,318 bytes**, SHA-256 `63cd67c70ca3783d48cb12d4a17fa2f12e775314fa261c0c70eb66d4ec6d828e`. The [framework lock](../../../sites/anatomy-gallery/framework.lock.json) verifies the frozen ZIP, framework commit `f65265ca3c7d94790a86537e6ef725241fc012ea`, tree and protected runtime. An independent build from a fresh clone of the bundle matched byte for byte. The [restore tool](../../../transport/tools/restore_snapshot.py) separately reconstructed the immutable 520,272-byte seed, SHA-256 `340b64f3bd3b13835e16d29c9bcb415265d6be5fbf8195564c9c349390bc4499`. Assembly used the [viewer lock](../../../sites/anatomy-gallery/viewer.lock.json), restored media, Node 24.21.0 and the pinned npm lock. The Gallery app sources and indexed assets have zero changes from the source revision. The [compatibility module](../../../sites/anatomy-gallery/retirements/head-neck-airway/handoff.mjs) is separate from Gallery assembly.

#### Airway legacy entries

| Original URL or fragment | Rehearsed visitor action |
| --- | --- |
| Airway `/` | The compatibility link opens `/#/use-cases/airway`. `#title`, `#intro` and `#panels` offer the original `/#/compare/bronchial-r13`. Existing bilingual controls, detail toggles, full-width view, evidence and `/changelog/` remain available. |
| `/review/bronchial-r13/` | Use the r13 notice while this exact page is missing. If the original review returns, keep it and add the link to `/#/compare/bronchial-r13`. Child `payload/` requests keep their original file handler. The r14 loopback lesson keeps its independent default and r13 cross-link. |
| `/review/nasal-airspace-2026-10-26/` | Offer `/#/compare/nasal-airspace-r01` alongside the original bilingual, native source-direction views and records. The specimen shows airspace. |
| `/review/trachea-r06/` | Offer `/#/compare/trachea-r06`. Keep the bilingual raster comparison, five original raster files, attribution, evidence JSON and both model URLs. The Gallery comparison uses its separately bound geometry projections. |
| Verification `/review/trachea-polish-r05/#comparison` | Retain the Verification route and its links. Gallery visitors reach the separately labeled closed cast at `/#/compare/trachea-r05` via r06 or directly. Its Library revision is `trachea/host-conforming-cbands-r05`. |

#### File identity and observed service

| Pins and consumer | Rehearsal result |
| --- | --- |
| [Nine Head & Neck files](AG-GAL-008-retire-head-and-neck-host.md#2026-11-22-file-service-rehearsal) | Original data, manifest and Gallery delivery matched 9/9. |
| [Seven bronchial r13](../../../transport/manifests/82e41092aa325de95435e2488126d7dd70ab971f40ca2a993b95366caa6613d3.json) and [six nasal r01](../../../transport/manifests/9b98f353ee334e953d6ba5a81d4d6367337d1ebefab8ce77d4dc0a0d0ee251bb.json) | Their legacy scripts read the respective `data.json` and offer the pinned model and evidence links. Those URLs, display/source bindings and Gallery index agree. |
| [Two separately linked trachea r06 models](AG-GAL-014-compact-delivery-and-recovery.md#2026-11-22-retention-and-file-rollback-rehearsal) | Both legacy links and both exact Gallery downloads verified. Retain the legacy copies and the five exact legacy raster witnesses. |

The local HTTP stand-in and actual Gallery preview checked full status, type, size, SHA-256 and HEAD for every scoped pair. Gallery byte ranges matched the same body. All scoped manifest entries use identity transport. The guarded downloader's stable checks exercised the real manifest, source URL, transfer and decoded size/hash and format verification with the HTTP read redirected to the stand-in. The real redirect guard rejected cross-origin fallback to Gallery. Every scoped raster decoded locally. Four Airway PNG-to-WebP display pairs also matched the source RGBA pixels. The extra Verification r05 control exercised its exact GLB and seven PNGs locally, including one more lossless display pair.

**Read-only live evidence, 2026-11-22 China time.** Full identity GETs matched all 24 original file addresses (9 Head & Neck, 13 Airway manifest, 2 r06) and all 24 Gallery file addresses. Sixty-five additional legacy consumer records and manifests matched their declared digests, including two Head & Neck records after TLS retry. Five original trachea r06 PNGs matched the review's evidence JSON. Hosted Gallery GLB ranges returned 206 with the requested bytes. The six old-host GLBs returned 200 with full bodies when asked for a range. Both sides returned usable HEAD metadata after retrying one Gallery TLS error. The first Airway read could not connect to the configured proxy from the sandbox. Direct DNS was unavailable there, and direct HTTPS outside it met a Cloudflare 403. The configured network path outside the sandbox returned the results above. These connection failures do not establish the endpoints' status.

The hosted Airway homepage still returned 200 and the direct r13 page still returned 404, confirming the 2026-11-20 and 2026-11-21 observations. The hosted Gallery home returned a different HTML digest and the Gallery study API returned 404. Its asset index responded on retry. This establishes current file responses, with the candidate's hosted HTML and Worker acceptance still open. The separate r05 hosted control exposed eight Verification-origin 307s. The GLB's redirect target matched the exact bytes, but the guarded downloader refuses that cross-origin redirect. Probes for the two r05 metadata files at the review root returned 404. Both files returned 200 at the nested paths used by the page. [AG-GAL-015](AG-GAL-015-verify-static-reviews.md#verification-trachea-r05-hosted-control) tracks this independent Verification dependency.

#### Reversal and next decision

The stand-in used captured legacy HTML and public-style origins with local read-only Gallery snapshot and presentation responses. Chrome entered old paths and fragments, activated the links, reloaded, and used Back and the in-Gallery return links. The rollback restored the five original HTML responses and the original r13 404, rechecked the old file paths, then reapplied the handoff. The file service exercise independently restored the original gland and both r06 model paths after cross-origin or missing-backing failures. [Head & Neck rollback](AG-GAL-008-retire-head-and-neck-host.md#rollback) · [Airway file rollback](AG-GAL-014-compact-delivery-and-recovery.md#2026-11-22-retention-and-file-rollback-rehearsal)

Before public cutover, capture the current Gallery and legacy deployment revisions, HTML, snapshot, Worker bindings and original file mappings. Test the compatibility pages under their intended routing, script policy and cache behavior. Roll back a failed legacy handoff independently and recheck its pages and pinned file bodies. A Gallery rollback restores the preceding deployment, snapshot and presentation bindings. Host shutdown and storage consolidation have separate decisions.

The ignored rehearsal bundle records the rendered output, captures and dated response receipts. Gate results are 15 Site tests, two preview tests, two compatibility tests, the ordinary and bronchial Chrome suites, and the static-review suite with 19 entries and 216 exact identities. Payload integrity checked 443 offline tests and 936 hydrated LFS files covering 987,328,919 bytes. Net tracked LFS change is **0 paths and 0 bytes**.

#### Owner-only staging · 2026-11-22

**Access and storage.** The dedicated Site has one owner on the custom allowlist and zero editor, group or external visitor grants. A probe Worker verified D1 snapshot and presentation writes and an R2 object write, followed by a separate readback. The staging D1 held the probe table before candidate upload. The public Gallery D1 held its existing Data tables and had no probe table. The staged bucket lacked the recorded public snapshot. Signed-out requests to the staged home, study API, snapshot, presentation and a warmed GLB returned HTTP 401. A service caller could read the initialized presentation and received HTTP 403 on a write. Normal owner editing was unobserved in this run. See the [maintainer's disposition](#whole-gallery-release-assessment).

**Build and readback.** The candidate used the saved client build and the real Gallery Worker from source commit `7078f7fa95f263f2433ad47a90efd238834bb402` in the dedicated Sites repository. The stock Data source packager matched a closing-head string inside bundled JavaScript. An isolated copy of `package-data-app-for-sites-source.mjs` used the helper's existing HTML parser for the same one-marker, matching-digest check. Missing, duplicate and wrong markers were rejected. The reviewed HTML is 4,811,318 bytes. The staging archive contains 4,811,236 bytes of client HTML after removing the local chat marker. The raw deployed HTML includes the staging project marker and is 4,811,323 bytes, SHA-256 `b7f97c6d98bab7168d44609e655cb8d409dcc5317b3b34bf90348b2d84b359d7`. The ordinary browser response included Sites infrastructure and contained the exact compiled client module. The snapshot response matched all four queries and 238 rows. Study API SHA-256 matched `d4fe48e04512760d0fa6a97cc48f2f0e9e980b647978664f164a6e91f4fbf240`.

**File service.** All 24 primary pairs returned matching full bodies from the staged Worker and the original public file addresses. This covers nine Head & Neck pairs, 13 Airway manifest pairs and two separately linked trachea r06 models. A staged model byte range matched the local file. The staging bucket holds 78 verified objects for the two journeys and their shared screens, including 15 previews recovered after the first walkthrough. Other Gallery collections are outside the staging media scope. The same saved version was redeployed with temporary media upload authorization removed. The old token received HTTP 403.

**Visitor journeys.** Fresh disposable Chrome used the Sites service credential for the supported private origin. Both journeys opened from Use Cases, rendered their evidence, opened the exact Library entries and passed direct fragment loads, reloads, Back and in-Gallery returns. The Airway walkthrough kept the r05 cast and r06 open and cutaway exports distinct. The final run reported zero page errors and zero HTTP 503 responses on staged asset routes. The 15 Site tests, three local compatibility tests and repository offline gate passed. The offline gate covered 443 tests and 936 LFS pointer identities.

**Public readback at this stage.** The public Gallery home returned a different body and its study API returned 404. The legacy homes responded and the original bronchial r13 bookmark returned 404. The [legacy-host rehearsal](#legacy-host-release-rehearsal) supersedes the local-only compatibility evidence. The saved owner-only probe was the rollback point for this staging version.

### Legacy-host release rehearsal

The Sites connector confirmed owner access and successful deployments for all three public projects. Active HTTPS readback bound Head & Neck's v1 and Airway's v7 to their exact owner Git source. Five page responses matched after removing the Cloudflare-injected challenge script. Head & Neck's salivary URL originally served its root HTML through static routing. Airway served an empty 404 for the r13 page and still served its child payload files. The public Gallery snapshot and asset index independently matched the v7 evidence below.

| Origin | Observed public rollback point | Environment revision |
| --- | --- | --- |
| Head & Neck | v1 `2f2c2b03ac6cc77c09cff160f39d9e7f2ad40120`, deployment `appgdep_6adf0dc587b0819198b95ae6349df1f9` | 0 |
| Airway | v7 `8e97257fcffb01cc6f82402e426dc8f0f2acf5c2`, deployment `appgdep_6ae347f5e10081919001e8cef396288e` | 0 |
| Gallery | v7 `c0d43d1d372224bb0ecdb0e9a50c64aec44bebb7`, deployment and snapshot identities in the [publication record](../../../sites/anatomy-gallery/snapshot-reference.json) | 8 |

Two distinct Sites received static preview builds. Each project had a custom allowlist with the owner as the sole viewer and zero editors, groups and external grants. Before owner data was uploaded, the previews returned 401 signed out and served a marker with Sites service access. Their manifests use static `dist` delivery with no D1, R2 or runtime environment variables. The matching owner-source copies were saved as private v2 rollback baselines. Their six route responses reproduced the public results and all 24 pin bodies matched.

The private v3 builds use the exact legacy source and change only the six HTML page entries, including an explicit salivary review entry and the r13 notice. The sole preview-specific edit to the generated HTML is the Gallery destination origin. The offline production route map checked all six defaults, 25 named fragment cases and graceful fallback. The hosted pages returned the expected HTML after removing the platform injection. All 24 pairs returned 200, with the expected media type for each origin, exact byte counts and matching SHA-256 values. The six pages and all six scoped model paths returned 401 signed out. Chrome followed the six hosted entry points, checked the named fragments, opened the destination headings and exercised reload and Back. Chrome passed the bilingual toggles on five retained HTML entries, the Head & Neck and Airway width controls, and the default links with JavaScript disabled. The hosted checks used Sites service access. Chrome saved both exact r06 GLBs from the public legacy origin. Native saves from the private copy canceled under service access even though same-origin browser GETs and the pinned file readbacks succeeded. See the [maintainer's disposition](#whole-gallery-release-assessment).

Each private v2 redeployment independently restored its original route bodies and pins while the other handoff and the Gallery study API remained available. Head & Neck restored both HTML pages and nine pins. Airway restored the three successful HTML pages, the original r13 404 and 15 pins. Both private v3 versions were reapplied and all six hosted entries matched again. A fresh public read reproduced the legacy baseline and Gallery snapshot. For a future public rollback, redeploy only the affected origin's bound preceding version, then verify the exact pages and files on that origin. Restore Gallery v7 with its binding and state record if the Gallery release itself fails.

| Scope | Recommendation |
| --- | --- |
| Head & Neck | **Private handoff verified. Release after public Gallery acceptance.** Both private entries and nine file pairs passed. Keep the original file URLs and restore public v1 if its future handoff fails. [Head & Neck file and shutdown decision](AG-GAL-008-retire-head-and-neck-host.md#hosted-rollback-point) |
| Airway | **Private handoff verified. Release after public Gallery acceptance.** All four private entries and 15 file pairs passed. Keep the legacy model addresses and restore public v7 if its future handoff fails. [Airway file retention](AG-GAL-014-compact-delivery-and-recovery.md#hosted-file-service-result) |
| Joint release | The [whole-Gallery assessment](#whole-gallery-release-assessment) records the private qualification and the authorized public sequence. The Gallery passed first, followed by Head & Neck and then Airway. |

The local handoff suite passed three tests. An independent replay against owner source checked the six production routes. The repository offline gate passed. The scoped tracked changes are the four release records and add zero LFS paths or bytes.

### Whole-Gallery release assessment

**Private qualification checkpoint, 2026-11-22.** The 245 new content-addressed routes were unverified in the production bucket at this checkpoint. Public v7 only served its listed assets, and the connected Cloudflare account could not list the Sites-managed bucket. The maintainer subsequently authorized bounded preparation on the existing Site and made the four retained visitor journeys the release gate. Optional unavailable images can be omitted or marked unavailable when the lesson or review remains usable. The [public result](#public-release-and-readback) supersedes this checkpoint.

**Candidate.** The dedicated owner-only **Anatomy Gallery Release Staging** Site serves v3 from private source `dd3355b070b4935c641cb4cc3fc0450bb0b656c6`, deployment `appgdep_6b026cab87a881919ceef500d646b99b`. The build overlays the bookmark fix on release review `13d8318`, using its locked framework and immutable seed. The compiled client module matched before packaging and in the served HTML, SHA-256 `081aff2016c43c7b4e31820feb7b9f4e6a0b9f668591d470fb9b5e646cff69c5`. Open **Use Cases** to start the walkthrough. The two legacy previews remain available.

| Check | Result |
| --- | --- |
| Bookmarks | Asset Library opens at the root. The authored path and the origin-specific short link open the original **Collection at a glance** with highlight and focus on direct visits and reloads. Chrome exercised Back, family and FDI31 links on the packaged client and staging. The local rehearsal used the public origin and its existing short ID `Rdo55Ten`. The same regression check reproduced the missing highlight on staging v2. |
| Public v7 baseline and additions | Live saved version, index and snapshot matched the [public rollback record](../../../sites/anatomy-gallery/snapshot-reference.json). All 1,001 retained routes preserve name, hash, size and media type. All 1,001 live HEAD responses matched the expected length, media type and SHA-256 ETag. Three manifest source paths moved within the repo and the payload inventory is identical. For the 245 new keys, **0 verified present, 0 confirmed missing, 245 unverified**. The connected Cloudflare account could neither resolve the Sites Worker nor list its R2 buckets. All 245 keys fall outside v7 and have no retained alias, so v7 route 404s cannot answer the production storage check. |
| Private media and journeys | Filled 523 gaps from verified originals and read back 601 full objects, including all 245 additions, with exact hashes. Chrome exercised the six Survey slices, legacy heart preview, Library search and Back, cardiovascular, lymphatic and endocrine plates, adrenal Compare and shared 3D Stage state. No asset 503s occurred in that walkthrough. The broader loopback suite passed, including local-only, archive and missing-media journeys. |
| Exact download and state | Chrome saved `FDI31-balanced.glb` from public v7 and private v3. Both matched 2,052,220 bytes and SHA-256 `90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7`. Staging study API, snapshot, asset index, range and ETag passed. The snapshot retained 238 rows across four queries. Presentation remained at revision 0 with empty overrides. Signed-out home, API, bookmarks and the exact file returned 401. |
| Accepted limitations | The maintainer accepted unobserved normal-owner Gallery editing and the canceled native r06 saves from the private Airway copy under service access. Exact r06 file reads and saves from the public Airway origin had already passed. No owner action is required for either observation. Specialist deferrals and loopback-only routes retain their recorded scope. |

The final v3 uses environment revision 4 with the temporary media upload settings removed. The old media credential received 403. Final readback matched the reviewed client, exact FDI31 and the public v7 index, snapshot and presentation baselines. Both owner-only legacy previews answered.

Keep staging v2 at `7078f7fa95f263f2433ad47a90efd238834bb402` as the private rollback point and public v7 at `c0d43d1d372224bb0ecdb0e9a50c64aec44bebb7` with environment revision 8 as the Gallery rollback point. Restore each legacy origin independently under its own receipt. Qualification receipts, the archive and private walkthrough entry are retained in `.artifacts/gallery-release-rehearsal/qualification/`. The [bookmark replay](../../../sites/anatomy-gallery/tools/verify_survey_bookmarks.mjs), repository offline and payload-integrity gates passed. Net tracked LFS change is **0 bytes**.


### Public release and readback

The integrated source was `5f8fddf247abcf358d77dba19700b8e80af4967f`, including the [authoring scaffold](../../../docs/gallery/README.md), the Body Systems prompt placement at `ac9324b`, and the [storage disposition](AG-GAL-017-local-and-remote-storage-cleanup.md) at `65b30fd`.

| Live origin | Saved version and Site source | Deployment | Independent rollback |
| --- | --- | --- | --- |
| [Anatomy Gallery](https://med-assets-model-survey.landy123007.chatgpt.site/) | v10, `ae6c41ffe395e7f4cb9bf21eb7aec52e081d39f9` | `appgdep_6b027d3831c48191b1b8c66fda641c00`, environment revision 12 | Gallery v7 `appgprj_6aed57a59dc88191a981c07e56d283e7~appgver_01c2c0795d64819189e2e8832c25c61a`. Use the existing DB and BUCKET and confirm the Survey and presentation with the [snapshot record](../../../sites/anatomy-gallery/snapshot-reference.json). |
| [Head & Neck](https://anatomy-head-neck-review.landy123007.chatgpt.site/) | v2, `2575a389d98225f6e2bd59bddf548613417fb0e4` | `appgdep_6b027e0fc93c819197b92955fe6aed65`, environment revision 0 | Head & Neck v1 `appgprj_6adf0c550fb08191b58c3389c0d48f8a~appgver_de7cbf6adabc8191a61faee3efba47cf`. Recheck two pages and nine pins. |
| [Airway](https://anatomy-airway-review.landy123007.chatgpt.site/) | v8, `65eac76d92756121c646e2933718330cfe2d0685` | `appgdep_6b027f317e608191866686ce7ecad6fa`, environment revision 0 | Airway v7 `appgprj_6adebb2703888191895bb93c431e82c4~appgver_1cc05d692afc8191a809a533a5a3c931`. Recheck the three successful pages, the original r13 404 and 15 pins. |

- **Preparation.** The first production preparation version returned 503 at the Survey home because the repackaged v7 HTML omitted five archived whitespace bytes. The upload process stopped before its first write. The v7 rollback passed eight live controls. The corrected prep version matched the exact archived markup, passed the same controls and accepted 245 media objects plus the Gallery HTML and snapshot from verified local originals. The 247 writes totaled 37,539,485 bytes. Removed both temporary upload settings before Gallery deployment and confirmed the two prep endpoints returned 404.
- **Gallery.** Signed-out Chrome passed the Library exact r05 export, Use Cases lesson stops, Compare with and without its optional section image, and a shared Stage view in a fresh context. The [old Survey bookmark](https://med-assets-model-survey.landy123007.chatgpt.site/_data/components/Rdo55Ten), the FDI31 Balanced download and the compiled client, study API and assets index passed. The four snapshot queries retained all 238 rows. Presentation revision 0 and its empty overrides matched the preflight.
- **Legacy origins.** Signed-out Chrome opened all six handoff entries, followed their Gallery destinations, reloaded and returned with Back. The two Head & Neck pages and nine file bodies passed first. Airway then passed all four pages and 15 files, including both original r06 model addresses and the former r13 404 bookmark. Attribution and original download backing remain with the owners. The [Airway storage decision](AG-GAL-014-compact-delivery-and-recovery.md#decision--retain-the-public-airway-downloads) and [Head & Neck shutdown item](AG-GAL-008-retire-head-and-neck-host.md) remain separate.
- **Verification and evidence.** The integrated offline and payload gates passed 441 tests and 936 indexed LFS files totaling 987,328,919 bytes. The packaged app passed 15 tests and the local browser check passed all four surfaces and the Survey bookmark. Release archives, immutable upload receipts, and fresh HTTP and browser observations are in the ignored `.artifacts/gallery-production-release/` bundle. The earlier accepted limits on fresh owner editing and the private r06 save remain in the private qualification above.
