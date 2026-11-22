---
description: Put original acquisition evidence and current exceptions under sources/imports.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-011
work_status: done
work_kind: build
added: 2026-11-20
tags: repository, evidence, transport
depends_on: none
residual_of: none
residual_items: none
---

# AG-GAL-011 — Re-home original import records and overrides

## Intent

Make the import evidence discoverable together under `sources/imports/` and retire the top-level `metadata/` directory.

## Acceptance Criteria

- [x] Move `SHA256SUMS` and the records under `metadata/` into `sources/imports/`. Preserve immutable record bytes, historical layout entries, and current override provenance.
- [x] Update verifier and test paths, documentation and recovery readers together. Compare import coverage against the revision immediately before the move and preserve verification of the retained original paths.
- [x] Exercise the offline verifier with changed immutable bytes, a missing tracked imported file and an invalid current override. Confirm the corresponding failures remain distinguishable.

## Context and Trade-offs

The [import contract](../../../docs/WORKFLOW.md#import-and-source-integrity) and [verifier](../../../tools/verify.py) pin original record hashes. Original atlas package paths are outside this move. See [mirror planning](../../../docs/BACKUP_CHECK.md#scope-and-older-source-archives) for exact path coverage.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Accepted import provenance ownership for Wave 3 |
| 2026-11-21 | Maintainer | deferred | ready | Approved the two-commit local migration after reviewing the teaching batch at `519645d`. |
| 2026-11-21 | Codex | ready | wip | Began the import move from `519645d`. |
| 2026-11-21 | Codex | wip | done | Verified the import move and failure diagnostics locally. |

## Implementation Ledger

Against parent `519645d`, all six [record blobs](../../../sources/imports/) are byte-identical. The original snapshot has 591 paths. The retained set is identical at 430 paths with seven current overrides. The other 161 paths remain historical provenance. The atlas packages keep their paths and bytes.

The ordinary offline verifier reported the same 439 tests, 26 transport manifests, 25 foundation records and 998 LFS pointer identities before and after. Payload integrity passed for all 998 hydrated files (992,668,959 bytes) and 11 package checks. In a disposable checkout, added bytes to each pinned record separately, removed the tracked atlas `head.svg` from disk and broke its override's original SHA-256 binding. Each invocation exited 1 with the corresponding diagnostic: historical checksum changed, historical manifest changed, missing reference or invalid original hash binding. The verifier checks import integrity before running tests that read the same records.

The [imported atlas README](../../../body/2d-v4/whole-body-anatomy-v4-spatial/README.md) still contains its original relative link into `metadata/`. Its bytes are part of the verified import. The [sources guide](../../../sources/README.md#sources-and-scoped-uses) and [import contract](../../../docs/WORKFLOW.md#import-and-source-integrity) lead to the current records.
