---
description: Merge compatible assets into a maintained organ model and deliver two lesson-specific selections from it.
scope: Anatomy Gallery organ assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-027
work_status: done
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


## Accepted local selections

The [overlap audit](../../campaigns/organ-and-lesson-overlaps.md) records each learner action, anatomical fit and retention decision. The initial register had 79 families and 79 files. It now has 77 distinct families and 80 selected teaching files. Two demonstrated mergers reduce the family count. Adding the tracheal cutaway brings its independently assessed lesson into coverage. Of the 80 files, 74 meet target on all four axes and six retain previously documented form exemptions. [Exact scorecard](../../campaigns/teaching-asset-review/current-coverage.md)

| Model | Lead review and result |
| --- | --- |
| [Cardiac Atlas](../../../reviews/teaching-assessments/2026-11-23-cardiac-shared-source/README.md) | The full static and two-part motion lessons rebuild from one editable atlas. A disposable 1 mm aorta edit reached both. Matched overview, anterior and posterior views preserve vessel orientation. The LV changes against the fixed aorta at the sampled phases. The complete model reimported with 247 meshes and 228 channels. Static falls from 4.25 to 3.50 MB and motion from 1.16 to 0.85 MB. Keep the schematic joins explicit. |
| [V7 trachea](../../../reviews/teaching-assessments/2026-11-23-trachea-cutaway/README.md) | A shared wall-thickness edit reached the open and cut shells. Airway Review uses the three openings and One Breath uses the exposed path into the left bronchus. The maintained open edition and exact V7 cutaway each carry a rating. Removing 19 hidden duplicate meshes from the companion reduces the five One Breath downloads from 9.79 to 8.21 MB. Five matched views and the exchange diagram preserve the original result. A smaller cutaway encoding remains a reproducible trial. |
| [HRA female pelvis](../../../assemblies/hra-female-pelvis/README.md) | The same 21-part geometry builds the eight-part bladder-base and seven-part cervicovaginal selections with distinct materials. A disposable 0.10 mm dome edit reached both. The ordinary build reproduced both assessed downloads exactly. An incompatible layout was rejected. The cross-collection links identify the change of atlas. |

The lead inspected the matched views and ordinary Gallery selections. The [remaining component work](AG-GAL-028-reuse-z-atlas-components.md) covers the right-arm bones and parotid envelopes. Their present lessons need different surrounding structures; the item names the common surfaces, the topology differences to resolve and owners for the narrower trials.

## Cleanup and contract corrections

- **Lesson ownership.** The ovary package README, Body Systems README and reviewed stops, Use Cases checks, Gallery use-case guide and routes guide now identify the shared lesson, the source and scale transition, and each entry’s return. The original AG-GAL-016 ledger describes the first version. The Gallery README names the focused replay.
- **Shared model ownership.** The maintained register, Library guide, rubric, generated coverage report and backlog previously assumed one starting file per family. They now distinguish editable ownership and exact lesson coverage. The cardiac package index and the bladder and vaginal export READMEs identify the editable source or assembly. Original editions remain reachable through revision history.
- **Airway delivery.** The One Breath and airway-route READMEs, trachea r06 package and recipe guides now describe the compact companion, its separate shell, and locally verified Stage behavior. The Balanced link in the specialist dental lesson now opens its named revision. The original published static and historical reviews retain their separate scopes.
- **Code and storage.** The respiratory companion and existing geometry-selection replay share one selector. The pelvic recipe takes over the prior standalone extraction; its old command still rebuilds the same file. Current evidence, exact public routes, style inputs, credits and import identities remain available. Review staging, disposable edit copies and duplicate QA exports were pruned. The new cardiac teaching GLBs total 4.35 MB of tracked payload.

## Verification

Tested implementation `7d95ddd7f5d9e9d288beefa8f3c5b430e61a7d36`. A fresh protected framework assembly reproduced the local Gallery HTML with SHA-256 `a83b4930be3222b7abbd66f798b1f4c827f3c23cb06b3901f36c95e78610ed7d`.

- Chrome verified both ovary entrances and returns, alternate and source views, all 11 Body Systems stops, 18 other use-case checks, and all 45 current or historical target comparisons. The Library checked 97 entries, 146 exact or parent routes, 124 campaign reviews and 101 download responses. Each cardiac and pelvic lesson has its own visible assessment.
- Stage checks covered the two cardiac selections, vessel isolation, the wall-motion scrubber, preset reload, exact downloads, missing and same-size corrupted bytes, and retry. A public-origin browser rehearsal against the local server verified both tracheal presets and their exact Library links. It exposed a poster failure when a local review was unavailable; the corrected public path uses the indexed reference image.
- The repository offline gate passed 454 tests. Payload integrity verified 1,115 hydrated LFS files, 25 foundation records and 13 package checks. All 15 packaged Gallery tests, four preview-server tests, seven pinned dental checks, and 37 standalone One Breath tests passed. The scorecard regeneration and changed Markdown links were checked.
- Local review scratch fell by approximately 320 MB across the three work areas, including the disposable full cardiac atlas and superseded Gallery builds. Current QA images, reconstruction inputs and the verified local walkthrough were retained. These checks cover local delivery and a simulated public origin. Hosted publication and specialist anatomical review remain separate.
