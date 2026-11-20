# Asset Library PRD

**Outcome.** A visitor picking a reusable model can distinguish sources, select a revision and see what evidence supports using it. One entry represents one model lineage. Revisions share its history. A common anatomical name makes two lineages discoverable together.

## What the visitor sees

Index public 3D assets across model, atlas, assembly, lesson and review packages. A lineage can be found by name, anatomy or the use case that features it. Expose historical revisions within its history. Trace a selected scene object to its exact asset revision when it is independently reusable. A mesh that exists only as part of a larger export links to that export with its part selected. List known public entries with unavailable exports or missing ratings and show their actual state.

The asset maintainer explicitly selects which revision carries **Recommended** for a lineage. A review score is evidence the maintainer can use in that decision. The lineage opens on the recommended revision. If a newer candidate exists, show its version and status beside the selector. Until a recommendation exists, open the latest revision with its actual review status. A link to a specific revision always opens that revision.

- An identifying portrait bound to the selected revision, its source, version, attributes, rights, available export and principal limitation. Distinguish the date the asset changed, the date its preview was rendered and the date someone last reviewed it.
- The revision’s quality profile and a **Rating rubric** link beside it, including in the empty state. The dedicated product URL is `/rubric`; its content owner is the [canonical rubric](../../guideline/asset-quality.md). A saved assessment identifies the rubric revision used.
- Exact-version reviews, related lessons and the 3D preset behind the portrait. Preserve revision selection when returning from these destinations.

## Acceptance examples

The adrenal atlas pair has two glands in its export. A regional teaching view can show kidneys as context. The library identifies which structures the visitor will actually download.

A new revision with no assessment displays **Unrated** and offers the rubric. A partially scored revision labels each missing axis **Unrated**. Looking at r04’s review while browsing r05 keeps both version labels visible. A named teaching total carries its task and points to the corresponding review.

[Gallery product requirements](README.md) · [Existing Model Survey](../../sites/model-survey/README.md)
