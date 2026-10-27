# Contributing

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

Once there is concrete progress, open a draft/WIP PR. Link the related issues;
issues and PRs may have many-to-many relationships. Describe scoped commits,
tests and results, and remaining work. Reference issues without auto-closing them
when a PR delivers only part of their acceptance criteria.

Mark a PR ready when its scoped acceptance criteria and applicable checks have
supporting evidence, the exact tested commit is identified, and limitations are
explicit. Merge only with applicable authorization. Close an issue as completed
only after its acceptance criteria are met; track residual work separately.
Repository issues, PRs, and documentation are the source of truth; keep chat
summaries concise.

Follow the applicable [review contract](docs/REVIEW_CONTRACT.md) and
[verification guidance](docs/VERIFICATION.md). Technical integrity, visual review,
anatomical/clinical approval, browser runtime, and publication are separate gates;
a screenshot alone does not establish runtime approval.
