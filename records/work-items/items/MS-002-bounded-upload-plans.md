---
description: Bounded upload plans for the maintained-state campaign.
scope: med-assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: MS-002
work_status: done
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

## Accepted locally

Accepted in `fcbee7a` and retested with the integrated tree. Eight end-to-end Node tests exercised the actual planner, uploader and in-memory Worker bucket, including a corrupt read, bounded interruption and resume, renaming, replacement, old addresses, unsafe paths and a stale checkout. A real kidney export of 2,527,704 bytes passed offline preflight against its existing address. All 1,245 catalog routes and the historical 694-object receipt were retained. Remote availability requires an authorized transfer and readback.
