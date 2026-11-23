---
description: Bounded upload plans for the maintained-state campaign.
scope: med-assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: MS-002
work_status: ready
work_kind: build
added: 2026-11-23
depends_on: none
tags: repository, evidence
---

# MS-002 — Bounded upload plans

Transport planner, uploader, path lookup and catalog consumers. Keep the historical migration receipt and immutable destination names.

## Acceptance and verification

Run real planner output through uploader preflight, fake transfer and fresh readback. Add, rename, replace and locally remove a source while retaining approved old addresses. Select before inspecting bytes. Reject stale revision, changed bytes, unsafe paths, undeclared destinations and inconsistent totals. Interrupt and resume with an identical plan.

A Sol-high builder owns implementation and scoped regression evidence. The campaign lead reviews the patch, repeats the significant failure path and decides acceptance. [Campaign and baseline](../../campaigns/maintained-state/README.md)
