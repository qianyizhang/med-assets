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
