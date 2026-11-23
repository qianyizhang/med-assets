---
description: Reproducible Gallery bootstrap for the maintained-state campaign.
scope: med-assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: MS-005
work_status: done
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

## Accepted locally

At `7392cf5`, the owner hydrated the verified export inputs in a new depth-one checkout. Its 78 display WebPs were absent. Offline bootstrap regenerated all 78 and reproduced the browser-tested candidate HTML and compiled catalog byte for byte. A fresh published rehearsal also reproduced its tested HTML and catalog. The builder separately restored the frozen framework ZIP and seed, reused the populated caches, and rejected changed seed, source PNG, viewer bytes, archive, published snapshot, conflicting output and a simulated npm build failure. Previous successful output survived each failure.
