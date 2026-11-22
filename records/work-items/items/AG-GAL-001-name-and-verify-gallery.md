---
description: Rename the Site source directory and visible product title with compatible build, preview and delivery.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-GAL-001
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, repository
depends_on: none
residual_of: none
residual_items: none
---

# AG-GAL-001 — Name and verify Anatomy Gallery

## Intent

Move `sites/model-survey/` to `sites/anatomy-gallery/` and use **Anatomy Gallery** as the visitor-facing title. Keep **Model Survey** for the dated catalogue, immutable seed and archive.

## Acceptance Criteria

- [x] Update active source references in build and restore tooling, asset fetch and preparation, test fixtures, preview commands and docs. Keep historical records readable.
- [x] Prepare the Site’s pinned Three.js modules from a clean checkout using documented Site-owned inputs. Exercise missing and corrupt inputs without relying on ignored lesson or report caches or legacy test fixtures.
- [x] Build and open the ordinary local preview from the new path. Exercise the four surfaces, `/rubric`, family and FDI31 bookmarks, and the archive. Verify a Git-pinned fetch and the missing or mismatched payload behavior through the supported entry points.
- [x] Verify the hosting configuration, publication ancestry, public hostname, delivery index contents and hash-addressed paths against the baseline. Record local checks and any remaining live acceptance separately.

## Context and Trade-offs

The [Site README](../../../sites/anatomy-gallery/README.md) documents the pinned framework, immutable seed and ignored publishing checkout. Preserve the generated and publication checkouts or migrate them recoverably. The [routes and API](../../../docs/gallery/routes-and-api.md) define the tested interface. The Site owns the viewer setup from the first build. The later Body Systems move owns its display index, media and historical replay.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | ready | Accepted product name and compatibility boundary |
| 2026-11-20 | Codex | ready | done | Local delivery at `be4aeda` and final Chrome recheck at `135e800` |

## Implementation Ledger

### 2026-11-20 · Verification · not-required

A clean index export of the `be4aeda` build inputs used the verified frozen ZIP and its framework bundle, the immutable Model Survey source seed, and a fresh fetch of all six files in the [viewer lock](../../../sites/anatomy-gallery/viewer.lock.json). Node 24.21.0 and npm 11.19.0 completed `npm ci` with an empty cache. The production build verified all 241 protected framework files and all 12 Site tests passed. With a missing and then a same-length corrupt viewer input, the ordinary framework command failed before creating either target. The restored seed's digest matched its recorded identity. The generated app showed **Anatomy Gallery** in the visible Site bar and browser title.

A clean Git checkout at `135e800` reused the exact verified inputs and npm cache. The production build and Site tests passed again. Its HTML SHA-256 matched the browser-tested build at `071d5c7fbcfbdab18ab444ca88001b0eddc7848f3c6cf7e9ea4f1cac4e515795`.

Disposable Chrome passed the ordinary loopback journey at the rename and again at `135e800`, covering the four surfaces, eleven system entries, rubric, direct family and FDI31 bookmarks, and the Model Survey Overlaps and Gaps archive. The FDI31 button returned the exact 2,052,220-byte Balanced GLB. The final browser pass blocked both a missing response and a same-length mismatched payload. The [Git-pinned fetch command](../../../transport/tools/fetch_asset.py) fetched that same export from the public host at `5eed87c` into a fresh cache.

### 2026-11-20 · Finding · not-required

The hosting config, publication reference, retirement notice and full 1,149-route local delivery index match `5eed87c` byte for byte. The public hostname returned the 1,001 published routes, all matching the local index by filename, MIME type, byte count and SHA-256. The separate retained FDI31 handoff source at `c0d43d1` contains the original publication `f69d317`, pinned framework `f65265c` and moved local checkout's head `3d1bb00` in its ancestry. Its hosting bindings match the moved Site. The existing local publishing checkout and recovery files moved with the source. The two previews using the old source directory were stopped before moving it.

### 2026-11-20 · Handoff · pending

The published Site still has its pre-Wave 1 experience. Future cutover needs the new title, routes and hosted Worker checked after authorized publication. The live index comparison establishes compatibility of the 1,001 declarations. The 148 additional local declarations and their payload availability have their own delivery acceptance.
