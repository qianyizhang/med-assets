# Asset Library PRD

**Outcome.** A visitor picking a reusable model can distinguish sources, select a revision and see what evidence supports using it. One entry represents one model lineage. Revisions share its history. A common anatomical name makes two lineages discoverable together.

The [maintained family list](maintained-models.md) identifies each editable lineage and its selected teaching files. The Library continues to serve exact consumer revisions.

## What the visitor sees

Index public 3D assets across model, atlas, assembly, lesson and review packages. A lineage can be found by name, anatomy or the use case that features it. Include prior revisions that still serve a lesson, consumer or review under the [beta retention policy](../WORKFLOW.md#retention). Trace a selected scene object to its exact asset revision when it is independently reusable. A mesh that exists only as part of a larger export links to that export with its part selected. List known public entries with unavailable exports or missing ratings and show their actual state.

The asset maintainer explicitly selects which revision carries **Recommended** for a lineage. A review score is evidence the maintainer can use in that decision. The lineage opens on the recommended revision. If a newer candidate exists, show its version and status beside the selector. Until a recommendation exists, open the latest revision with its actual review status. A link to a specific revision always opens that revision.

- An identifying portrait bound to the selected revision, its source, version, attributes, rights, available export and principal limitation. Distinguish the date the asset changed, the date its preview was rendered and the date someone last reviewed it.
- The revision’s quality profile and a **Rating rubric** link beside it, including in the empty state. The dedicated product URL is `/rubric`; its content owner is the [canonical rubric](../guides/asset-quality.md). A saved assessment identifies the rubric revision used.
- Exact-version reviews, related lessons and the 3D preset behind the portrait. Preserve revision selection when returning from these destinations.

## Making a release selection

Declare package membership and stable revision routes in the [Library package declarations](../../sites/anatomy-gallery/app/src/content/gallery/library-packages.json). A newly selected teaching export in an existing family can supply its named route through the accepted assessment. The [retained edition routes](../../sites/anatomy-gallery/app/src/content/gallery/library-editions.json) preserve current bookmarks for accepted assessments that predate named routes. A family with one maintained revision uses that revision as its candidate recommendation. The [Library recommendations](../../sites/anatomy-gallery/app/src/content/gallery/library-recommendations.json) record editorial choices across families with multiple maintained revisions. The [teaching register](maintained-models.md) owns the exact reviewed exports and learner tasks.

Assembly binds each revision’s downloads, attribution, evidence and per-export assessments. A multi-file Library link uses the file digest to open its assessment, with the export path as a second identifier when two filenames share the same bytes.

## Review coverage

Use the [maintained family register](maintained-models.md) to count progress on the selected teaching assets. Count a demonstrated shared model once. Include every selected lesson export in coverage, with its learner task, exact file identity and four independent scores. A source edit must propagate to both lesson exports in a disposable rebuild before grouping their family. An editable assembly used as a whole counts as one selection. If a Gallery default or published delivery differs from the maintained starting file, identify both revisions.

Report fully rated, partially rated and unrated counts. Full coverage for one starting file requires all four axes for the declared task. A partial assessment identifies the missing axes. A missing assessment keeps the file visible in the denominator. The [teaching-asset rubric](../guides/asset-quality.md) owns the score meanings and evidence requirements.

The two Cardiac Atlas selections share a local Library entry. Its static and animated bookmarks still open the original histories. The shared female pelvic atlas spans Urinary and Reproductive. Each exact study links to its sibling, and both collections count toward task coverage. The total counts the atlas once. Other specimens in either package retain their original identities.

## Browsing

Open on a compact list. Cards emphasize the preview. The tree groups the same entries by the survey’s anatomical categories. Show role, teaching purpose, review status, recorded score and indexed file count. Search names, tags and paths, including names of files in revision history. A unique match within a family selects its revision or package delivery. Search by exact path, SHA-256, revision name or short version such as `r13`. When multiple revisions in a family share a filename, search the full path or open the family’s revision history to pick one. Combine anatomical system, teaching purpose, entry type, review status and rating filters. Sort by name, file count or teaching total in either direction. Entries without a total follow complete scores in either score order. Rated includes partial assessments. The [current routes](routes-and-api.md#page-links) list the shareable filter parameters.

## Acceptance examples

The adrenal atlas pair has two glands in its export. A regional teaching view can show kidneys as context. The library identifies which structures the visitor will actually download.

A new revision with no assessment displays **Unrated** and offers the rubric. A partially scored revision labels each missing axis **Unrated**. Looking at r04’s review while browsing r05 keeps both version labels visible. A named teaching total carries its task and points to the corresponding review.

[Gallery product requirements](README.md) · [Existing Model Survey](../../sites/anatomy-gallery/README.md)

The [discovery audit and pilot](../../records/work-items/items/AG-GAL-018-reconcile-library-revisions.md) account for public exports and replay inputs. The [maintained-family review](../../records/campaigns/teaching-asset-review.md) covers the current starting files. The [second cohort](../../records/work-items/items/AG-GAL-025-assess-next-teaching-cohort.md) adds the skin envelope, right rotator cuff and illustrative thyroid.

For local teaching, promote the exact file that supports the maintained task. In a multi-export package, the isolated component and the contextual assembly each retain their own assessment. A file-specific link selects its own ratings and teaching view. A collection records whether its required learner actions worked in their reviewed settings. See the [teaching target](../guides/asset-quality.md#resolve-the-teaching-target).
