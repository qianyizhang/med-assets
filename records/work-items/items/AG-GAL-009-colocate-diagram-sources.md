---
description: Move four authored diagram inputs to their owning illustration packages.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-GAL-009
work_status: done
work_kind: build
added: 2026-11-20
tags: repository, evidence
depends_on: none
residual_of: none
residual_items: none
---

# AG-GAL-009 — Co-locate reusable diagram sources and recipes

## Intent

Give the biliary pathway, oral spaces, testis pathway and urinary outflow diagrams one place to find their editable sources, builders and exports.

## Acceptance Criteria

- [x] Move the four single-use packages from `sources/authored/` into `diagrams/`. Preserve editable source bytes, attribution and revision boundaries.
- [x] Update recipes, input hash references, tests and package instructions. Replay the affected diagrams and compare the resulting SVG and image identities against each package's acceptance rules.
- [x] Keep existing public export paths and published evidence intact. Retire the old source directory once its known readers have moved.

## Context and Trade-offs

The [ownership map](../../../docs/WORKFLOW.md#target-layout) puts reusable illustrations in `diagrams/` and single-lesson plates with their lesson. This is a repository package move. Any new lesson adoption can choose its own stopped view and evidence.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Accepted package ownership and a bounded Wave 2 move |
| 2026-11-20 | Codex | deferred | done | Moved the recipes and passed exact replay and identity checks. |

## Implementation Ledger

The editable SVGs and builders now live in the revisioned `diagrams/*/recipes/` directories. The oral input pins, testis r02 frozen-input paths, review file references and export instructions point to the new owners. All tracked display exports keep their original paths and bytes.

On the Mac, Inkscape 1.4 (`e7c3feb1`, 2024-10-09), verified against the official disk image SHA-256, reproduced all eight r01 decoded PNGs through the owning recipes. The three original generators reproduced all six editable SVGs they own, and both oral spaces editable inputs matched their recorded hashes. The r02 build reproduced both editable and both outlined SVGs byte for byte, and all four reviewed decoded pixel hashes at native size and 800 px. The temporary Fontconfig setup used Noto Sans CJK SC Regular (`2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b`) and Noto Sans Regular (`b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5`). No font files were added to the repository.
