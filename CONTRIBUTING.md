# Contributing

## Issues and status

Scan for problems and track actionable work in issues. Describe the problem,
impact, supporting evidence (including authorized screenshots or illustrations when
useful), acceptance criteria, and what is out of scope. Use existing semantic labels
where helpful. A tiny self-contained fix may explain its problem in the PR instead
of opening an issue; say why a separate issue is unnecessary.

Keep issue status current, including work already implemented locally but not
pushed. Distinguish work not started, local work not pushed, validation pending,
and delivery blocked; identify a recoverable branch, commit, or artifact and the
next action where applicable. Work items can continue, pause, or be cancelled
independently; record dependencies rather than silently changing related work.
Closing as not planned differs from completing acceptance and does not itself
authorize deleting history or artifacts; follow applicable retention rules.

## Pull requests and delivery

Once there is concrete progress, open a draft/WIP PR. Link the related issues;
issues and PRs may have many-to-many relationships. Use the
[shared GitHub guide](https://github.com/qianyizhang/repo-kit/blob/main/user/practices/github.md)
for public issue, PR and follow-up briefs; keep detailed worker evidence in
linked records. Reference issues without auto-closing them when a PR delivers
only part of their acceptance criteria.

Mark a PR ready when its scoped acceptance criteria and applicable checks have
supporting evidence, the exact tested commit is identified, and limitations are
explicit. Merge only with applicable authorization. Close an issue as completed
only after its acceptance criteria are met; track residual work separately.
Repository issues, PRs, and documentation are the source of truth; keep chat
summaries concise.

Keep issue/PR scope balanced: split oversized issues into independently closable
outcomes with explicit dependencies, not one ticket per mechanical commit. After
each merge, add a concise comment to every relevant issue: delivered change/PR,
checks, remaining work and current status; partial delivery leaves the issue open.
When a surface's actionable backlog is cleared, audit that surface and propose the
next evidence-backed batch of meaningful improvements. Do not create filler;
blocked or paused issues remain visible and are not counted as completed.

## Iteration and checks

Iterate toward a useful result: build v1, inspect actual defects, fix v2, run
affected regression checks, then repeat until the agreed acceptance is met.
Reuse valid evidence tied to the exact artifact and test conditions unless a change
invalidates it. Repeat reproduction or an audit only for a concrete risk or question,
not as a substitute for improvement. Each cycle should deliver a concrete improvement
or resolve a blocker; if meaningful effort stalls, report the blocker and next choice.
Stop when acceptance is met; do not invent extra gates or reopen settled checks.
Keep concise reusable lessons in the existing owning guide or review record, not
duplicate reports. Required scoped local checks and separate quality gates still apply.

Follow the applicable [review contract](docs/REVIEW_CONTRACT.md) and
[verification guidance](docs/VERIFICATION.md). Technical integrity, visual review,
anatomical/clinical approval, browser runtime, and publication are separate gates;
a screenshot alone does not establish runtime approval.

## Generated artifacts and retention

Keep canonical inputs, source identities, licenses, attribution, replay recipes,
unique measurements and review decisions. Preserve masters, failed drafts and
approved derivatives as distinct evidence. Generated files can still be required
deliverables or historical records; regeneration alone does not make them disposable.

A file around 1,000 lines warrants a usefulness and duplication review, not a size
limit. Retain large files when they carry unique evidence, replay inputs or a
consumer contract. Trace readers, dynamic discovery, packaging and checks before
removal. Prefer one authoritative record with a pinned reference over copied
inventories or receipts; materialize consumer-specific copies during preparation.
Remove a copy only after proving its replacement or repeatable regeneration,
updating producers and consumers together, and comparing meaningful outputs and
asset hashes. Keep immutable historical manifests intact. Record the evidence and
checkout savings in the issue/PR; do not minify, split files arbitrarily or add a
permanent audit report merely to lower line counts.

## Visual evidence in issues and PRs

- Keep asset issue updates visual-first. Use short bullets for problem, change,
  remaining gap and next step; link verbose checks instead of repeating logs.
- Asset and visible-feature PR descriptions must embed representative matched
  baseline/current screenshots, or clear views of a new asset, with brief labels
  for the intended change. See the [comparison contract](docs/REVIEW_CONTRACT.md#comparing-asset-variants)
  for export/reimport and artifact-binding requirements.
- For both issue updates and PRs, match camera, scale and lighting; show whole
  context and zoom subtle details. Reuse existing authorized evidence; do not
  recapture or rerender valid evidence just to satisfy this rule. Image publication
  still needs authorization.
- For docs/test-only or other nonvisual changes, state screenshots are not
  applicable; do not create decorative images.
- Highlight only key facts/numbers with textual cues: 🟢 Passed/Positive,
  🔴 Failed/Blocked, 🟡 Pending/Uncertain; never rely on color alone.
