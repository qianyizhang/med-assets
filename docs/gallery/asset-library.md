# Asset Library PRD

**Outcome.** A visitor picking a reusable model can distinguish sources, select a revision and see what evidence supports using it. One entry represents one model lineage. Revisions share its history. A common anatomical name makes two lineages discoverable together.

The [maintained family list](maintained-models.md) selects one starting file per family for authoring and storage planning. The Library continues to serve exact consumer revisions.

## What the visitor sees

Index public 3D assets across model, atlas, assembly, lesson and review packages. A lineage can be found by name, anatomy or the use case that features it. Expose historical revisions within its history. Trace a selected scene object to its exact asset revision when it is independently reusable. A mesh that exists only as part of a larger export links to that export with its part selected. List known public entries with unavailable exports or missing ratings and show their actual state.

The asset maintainer explicitly selects which revision carries **Recommended** for a lineage. A review score is evidence the maintainer can use in that decision. The lineage opens on the recommended revision. If a newer candidate exists, show its version and status beside the selector. Until a recommendation exists, open the latest revision with its actual review status. A link to a specific revision always opens that revision.

- An identifying portrait bound to the selected revision, its source, version, attributes, rights, available export and principal limitation. Distinguish the date the asset changed, the date its preview was rendered and the date someone last reviewed it.
- The revision’s quality profile and a **Rating rubric** link beside it, including in the empty state. The dedicated product URL is `/rubric`; its content owner is the [canonical rubric](../guides/asset-quality.md). A saved assessment identifies the rubric revision used.
- Exact-version reviews, related lessons and the 3D preset behind the portrait. Preserve revision selection when returning from these destinations.

## Browsing

Open on a compact list. Cards emphasize the preview. The tree groups the same entries by the survey’s anatomical categories. Show role, teaching purpose, review status, recorded score and indexed file count. Search names, tags and paths, including names of files in revision history. A unique match within a family selects its revision or package delivery. Search by exact path, SHA-256, revision name or short version such as `r13`. When multiple revisions in a family share a filename, search the full path or open the family’s revision history to pick one. Combine anatomical system, teaching purpose, entry type, review status and rating filters. Sort by name, file count or teaching total in either direction. Entries without a total follow complete scores in either score order. Rated includes partial assessments. The [current routes](routes-and-api.md#page-links) list the shareable filter parameters.

## Acceptance examples

The adrenal atlas pair has two glands in its export. A regional teaching view can show kidneys as context. The library identifies which structures the visitor will actually download.

A new revision with no assessment displays **Unrated** and offers the rubric. A partially scored revision labels each missing axis **Unrated**. Looking at r04’s review while browsing r05 keeps both version labels visible. A named teaching total carries its task and points to the corresponding review.

[Gallery product requirements](README.md) · [Existing Model Survey](../../sites/anatomy-gallery/README.md)

The [discovery audit and pilot](../../records/work-items/items/AG-GAL-018-reconcile-library-revisions.md) account for public exports and replay inputs. The [second cohort](../../records/work-items/items/AG-GAL-025-assess-next-teaching-cohort.md) adds the skin envelope, right rotator cuff and illustrative thyroid.
