# Contributing

## Asset admission: reuse, improve, then expand

**This is a blocking review gate for all future asset expansion**, including
imports, authored assets, maintained variants and duplicated packages. The goal
is better quality and useful coverage, not a larger collection to maintain.
Demonstrably better replacements and variants for different purposes are welcome.

Start from existing assets. Prefer adapting or absorbing the useful parts of a
source into the owning asset, or using reversible parameters, materials, overlays
and assemblies, rather than importing everything or maintaining a parallel copy.
Compare against the intended quality and use, not merely whether an existing
asset can technically render. Do not force a destructive edit or a lower-quality
result to avoid an addition.

Add a separately maintained asset or variant only when evidence shows either:

1. Existing assets cannot meet the stated purpose and quality requirements,
   including a demonstrated quality improvement that warrants replacement; or
2. Adapting an existing asset would break another named, purposeful use, and the
   uses cannot safely coexist through non-destructive controls or composition.

Before committing to expansion, record the decision in the existing issue or
owning asset/review record; the PR must link it. Keep it concise and include:

- **Need and benefit:** intended use, required quality and the concrete improvement
  or distinct purpose. Novelty, availability or collection size alone is not a need.
- **Reuse comparison:** existing asset IDs/paths and revisions, options considered
  (reuse, adaptation, selective integration and non-destructive composition), and
  concrete evidence for the chosen exception. Use inspected matched output or
  relevant measurements; an unsupported claim that reuse is unsuitable is insufficient.
- **Cost and ownership:** added source/export/storage, dependency, review and upkeep
  burden; the maintenance owner; why the benefit warrants that burden. For a
  replacement, identify the active role it supersedes and the consumer migration.
- **Preservation and checks:** other uses/consumers that must keep working, retained
  masters and provenance, and affected regression/quality checks. Preserve decisions
  and provenance without keeping every superseded version as an active asset.

**Do not mark ready or merge an expansion with a missing or unsupported decision.**
If reuse or selective adaptation delivers the intended purpose and quality
improvement without breaking other uses, prefer it over a separately maintained
addition. A demonstrably better replacement remains welcome when its benefit
justifies migration and upkeep. This gate does not authorize
deletion, destructive replacement, publication or merge, and does not reopen
settled work. Existing retention, source/licensing, technical, visual,
anatomical/clinical and runtime gates remain separate and required as applicable;
neither this decision nor passing CI establishes user or clinical acceptance.

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

Before marking ready, include the [retention review](#generated-artifacts-and-retention)
for large files or repeated generated artifacts added or changed by the PR:
purpose, canonical source, consumers and why each retained copy is needed.

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
current delivered assets, unique measurements, review decisions and required
recovery material. Retain exact artifact/evidence bindings for current claims.
Original import manifests and checksums remain provenance; do not rewrite them
to hide later changes.

Use ignored `.artifacts/<outcome>/` for intermediate renders, logs, audit dumps,
source-hash lists and routine check output. Do not commit per-step receipts or
another copy of a package inventory. Record routine check results in the existing
issue/PR or owning README. Keep executable integrity hashes where a consumer
actually uses them.

Keep a durable bundle only for a delivered result or an active finding that needs
its supporting evidence. Use one bundle and its README for the outcome, source
revision, check summary, limits and retention reason. Do not duplicate source,
media or metadata across bundles when a reference serves the consumer.

At closeout, move accepted decisions and unresolved defects to their owners, then
remove spent intermediates and superseded output. A concise failure note must
retain the rejected approach, reason and any remaining risk; it does not require
keeping every failed draft or render. Git history preserves committed old output.
Trace readers, dynamic discovery, packaging, tests and symlinks before removal;
repair consumers and retire claims whose supporting evidence is removed.

Review remaining temporary bundles after 30 days. Keep one only with a named
active need and next review date. Source/licensing obligations and unique recovery
material need an explicit retention reason. No deletion ledger or automatic
janitor is required. File size alone is not a reason to keep or delete a file.

## Visual evidence in issues and PRs

- Keep asset issue updates visual-first. Use short bullets for problem, change,
  remaining gap and next step; link verbose checks instead of repeating logs.
- Asset and visible-feature PR descriptions must embed representative matched
  baseline/current screenshots, or clear views of a new asset, with brief labels
  for the intended change. See the [comparison contract](docs/REVIEW_CONTRACT.md#comparing-asset-variants)
  for export/reimport and artifact-binding requirements.
- For both issue updates and PRs, match camera, scale and lighting; show whole
  context and link close-ups to an exact overview locator. Use legible anchored
  labels, consistent Original / Updated pairs and a short what-changed/why caption
  as specified in the comparison contract. Reuse existing authorized evidence; do not
  recapture or rerender valid evidence just to satisfy this rule. Image publication
  still needs authorization.
- For docs/test-only or other nonvisual changes, state screenshots are not
  applicable; do not create decorative images.
- Highlight only key facts/numbers with textual cues: 🟢 Passed/Positive,
  🔴 Failed/Blocked, 🟡 Pending/Uncertain; never rely on color alone.
