---
description: Put transport implementations beside their manifests and give the Site delivery index its final name.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-012
work_status: done
work_kind: build
added: 2026-11-20
tags: transport, repository
depends_on: AG-GAL-007
residual_of: none
residual_items: none
---

# AG-GAL-012 — Consolidate delivery and recovery tooling

## Intent

Give fetch, upload, backup and restore implementations a single home under `transport/tools/` and align the internal Site delivery index name with its role.

## Acceptance Criteria

- [x] Move the transport implementations and update repo-owned callers, including the offline verifier, workflow invocations and sparse-checkout paths. Keep a compatibility command at an old path wherever a real external consumer requires it.
- [x] Rename `r2-trial.json` to `delivery-index.json` and migrate its Site build, preview, fetch, restore, manifest preparation and test readers together. Preserve declared routes and exact file identities.
- [x] Verify Git-pinned retrieval, on-demand hydration, backup restore and applicable failure paths through supported interfaces. Preserve public file addresses, historical transport manifests and workflow guards.

## Context and Trade-offs

Use the delivery and restore evidence from [AG-GAL-007](AG-GAL-007-plan-r2-and-recovery.md) and the [transport contract](../../../transport/README.md). General commands such as the offline verifier remain under `tools/`. Track storage retirement separately if exact consumers or recovery remain unsettled.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Accepted transport implementation ownership for Wave 3 |
| 2026-11-21 | Maintainer | deferred | ready | Approved local migration after reviewing the teaching batch at `519645d`. |
| 2026-11-21 | Codex | ready | wip | Began the transport move after `b461f8f`. |
| 2026-11-21 | Codex | wip | done | Verified recovery, the ordinary Gallery build and preview, and the guarded workflow paths locally. |

## Implementation Ledger

### Local delivery migration

[Transport tools](../../../transport/tools/) own Git-pinned fetch, R2 planning and upload, guarded LFS and Balanced fallback, mirror checks and transfer preparation, preview object preparation, and seed and legacy Dental Review restore. The three affected workflows use the new paths in their checkout patterns and callers. [The offline verifier](../../../tools/verify.py) remains the repository entry point. Repository and local consumer checks found no active external command requiring a shim.

The [Gallery delivery index](../../../sites/anatomy-gallery/app/src/content/assets/delivery-index.json) matches the previous index at `b461f8f` byte for byte. All 1,243 declared routes retain their URL, MIME type, size and digest. All 26 historical transport manifests match the parent. The pinned framework Worker at `f65265ca3c7d94790a86537e6ef725241fc012ea` still imports `src/content/assets/r2-trial.json`. The ordinary assembler generates that file from the canonical index inside its output. The protected Worker and public `/assets/index.json` route keep their existing contracts.

### Verification and recovery

- In a fresh clone of the migration candidate with LFS smudge disabled and an empty payload store, downloaded the Git-pinned 2,527,704-byte left kidney GLB into a fresh cache. Its working file remained a pointer. In a separate fresh cache, fetched and hydrated the 1,564,740-byte trachea cutaway GLB. The SHA-256 values matched Git and hydration preserved mode `0640`. A 404 and equal-length corrupt response injected at the fetch CLI boundary preserved the pointer and left no cached payload. Both same-length and different-length local edits were preserved before fetching.
- The retained [teaching ZIP](../../../sites/body-systems-survey/README.md#restore-the-media) matched its size and SHA-256. A clean extraction matched the exact path list and all 327 member hashes. The archive checksum blocked a missing and a corrupt input before extraction. The documented non-overwrite restore kept an edited airway-route GLB and flagged that one member. The other 326 passed.
- The retained framework ZIP matched its lock and ZIP integrity check. Its Git bundle, tree and protected runtime passed the ordinary Gallery build. The moved seed command reproduced the exact seed from both the frozen source and the original embedded snapshot, and refused to overwrite an edited destination. Local preview preparation produced 306 verified objects without changing the declared index. The moved legacy dental command verified all ten retained local payloads.
- The pinned Worker returned the full index at the public route from the generated compatibility file and served a representative asset HEAD with an R2 double. Ordinary loopback preview served the production HTML, study API and exact GLB, PNG and MP4 responses, including range and conditional requests. The restored-film preview test passed. The build verified 241 protected files and passed 12 Site tests using existing dependencies with the same lockfile.
- Recreated the bounded LFS, Balanced Drive and FDI31 sparse checkouts from the workflow patterns. Their offline units passed, and the bounded manifest validated through the moved CLI. The six uploader tests used local doubles, including resume and refusal paths. Read-only mirror inventory, transfer capabilities and R2 planning ran locally.
- Repository verification passed 440 offline tests, 430 retained import paths and 26 historical transport manifests. Payload integrity checked all 998 hydrated LFS files and 11 package checks.

Production cutover, hosted workflow execution, remote uploads, remote mirror restore, storage retirement and specialist viewer acceptance remain outside this delivery.
