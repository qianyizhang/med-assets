# Gallery product requirements

Anatomy Gallery brings the maintained public views of med-assets into one Site. Its landing page should offer two ways in. Asset Library helps visitors choose something to reuse, and Use Cases shows what they can teach with it. A visitor should be able to move from either entrance to the exact asset revision, teaching stop and supporting review without knowing how the repository stores or delivers them. The current Site opens directly on Asset Library. [Implemented routes](routes-and-api.md#page-links)

| Surface PRD | Visitor’s question | Record it owns |
| --- | --- | --- |
| [Asset Library](asset-library.md) | Which asset and revision can I reuse? | Curated index and asset pages |
| [Use Cases](use-cases/README.md) | What does this teach, and what needs work? | Collections, teaching sequences and their Development views |
| [Compare](compare.md) · Tool | What changed, and does it matter? | Comparison session and saved review |
| [3D Stage](3d-stage.md) · Tool | How do I compose, share or export this view? | Versioned preset and its exported image |

The [gallery-wide design guide](design.md) owns navigation, view choice and presentation across these surfaces. Asset packages own their exports and credits. Reviews own evidence and decisions. Each surface links back to the identified record.

Use the [glossary](../../GLOSSARY.md#gallery-and-surfaces) for canonical names. The [inventory](existing-visualizations.md) records the pre-migration baseline. The [collection ledger](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) records implemented destinations and retained external viewers. The [route guide](routes-and-api.md#legacy-page-handoffs) owns page compatibility and the [campaign](../../records/campaigns/anatomy-gallery-consolidation.md) records completion and follow-up work.

## Site and media governance

Publish all public gallery experiences on the existing Site as [Anatomy Gallery](../../sites/anatomy-gallery/README.md). Model Survey remains the name of the dated catalogue. Asset Library and Use Cases are the two main entrances. Compare and 3D Stage open from the relevant asset, review or lesson stop and from Tools. Retained external tools have an explicit disposition in the collection ledger. Each Gallery experience has its own address on this Site and completes its visitor task there. Old addresses can continue serving bookmarks and exact evidence.

Asset Library should make every publicly listable, independently reusable asset discoverable, including those first encountered inside an assembly, lesson or review. The [Library requirements](asset-library.md) define what gets its own page. Every public interactive 3D showcase uses the shared 3D scene presentation owned by 3D Stage. A visitor can inspect the scene in context or open the same preset in Stage. A lesson or saved review retains control of its narrative, sequence and evidence.

Follow the [display image policy](design.md#display-images) and the [storage and delivery policy](../../transport/README.md) when adding or migrating a surface.

## Author a Gallery entry

Start with an exact asset revision and a visitor question. The package owns the asset, exports and credits. The review owns the finding, evidence and limits. Use the [review promotion workflow](../guides/teaching-assessments.md) for an accepted task and the [Gallery release inputs](asset-library.md#making-a-release-selection) for its package and resources. Keep existing route IDs when updating an entry. Adding a candidate resource and admitting a public download are separate decisions. Use the maintained s1233 adrenal study as a [working example](../../sites/anatomy-gallery/app/src/content/gallery/adrenal-study.js). Its Library record, lesson stops, comparison inputs and Stage version all run in the ordinary Gallery.

| Surface | Minimal scaffold | Add it to the ordinary Gallery |
| --- | --- | --- |
| Asset Library | Copy the shape of the seated nail record in [reviewed entries](../../sites/anatomy-gallery/app/src/content/gallery/reviewed-entries.json) for a single reviewed export. Supply a stable ID, name, category, use, limits, exact export, portrait and review. Record only assessed axes. | The release compiler includes these reviewed entries in the selected Library. The browser opens `#/library/<id>`. For a revision series, use the s1233 Library record above. Keep each rating on the revision the review assessed. |
| Use Cases | Use the s1233 lesson stops for a model-backed lesson. Each stop has an ID, label, instruction and initial selection. Use the [retained still lessons](../../sites/anatomy-gallery/app/src/content/gallery/SpecialistStills.jsx) for an image-led stop with a source link. | Link the lesson from [Use Cases](../../sites/anatomy-gallery/app/src/content/gallery/UseCases.jsx) or its owning collection and register its route in [Gallery](../../sites/anatomy-gallery/app/src/content/gallery/Gallery.jsx). Expose stable stop IDs through the [study catalogue](../../sites/anatomy-gallery/app/src/content/gallery/catalog.js). Link the exact Library record and the saved review. |
| Compare | Use the [static review records](../../sites/anatomy-gallery/app/src/content/gallery/static-reviews.json) for an evidence page. Bind the review record, revision, section, witness and finding. Use the s1233 pair for a matched revision comparison with shared ordering and finish. | Static review records already feed the Compare index, page and study API. Use the shared [Evidence](../../sites/anatomy-gallery/app/src/content/gallery/Evidence.jsx) view so an unavailable optional image leaves its caption and the source link reachable. |
| 3D Stage | From an exact model-backed record or lesson stop, open **Inspect in 3D**, then **Open in 3D Stage**. Frame the question, choose the part and appearance, and save **Share this view** and **Export WebP**. The URL is the preset. It stores the exact export and camera, with an optional return path. | Use [the existing Scene](../../sites/anatomy-gallery/app/src/content/gallery/Scene.jsx) or link the saved preset. The [preset codec](../../sites/anatomy-gallery/app/src/content/gallery/presets.js) binds the allowed version, model and return destinations. Use a new version for a new scene recipe. The s1233 scene record is the minimal example. |

Build and serve the [ordinary Site locally](../../sites/anatomy-gallery/README.md#restore-and-build-locally). Run the [focused browser journey](../../sites/anatomy-gallery/README.md#recipes-and-checks) to search the Library, download the exact r05, follow its lesson into Compare, and find the review while an optional section image is unavailable. Open the same r05 in Stage, share the view, reopen it in a fresh session and check the part, appearance and camera. The WebP embeds the shared URL and the view returns to the originating stop.

## Milestones

The published Gallery includes both adrenal journeys. The [release readback](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) exercised the s1233 journey through all four surfaces. The s1233 lesson and revision comparison support shareable versioned views and WebP export. The BodyParts3D family opens its exact source review and keeps a return path to the selected family. The [routes and API](routes-and-api.md) describe the compatibility bookmarks. Existing Blender renders, sections and photographs keep their original evidence bindings.

General two-model comparison and author adoption of a newer lesson revision are product requirements. Schedule them with the first collection that needs them. The [route contract](routes-and-api.md) identifies the authored journeys available today.

**Library coverage.** Follow the [Asset Library coverage rules](asset-library.md#review-coverage) for exact-file selection and rating counts. The [teaching asset review campaign](../../records/campaigns/teaching-asset-review.md) owns collection order and progress.
