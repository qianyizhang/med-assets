---
description: Reproducible Gallery bootstrap for the maintained-state campaign.
scope: med-assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: MS-005
work_status: deferred
work_kind: build
added: 2026-11-23
depends_on: MS-001
tags: repository, evidence
---

# MS-005 — Reproducible Gallery bootstrap

Supported Gallery preparation entry, seed verification, pinned framework and viewer inputs, historical encoders and display preparation order.

## Acceptance and verification

Build a fresh candidate with empty derivative cache from verified hydrated inputs. Reuse verified inputs on a second run, reject a changed seed and corrupt source, and preserve any previous successful output on failure. Exercise fresh and warm builds under the release interface and check digest-bound published inputs.

A Sol-high builder owns implementation and scoped regression evidence. The campaign lead reviews the patch, repeats the significant failure path and decides acceptance. [Campaign and baseline](../../campaigns/maintained-state/README.md)
