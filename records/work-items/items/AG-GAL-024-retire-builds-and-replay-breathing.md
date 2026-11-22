---
description: Retire superseded local Gallery builds and verify portable Breathing replay.
scope: backlog item
status: stable
last_update: 2026-11-21
document_class: work_record
work_id: AG-GAL-024
work_status: done
work_kind: build
added: 2026-11-21
tags: gallery, repository, evidence
depends_on: AG-GAL-018, AG-GAL-020, AG-GAL-022
residual_of: AG-GAL-018
residual_items: none
---

# AG-GAL-024 — Retire review builds and replay Breathing

Nine generated Gallery applications were retired locally. One walkthrough covers
the retired review rounds. The [Breathing recipe](../../../body/breathing/README.md#replay-and-verify)
now replays the existing animation from exact Workshop meshes into fresh outputs.

## Local retirement

| Review round | Retired app directories | Retained evidence |
| --- | --- | --- |
| AG-GAL-018 Library | `discovery-app`, `pilot-app`, `node24-app`, `final-app` | Census, path and download receipts, pilot and final captures, and five distinct draft Gallery source files saved from the app directories. |
| AG-GAL-020 heart | `gallery`, `integrated-gallery` | Repack GLB and validation, Chrome captures, integrated Library and Gallery receipts. The two dependency links targeted the existing installation. |
| AG-GAL-022 form | `gallery-build`, `integrated-gallery`, `final-gallery` | Renders, exact browser captures, Library regressions, scripts, patches and logs. Two app copies had identical HTML. |

The nine retired directories accounted for 879,353,856 allocated file-block bytes after excluding surviving hardlinks. Available volume space increased by 583,970,816 bytes (556.92 MiB) during deletion. The walkthrough and receipts occupy 24,690,688 allocated bytes, giving an estimated net gain of **533.37 MiB**. Concurrent activity and APFS block sharing affect this estimate.

The [retirement receipt and archive](../../../.artifacts/AG-GAL-024-local-retirement/README.md) identify readers, symlinks and exact removals. Seven distinct HTML files and five draft overlays were read back from the 9,121,435-byte archive and verified against their hashes. The shared install, active builds, comparison evidence and independent backups were retained. Review the local receipts on 2026-12-21. [LFS and remote storage decisions](AG-GAL-017-local-and-remote-storage-cleanup.md#remote-inventory-and-recommendation)

## Walkthrough and rebuilds

Serve the retained walkthrough from the repository root with Node 24.

```sh
node sites/anatomy-gallery/tools/preview_gallery.mjs .artifacts/AG-GAL-024-local-retirement/gallery 0
```

The walkthrough used the `a0be351` overlay and the pinned backup. After retirement Chrome verified 102 Library routes, 22 downloads, heart selection and shared-view reload. The preview also served the exact left lung clip. For a new walkthrough, follow the [current assembly recipe](../../../sites/anatomy-gallery/README.md#restore-and-build-locally) in a fresh output directory. Share an existing dependency installation only after its lockfile matches.

## Breathing replay

The [Breathing package](../../../body/breathing/README.md#replay-and-verify) owns inputs, commands, attribution and the historical Site test limits. Ten clips replayed byte for byte. Only 41 float32 diaphragm morph values differed, by at most 1.86 nm. Clean Blender reimport matched the 67 object-bound tracks and all five sampled poses. The replay grouped tracks into 11 action datablocks versus 67 in the delivered assembly.

Default and explicit source paths passed, including missing and corrupt inputs, existing outputs, dangling symlinks and partial-build cleanup. The [local receipts](../../../.artifacts/AG-GAL-024-local-retirement/README.md) give the per-organ motion and phase results. `25b063b` contains the portable recipe, `d5c8257` records the four import overrides and passed payload integrity, and the final offline gate at `bd3f4a9` passed 443 tests.
