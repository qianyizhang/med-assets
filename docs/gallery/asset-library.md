# Asset Library PRD

**Outcome.** A visitor can find a reusable asset, choose an exact revision and see what it contains, where it is used and what evidence supports reusing it. The Asset Library is the index. Each independently reusable asset lineage has one asset page with its revision history, parts, uses and exports.

## What the visitor sees

List every publicly listable reusable asset, including assets encountered in assemblies, lessons or reviews. A name, anatomy or use can connect several independently sourced lineages in the index. A new export, language, format, pose or review stays with the lineage when it shares the maintained asset. Give a component its own page when it has independent reuse and a maintained identity. A part available only within a parent revision opens the parent asset page at the exact revision and selects the part. Keep known public entries visible with their actual export availability and review status.

Use kind, authoring method and export format as separate filters in the Library. On the asset page, describe them for the selected revision.

| Information | What it tells the visitor |
| --- | --- |
| Kind | What is reusable, such as an anatomical model, assembly, diagram, rig or generator. An editable rig or generator may be a part of an asset or independently reusable. |
| Method | How the asset was made, such as source tracing, scan-derived segmentation, manual illustration or procedural generation. |
| Format | How a specific export is delivered, such as GLB, BLEND, SVG or PNG. Show the recorded file identity and availability for each export. |
| Parts | Named structures or components and which exports contain them. Indicate what is selectable, separately available or visible only as context. |
| Capabilities | What visitors or authors can do with the revision or export, such as isolate a structure, play motion, edit labels, pose a rig or generate scan views. State the applicable inputs and limits. |
| Uses | Lessons, assemblies, Stage presets and saved reviews that use the revision. Link to the precise stop, view or finding where one exists. |

The [Testis pathway](../../diagrams/testis_pathway/README.md) is a reusable diagram. Its English and Chinese SVGs belong to the same revision. The r01 PNGs are additional formats of the r01 diagram. The [breathing assembly](../../body/breathing/README.md) contains lung and diaphragm parts. Its Blender shape keys are controls for animating those parts. The [ultrasound sweep builder](../../experiments/ultrasound-sweep/README.md#replay) illustrates a generator that samples reference anatomy using prescribed probe tracks. Individual probe poses, simulated frames and overlays belong with their sweep and keyframe. Acquired comparisons carry their separate source and rights.

**Current scope.** The implemented Library focuses on 3D lineages and exact model deliveries. Image-led lessons and simulation tours already have their own routes in the [route guide](routes-and-api.md#page-links). Indexing eligible diagrams, generators and rigs as reusable assets is a product requirement. Public listing and export availability depend on the asset's rights and release admission.

The asset maintainer explicitly selects which revision carries **Recommended** for a lineage. A review score is evidence the maintainer can use in that decision. The lineage opens on the recommended revision. If a newer candidate exists, show its version and status beside the selector. Until a recommendation exists, open the latest revision with its actual review status. A link to a specific revision always opens that revision.

- A representative preview bound to the selected revision, with source, version, attributes, rights, available exports and principal limitation. Distinguish the date the asset changed, the date its preview was rendered and the date someone last reviewed it.
- For an export in the maintained 3D teaching assessment scope, show its exact-task quality profile and a **Rating rubric** link beside it, including in the empty state. The dedicated product URL is `/rubric`; its content owner is the [canonical rubric](../guides/asset-quality.md). A saved assessment identifies the rubric revision used.
- Exact-version reviews, related lessons and the 3D preset behind the preview when available. Preserve revision selection when returning from these destinations.

## Making a release selection

Follow the [asset release policy](../WORKFLOW.md#asset-releases) for versioning and recoverable releases. The current 3D Library declares package membership and stable revision routes in its [package declarations](../../sites/anatomy-gallery/app/src/content/gallery/library-packages.json). A newly selected teaching export in an existing asset lineage can supply its named route through the accepted assessment. The [retained asset revision routes](../../sites/anatomy-gallery/app/src/content/gallery/library-editions.json) preserve current bookmarks for accepted assessments that predate named routes. A Library entry with one maintained revision uses that revision as its candidate recommendation. The [Library recommendations](../../sites/anatomy-gallery/app/src/content/gallery/library-recommendations.json) record editorial choices where several maintained revisions are available. The [maintained selections](maintained-selections.json) bind each export and task to its accepted assessment. They generate the [Teaching register](maintained-models.md).

When the package, recommendation or route changes, [refresh the candidate Library admission](../../sites/anatomy-gallery/README.md#candidate-library-admission). The compiler checks each maintained export against its native owner and the teaching register. AssetKit can then trace an export to each Library route where learners can find it.

Assembly binds each revision’s downloads, attribution, evidence and per-export assessments. A multi-file Library link uses the file digest to open its assessment, with the export path as a second identifier when two filenames share the same bytes.

## Review coverage

Use the [Teaching register](maintained-models.md) to describe the selected 3D teaching exports. Report **register IDs** and **export–task pairs** separately. The first count deduplicates IDs under the existing `families` key across collections. The second counts every selected export with its own learner task, exact file identity and four independent scores. In Gallery prose, a [family](../../GLOSSARY.md#gallery-and-surfaces) is a discovery grouping. The schema key identifies register entries.

A separate **asset inventory** requires a separately verified census of independent editable sources or pinned upstream inputs and their owners. If the inventory includes retired or reference-only assets, report **active assets** separately and count them by asset lineage. Before counting a shared source once, demonstrate that one source edit propagates to both lesson exports in a disposable rebuild. An editable assembly used as a whole is one selection for its task. If a Gallery default or published delivery differs from the selected starting file, identify both asset revisions.

Report fully rated, partially rated and unrated counts. Full coverage for one starting file requires all four axes for the declared task. A partial assessment identifies the missing axes. A missing assessment keeps the file visible in the denominator. The [teaching-asset rubric](../guides/asset-quality.md) owns the score meanings and evidence requirements.

The two Cardiac Atlas selections share a local Library entry. Its static and animated bookmarks still open the original histories. The shared female pelvic atlas spans Urinary and Reproductive. Each exact study links to its sibling, and both collections count toward task coverage. The atlas has one register ID in the combined total. Other specimens in either package retain their original identities.

## Browsing

Open on a compact list. Cards emphasize the preview. The tree groups the same entries by the survey’s anatomical categories. Show role, teaching purpose, review status, recorded score and indexed file count. Search names, tags and paths, including names of files in revision history. A unique match within an asset page selects its revision or package delivery. Search by exact path, SHA-256, revision name or short version such as `r13`. When several revisions of an asset share a filename, search the full path or open its revision history to pick one. Combine anatomical system, teaching purpose, entry type, review status and rating filters. Sort by name, file count or teaching total in either direction. Entries without a total follow complete scores in either score order. Rated includes partial assessments. The [current routes](routes-and-api.md#page-links) list the shareable filter parameters.

## Acceptance examples

The adrenal atlas pair has two glands in its export. A regional teaching view can show kidneys as context. The library identifies which structures the visitor will actually download.

A new revision with no assessment displays **Unrated** and offers the rubric. A partially scored revision labels each missing axis **Unrated**. Looking at r04’s review while browsing r05 keeps both version labels visible. A named teaching total carries its task and points to the corresponding review.

[Gallery product requirements](README.md) · [Existing Model Survey](../../sites/anatomy-gallery/README.md)

The [discovery audit and pilot](../../records/work-items/items/AG-GAL-018-reconcile-library-revisions.md) account for public exports and replay inputs. The [teaching asset review](../../records/campaigns/teaching-asset-review.md) covers the current starting files. The [second cohort](../../records/work-items/items/AG-GAL-025-assess-next-teaching-cohort.md) adds the skin envelope, right rotator cuff and illustrative thyroid.

For local teaching, promote the exact file that supports the maintained task. In a multi-export package, the isolated component and the contextual assembly each retain their own assessment. A file-specific link selects its own ratings and teaching view. A collection records whether its required learner actions worked in their reviewed settings. See the [teaching target](../guides/asset-quality.md#resolve-the-teaching-target).
