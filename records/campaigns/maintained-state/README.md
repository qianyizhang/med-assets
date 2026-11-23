# Make maintained assets verifiable from their current inputs

Starting at `e613024`, the same checked-in assessments give different scores in two clean environments, and the retained delivery catalog cannot describe one bounded upload. The [independent audit findings](audit.md) identify the reproductions and the owners. The maintainer approved local implementation on November 23.

## Approved work and order

| Item | Outcome | Start after |
| --- | --- | --- |
| [MS-001](../../work-items/items/MS-001-portable-verification.md) | Portable verification | Independent |
| [MS-002](../../work-items/items/MS-002-bounded-upload-plans.md) | Bounded upload plans | Independent |
| [MS-003](../../work-items/items/MS-003-maintained-selections.md) | Direct maintained selections | MS-001 |
| [MS-004](../../work-items/items/MS-004-gallery-release-builds.md) | Gallery release builds | MS-003 |
| [MS-005](../../work-items/items/MS-005-gallery-bootstrap.md) | Reproducible Gallery bootstrap | MS-001 |
| [MS-006](../../work-items/items/MS-006-owner-recipes.md) | Promote active recipes | Independent |
| [MS-007](../../work-items/items/MS-007-campaign-acceptance.md) | Owner acceptance | MS-001, MS-002, MS-003, MS-004, MS-005, MS-006 |

Start MS-001 and MS-002 together. Promote the two recipes as an independent slice. Set the shared selection contract before switching Gallery consumers. Review candidate and published output separately before integrating the bootstrap command. The last approved public baseline is Gallery v10 in [the release record](../../../sites/anatomy-gallery/snapshot-reference.json). Preserve the existing candidate and use non-loopback behavior at the starting revision as a third comparison. Any later promotion has its own release decision.

## Ownership and acceptance

The campaign lead owns the contract between items, assignment, diff review, integration, polish and acceptance. Sol-high builders own the six implementation items. Each handoff identifies changed paths, test commands, before/after results, failures and any evidence or consumer that prevents pruning. Express invariants in executable checks. Remove superseded readers and redundant artifacts when their consumers and recovery are accounted for. Report changes in tracked file count and size independently of temporary verification output.

Use local commits and the [repository gates](../../../docs/WORKFLOW.md#verification). Preserve unrelated edits and exact public addresses within the approved release. The campaign finishes at verified local builds and rehearsed delivery. Archive restore unification remains a transport follow-up for the existing 327-member ZIP. Drive coordinator consolidation remains with the mirror owner pending a consumer and disposition of existing journals.

## Local acceptance

The lead accepted all seven items on implementation `7392cf5`. Sol-high builders delivered verification, bounded transport, selections, bootstrap and both promoted recipes. The lead integrated the release compiler and preview, and a Sol-high builder delivered the two-origin browser comparison. The individual work items record the failure paths and results.

The candidate and v10 rehearsal built from the final committed source reproduced their browser-tested HTML and catalogs byte for byte. The candidate HTML SHA-256 is `88205fbe86dd94a9ea5c65d48dc1586ebb176c290acad5dbebb7ecfe65a086b7`. The public rehearsal HTML SHA-256 is `1fb9734011f6e20e803e890fb8f15fcac3d7e529fa3659d51e5450180b829a16`. Its data, routes and behavior reproduce v10 in a newly compiled rehearsal. Candidate-only downloads in those browser checks used the loopback preview. The [follow-up audit](audit.md#second-review-of-aa2d63c) identifies the generated Worker coverage gap. The deployed v10 HTML has its own [recorded identity](../../../sites/anatomy-gallery/snapshot-reference.json). Publication and remote transport require separate authorization.

At implementation acceptance, the tracked tree grew from 3,658 to 3,684 files and by about 440 kB of Git file contents, counting LFS pointers at pointer size. The two structured selection and assessment inputs account for about 324 kB. Hydrated LFS identities and bytes stayed constant. One previously retained rehearsal duplicated 327 files totaling 12.1 MB. After moving its sole dependency installation to the retained identical project and checking its consumers, all 241 protected runtime files and 15 packaged tests passed. The builder also retired over 6 GB of temporary verification trees created during this campaign. These are logical file sizes. [Remaining recipe inventory](recipe-dependencies.md)
