---
description: Portable verification for the maintained-state campaign.
scope: med-assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: MS-001
work_status: done
work_kind: build
added: 2026-11-23
depends_on: none
tags: repository, evidence
---

# MS-001 — Portable verification

Root verifier, current coverage generator, Gallery test discovery, display identity validation and CI prerequisites.

## Acceptance and verification

Run the ordinary gate and tracked scorecard in a depth-one LFS-pointer clone and in the prepared checkout. Both resolve all 81 selections, including the UFF and parathyroid witnesses. An incorrect source or derivative binding fails. Historical comparison requires an explicit baseline. Run the portable Gallery Node tests and retain separate preview and payload gates.

A Sol-high builder owns implementation and scoped regression evidence. The campaign lead reviews the patch, repeats the significant failure path and decides acceptance. [Campaign and baseline](../../campaigns/maintained-state/README.md)

## Accepted locally

At `7392cf5`, a new depth-one checkout started with 1,147 unresolved pointers and no display cache. Node 24 ran 15 portable tests and Python ran 462 tests. The tracked 81-file scorecard and generated register both matched. The same gate passed with hydrated bytes. Mutating the UFF source identity or parathyroid derivative digest and dropping the UFF binding each failed verification. The full-history audit resolved the explicit 79-file baseline.
