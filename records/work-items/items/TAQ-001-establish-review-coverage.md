---
description: Establish exact-file review coverage.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: TAQ-001
work_status: done
work_kind: build
added: 2026-11-22
tags: gallery, evidence
depends_on: AG-GAL-018
---

# TAQ-001 — Establish exact-file review coverage

[Teaching asset review campaign](../../campaigns/teaching-asset-review.md)

Derive a coverage inventory from the maintained register and existing assessment owners. Bind available assessments by exact export identity and named task. Record the collection, family, starting path, identity, assessment source, coverage state and reason for a gap. Include the native assemblies. Record relevant alternate or hosted revisions separately.

- [x] Produce full, partial and unrated counts for each collection and overall. The three counts reconcile to the number of maintained starting files at the reviewed revision.
- [x] Check existing score sources, including Gallery entries, package assessments and older pilots. Preserve attribution and identify disagreements, missing identity or incomplete evidence explicitly.
- [x] Exercise the normal reporting entry point on a known rated asset, an unrated sibling and an assembly. Show that a wrong export or ambiguous match cannot silently acquire a rating. Verify register drift is visible.
- [x] Record the tested revision, command and results. Link the report from this item.

## Result

The baseline covered 79 starting files in 12 collections at
`a6f4b3cbea6b4859fdce769fed17f605fe109266`.
Four are fully rated, four are partially rated and 71 are unrated. Both native
assemblies and nine of the ten Respiratory starting files are unrated. Retained
ratings for alternate files, including bronchial r13, do not count toward the
selected file. The r03 adrenal overview and close-up reassessment report different
surface scores and retain their distinct view scopes.

Run the generator from the repository root for the current report. Confirm the
tracked scorecard with `--check`. To regenerate a detailed audit of the baseline,
pass `--repo PATH` with a checkout of `a6f4b3c`.

```sh
python3.12 records/campaigns/teaching-asset-review/coverage.py --check records/campaigns/teaching-asset-review/current-coverage.md
python3.12 -m unittest discover -s tests -p test_teaching_review_coverage.py -v
```

The report reproduced byte for byte from 145 inputs extracted from the pinned
Git revision, with Git LFS pointer identities where applicable. The reporting
entry point verified terminal airspaces r02, the unscored first-fork r14 and
the Breathing assembly. It rejected a sibling digest and a tied pair of
campaign tasks, and returned a drift failure after a register family rename.
The offline gate passed 447 tests, 26 transport manifests, 25 foundation records,
394 import references and 882 LFS pointer identities on the working tree.
The report preserves declared scores and evidence identities. Its scope
does not include a fresh anatomy, rendering or hosted delivery review.
