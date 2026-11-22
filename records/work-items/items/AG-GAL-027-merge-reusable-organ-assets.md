---
description: Merge compatible assets into a maintained organ model and deliver two lesson-specific selections from it.
scope: Anatomy Gallery organ assets
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-027
work_status: ready
work_kind: build
added: 2026-11-22
tags: gallery, assets, repository
depends_on: AG-GAL-026
---

# AG-GAL-027 — Merge reusable organ assets

**Owner** · Gallery campaign lead, following [lesson consolidation](AG-GAL-026-consolidate-overlapping-lessons.md). Maintain each shared structure once. One organ model may include exterior and interior surfaces, selectable parts and a motion rig. Each lesson uses the subset it needs and can load its own smaller export.

## Pilot and rollout

1. Review the [maintained families](../../../docs/gallery/maintained-models.md) against the consolidated lesson tasks. Start candidate selection with the cardiac models. Identify two existing lessons that share a structure and require different selections. Confirm their source, anatomical frame, units, laterality, license and any required motion or attachments. If cardiac sources cannot support the claimed fit, choose another evidenced pair. Keep unregistered specimens or source alternatives distinct and labeled within the organ package.
2. Give the shared geometry one editable source or reproducible assembly recipe. Declare each lesson's parts, view and optional motion using existing package conventions. Rebuild both exports from that source. Demonstrate in a disposable replay that a change to a shared structure reaches both exports and that each keeps its intended selection.
3. Inspect each lesson before and after at the same camera, scale and, where applicable, motion phase. Exercise both in the ordinary Gallery. Verify protected landmarks, selection and motion controls, exact downloads, and behavior when an export is missing or wrong. Record each export's size and assess its exact bytes for its own learner task. Verify the full model by clean reimport. [Asset and assembly requirements](../../../docs/WORKFLOW.md#asset-admission)
4. Apply the proven approach to other compatible overlaps found in the review. For each remaining candidate, record the concrete reason to preserve it separately, such as a different specimen or a task-specific rig. Success requires two working lessons from one organ model in the pilot.

## Beta cleanup

Move current lessons, recipes, tests, credits and docs to the selected owner. Delete redundant internal files and stale aliases after checking their readers. Git history is sufficient for ordinary retired beta material. Retain required rebuild inputs, immutable import identities, attribution and evidence supporting current claims. Preserve published links with known users. Update the register, exact-export scorecard and [Library guide](../../../docs/gallery/asset-library.md), then run the [applicable gates](../../../docs/WORKFLOW.md#verification). Report the change in maintained copies and download sizes alongside the learner checks.
