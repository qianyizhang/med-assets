# Gallery routes and API

Anatomy Gallery uses the existing Site and serves one HTML application. A page link identifies where a visitor was working. An asset URL identifies exact bytes. An API response supplies data. Preserve these three contracts independently when adding a collection or migrating a host.

Assembly selects the candidate or the last approved public release. The Library, study API and read routes use that build’s selections at every origin. The candidate Worker and loopback preview use the same handler for models, evidence and byte-pinned receipts. The published rehearsal reproduces the recorded v10 source and its delivery declarations. [Build and preview](../../sites/anatomy-gallery/README.md#restore-and-build-locally)

Both selections serve the exact tracheal cutaway GLB. In v10 One Breath opens its storyboard. The candidate adds interactive tracheal Stage presets and retains the storyboard. A v10 visitor can still use the adrenal Stage.

## Page links

Open the fragment on the Site root, for example `/#/library/s1233-adrenal/r05`. The pinned Data Site shell can append `?view=1` before the fragment. This marks a complete dashboard state, including its defaults, for recipients with saved dashboard settings. Gallery links can omit it. The browser owns the fragment, so a deep link, reload or Back navigation can use the same Worker entry. [Legacy file delivery](../../transport/README.md#legacy-file-addresses) owns original model and evidence URLs.

| Address on this Site | Visitor action and owner |
| --- | --- |
| `/#/library` | Browse the Asset Library. Fragment parameters preserve `q`, `system`, `purpose`, `kind`, `state`, `rating=rated\|unrated`, `layout=list\|tree\|cards` and `sort=name\|name-desc\|rating-high\|rating-low\|most-files\|fewest-files`. Example: `/#/library?rating=rated&sort=rating-high`. |
| `/#/library/s1233-adrenal/r05` | Open the exact revision. Its package owns the bytes and its dated assessment owns the score. The existing survey IDs still open the family or package. Use the revision history to choose a specific export. |
| `/#/use-cases/systems`, `/#/use-cases/systems/<system-id>` | Open the Body Systems collection or a system assembly. The optional fragment parameter `detail` selects a teaching detail. Reproductive `reproductive-female-left-pickup` opens the shared ovary lesson in the system sequence. |
| `/#/use-cases/adrenal-localization/region`, `…/right-gland` | Open the authored regional or isolated lesson stop. Each pins s1233 r05. |
| `/#/use-cases/head-and-neck/location`, `…/duct-course` | Locate the three major gland pairs and trace the supported parotid surface course. The duct stop links the excluded submandibular course to Compare. |
| `/#/use-cases/right-arm/elbow`, `…/shoulder` | In the candidate build, locate the elbow nerve or shoulder cuff against shared bones. The base route opens the elbow stop. Each question has unlabelled layers and an optional labelled answer. |
| `/#/use-cases/oral-spaces`, `…/en`, `…/zh` | Locate the vestibule in the English or Chinese r01 cutaway. The base address opens English. Use Cases and Head & Neck both link here. The cutaway keeps the originating duct stop with `from=duct-course`. On Head & Neck, `oral=zh` carries the visitor back to the Chinese cutaway. |
| `/#/compare/teaching-target?round=reopened` | Local matched comparisons for the second review of 20 families. Add `&asset=SHA256` for one edition. |
| `/#/compare/teaching-target?asset=SHA256` | Local before/after review for a maintained teaching file, including its task and any axis exemptions. |
| `/#/library/FAMILY/REVISION?file=SHA256` | Select one exact download and assessment inside a multi-export revision. |
| `/#/use-cases/regional-locators`, `…/aortic-arch`, `…/pulmonary-vein`, `…/brain-source-cut`, `…/ovary-tubal-context` | Open the locator collection or a specific stop. The Cardiovascular and Nervous pages link to their regional stops. The ovary lesson also opens inside Reproductive, retaining that collection’s navigation. |
| `/#/use-cases/biliary-pathway/en`, `/#/use-cases/testis-pathway/en`, `/#/use-cases/urinary-outflow/en`, `/#/use-cases/lymph-collecting-routes/en` | Open the bilingual figures. The base addresses open English and `/zh` opens Chinese. The optional `from` identifies a detail in the associated Body Systems assembly. The lymph figure offers optional directional motion. |
| `/#/use-cases/dental-arch`, `…/upper`, `…/lower` | Identify a source-labeled crown in either arch. The English and Chinese lesson keeps a selected tooth per arch while open. Missing images leave the FDI selector available. |
| `/#/use-cases/heart-slice`, `/#/use-cases/one-breath` | Read the original synthetic cardiac slice or follow the bilingual breathing lesson through mechanics, airway and exchange. One Breath retains its original storyboard for comparison. The pages return to Cardiovascular and Respiratory, respectively. |
| `/#/use-cases/ultrasound`, `/#/use-cases/ultrasound-abdomen/gallbladder` | In the candidate build, open the ultrasound tour collection or identify the gallbladder in the first authored view. The base Abdomen route opens the gallbladder stop. |
| `/#/use-cases/ultrasound-assets`, `…/gallbladder`, `…/liver`, `…/probe`, `…/scan` | In the candidate build, inspect the assets used by the Abdomen stop. The optional `from=gallbladder` restores that stop on return. |
| `/#/use-cases/dental-layers` | Compare the prepared FDI31 specimen's source pose and isolated layers in the original control review sheet. Open its exact Balanced download through the Library record. |
| `/#/use-cases/skeletal-relationships`, `…/second-costal`, `…/l3-l4-disc` | Open the two contextual plate studies. The optional `from` preserves a named Skeletal Body Systems detail. The base address opens the costal study. |
| `/#/library/cartilage-assembly/second-costal-2026-10-23`, `…/l3-l4-disc-2026-10-23` | Open the exact Library export for each skeletal study and return to its relationship plates. The optional `from` carries the originating skeletal detail through the Library round trip. |
| `/#/compare` | Discover saved reviews by collection. The static batch opens at stable finding IDs listed in the [review ledger](../../records/work-items/items/AG-GAL-015-verify-static-reviews.md). |
| `/#/compare/polish-appendix`, `…/parathyroids`, `…/bronchial`, `…/esophagus` | Read the original appendix in section order or reopen one section directly. Each section provides its own exact Library handoff. |
| `/#/compare/fdi31-interface-locked`, `/#/compare/fdi31-source-layers-r03` | Inspect the interface candidate or the earlier source-layer plate. The Balanced specimen remains on `/#/library/swirendo_fdi31`. |
| `/#/library/<family>/<revision>` | Open a named revision or package delivery. Search the filename or full path to reach its record, or follow the family’s revision history. The record gives the byte count and SHA-256 and links the owning evidence. An unavailable export shows its recorded identity and availability. |
| `/#/library/cardiac-exterior`, `…/static-opaque-exterior-r02` | The candidate Gallery opens the recommended static r02 export. `…/static-opaque-exterior` still opens the exact original r01 and `…/animated-source-opaque-exterior` opens the repository-source animation. |
| `/#/library/uff_tomo1b/r01`, `/#/library/dental_specimens` | Open the same UFF Tomo1B revision. Either catalogue ID finds the one Library entry. |
| `/#/library/cardiac-atlas/great-vessels-ed-r01`, `…/wall-motion-shared-r01` | In the candidate Gallery, inspect two studies from one editable Cardiac Atlas. Both original static and animated families retain their exact-revision bookmarks. |
| `/#/library/cardiac-animated/fitted-canonical` | Inspect the identity and provenance of the unavailable fitted Site animation. The original authored animation variants are under `…/repository-source`. |
| `/#/compare/salivary-native-r02` | Inspect the rejected original-source crossing and the scoped r02 review. |
| `/#/library/salivary_glands/z-native-scoped-r02` | Get the exact glands-and-parotid-ducts and same-source context exports. The family route also opens this record. |
| `/#/use-cases/airway` | Select the nasal airspace, trachea or bronchial fork. It is also reachable from Respiratory Body Systems. The candidate bronchial card opens the first-fork lesson. |
| `/#/use-cases/airway/first-fork` | Candidate lesson with a 3D view of first-fork fairing r15, an exact Library link and the saved original r13 comparison. |
| `/#/library/bronchial_tree/distal-sampling-r14` | Retained exact r14 model and download. The candidate family opens `…/first-fork-fairing-r15`. `…/authored-central-fairing-r13` opens the original export and its assessment. |
| `/#/compare/nasal-airspace-r01`, `…/trachea-r06`, `…/bronchial-r13`, `…/trachea-r05` | Read the revision-specific findings and open the associated exact Library record. The r05 cast and r06 shell have separate evidence and exports. |
| `/#/compare/adrenal-r04-r05` | Open the blind review. A shared comparison records `finish=tissue\|neutral` and `order=ab\|ba` in the fragment query. Both witnesses use the recorded camera. The findings and scores belong to the saved review. |
| `/#/compare/adrenals__source-candidate-01` | Read the single-export BodyParts3D review, inspect the exact retained WebP witnesses and return to the same Library family. An unavailable witness leaves its caption, the other evidence, and the links to the review owner and family available. |
| `/#/stage/adrenal-v1?view=<encoded JSON>` | Restore a pinned scene recipe and exact export. An optional encoded `from` carries a supported referring Library revision, lesson stop or comparison with its finish and side order. Bare `/#/stage` opens the authored starting view and also accepts a local GLB. |
| `/#/stage/cardiac-exterior-v1?view=<encoded JSON>` | Restore the candidate-only static r02 model, selected structure and camera. An optional encoded `from` returns to its exact Library record. |
| `/#/stage/bronchial-first-fork-v1?view=<encoded JSON>`, `…/bronchial-first-fork-v2?view=<encoded JSON>` | Restore the candidate r14 model with v1 or r15 with v2, including its shared camera and appearance. The optional encoded `from` returns to the first-fork lesson or exact Library record. |
| `/rubric` | Stable public rubric address. GET or HEAD returns 302 to `/#/rubric`. The build reads the [canonical rubric](../guides/asset-quality.md). |
| `/#/archive/kidney-outline-trial` | Compare the HRA female left-kidney exterior and isolated shapes. Start with `view=exterior\|internal\|paired`, `outline=0\|1` and `lang=en\|zh` in the fragment query. |
| `/#/archive/dental-video-treatments`, `…/hyperframes`, `…/remotion`, `…/manimgl`, `…/comparison` | Play the four exact reviewed exports with shared narration, captions and the original study records. |
| `/#/archive/dental-image26`, `…/combined`, `…/<story-id>` | Open the combined film or a named Image 2.6 story. The preview uses the verified teaching backup members. The transcript and provenance are available if playback fails. |
| `/#/archive/dental-shot-studies` | Inspect the authored FDI31 poses and schematic caries and periodontal posters. Follow links to the original packages or the related Image 2.6 films. |
| `/#/archive/planning` | Open the dated survey with Overlaps selected and Coverage and Gaps available. Discover it from **Use Cases → Experiments & Archive**. |
| `/?view=1#swirendo_fdi31`, `/#family-<id>` | Open the selected family in the ordinary Asset Library. The FDI31 bookmark still offers the verified Balanced download. |
| `/_data/components/survey-coverage`, `/_data/components/<origin-specific short ID>` | Open the dated Survey coverage page and focus **Collection at a glance**. The framework generates the short ID from this Site's origin. |
| `/#family-adrenals`, `/#candidate-adrenals__source-candidate-01`, `/#refinement-surface-adrenal` | Open the BodyParts3D family in the Library, exact BodyParts3D review, and related s1233 comparison, respectively. The two reviews each link back to the selected family. |

The released Head & Neck and Airway handoffs map the [salivary fragments](../../records/work-items/items/AG-GAL-003-migrate-head-and-neck.md#2026-11-22-release-rehearsal) and [Airway bookmarks](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#airway-legacy-entries). The old bronchial bookmark opens the exact r13 review in either Gallery mode. The separate first-fork teaching lesson belongs to the candidate build. [Public readback](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback)

### Legacy page handoffs

The [collection ledger](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) records each former experience's Gallery destination and retained external viewers. Before replacing a consumed page address, test its path and fragments through the destination, reload, Back and return links. Match handoff rules to the named HTML paths. Retire internal beta aliases when their readers move under the [retention policy](../WORKFLOW.md#retention).

Keep page and file mappings independently restorable. After a failed handoff, restore the previous page mapping and recheck its bookmarks and pinned file responses. A Gallery rollback also restores its snapshot and presentation bindings. The [public release record](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) identifies the independent rollback points. Replacing a retained specialist viewer requires checking its selected interactions and saved state. Full host shutdown has its own [consumer and recovery decision](../../records/work-items/items/AG-GAL-008-retire-head-and-neck-host.md).

## Data and file endpoints

| Request | Response and failure behavior |
| --- | --- |
| `GET /api/gallery/v1/studies` | Read-only JSON with the schema version, authored lessons and saved reviews with exact export hashes. Ordered stop IDs identify child routes. The cardiac slice, One Breath storyboard and dental control sheet have empty stop lists because their base routes open the full lesson. Body Systems plates are assembled from [the Body Systems display index](../../lessons/body-systems/display/index.json) at build time. HEAD has the same status and no body. Other methods return 405. Assembly compiles the selected [study catalogue](../../sites/anatomy-gallery/app/src/content/gallery/catalog.js) into the release. |
| `GET /assets/index.json` | Site delivery declarations with filenames, sizes, media types and SHA-256 values. This is a file index. The Library's lineage, editorial review and lesson records provide different information. A declared route can precede upload. |
| `GET /assets/<sha256>/<name>` | Exact file bytes. HEAD, byte ranges, ETag and conditional reads follow the [asset handler](../../sites/anatomy-gallery/app/src/content/shared/r2-assets.js). An unknown route returns 404. A declared object with absent or mismatched storage metadata returns 503. The shared scene also checks byte length and SHA-256 before decoding. |
| `PUT /assets/<sha256>/<name>` | Existing guarded upload flow. Requires owner or time-limited upload authorization and checks the declared size and digest. [Storage policy](../../transport/README.md) |

The protected framework owns snapshot, presentation and deployment endpoints. The Survey seed supplies the dated Planning and Archive data. The [read-only local preview](../../sites/anatomy-gallery/tools/preview_gallery.mjs) supplies verified local bytes to the selected build’s read handler. Restored Image 2.6 films and legacy Dental Review files use optional local storage. The public index declares which digest and filename pairs are eligible for owner upload.

The candidate read handler serves the [static heart r02 GLB](../../heart/exterior-presentation-r02/README.md) through R2 or the preview’s local adapter. Missing storage, a Git LFS pointer or mismatched bytes return 503. The route is outside the public asset index and becomes usable in the running preview as soon as the exact local payload is restored.

The local `#/compare/teaching-refinements?asset=<control-sha256>` route opens the evidence for the selected starting file. The stomach and gallbladder Stage presets preserve the selected source or section group. The cardiac wall preset also preserves its normalized cycle phase. The [recovery instructions](../../reviews/teaching-assessments/refinement-economy/README.md#serve-recovered-candidates-locally) describe how candidate downloads become available from the loopback preview.

## Sharing and authorship

**Share this view** produces an immutable URL directly in the browser. Its version, revision, exact model hash, selected part, tissue or neutral material, key light, orthographic camera position, target and vertical field determine what reopens. The v1 recipe fixes model placement, background, secondary lights, projection and a 1200 × 960 WebP export. Keep this decoder and these defaults when adding a new version. Invalid or unavailable inputs have explicit recovery states. A local file can be inspected and exported. Sharing it as a gallery preset requires an addressable gallery revision.

The WebP export embeds the preset URL and renderer identity as XMP metadata. An export of a device-local model records its filename in place of a shareable URL. Reviewed Blender images retain their original evidence bindings. [WebP container and XMP](https://developers.google.com/speed/webp/docs/riff_container#metadata)

A visitor can share a view or the exact arrangement of a blind comparison without an account or server write. A maintainer chooses which preset a published record uses. Publishing a finding requires an authored review with inputs, evidence and attribution. A lesson author adopts an updated revision independently.

## Decisions for subsequent migrations

Add a study to the read API when it has an owned lesson or review. Extend the preset schema when a lesson needs new reproducible state, such as a cardiac phase and slice plane. A catalogue API for cross-client asset discovery is a separate design decision once the package-to-lineage reconciliation is ready. The present study API promises only the authored studies listed above.

Use the [ordinary authoring and browser check](README.md#author-a-gallery-entry) to verify a new or updated handoff. The full browser journey also exercises invalid presets, local GLBs, the rubric and legacy bookmarks.
