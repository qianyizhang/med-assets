---
description: Give the maintained collection and the historical Body Systems replay clear homes.
scope: backlog item
status: stable
last_update: 2026-11-20
document_class: work_record
work_id: AG-GAL-005
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, repository, evidence
depends_on: AG-GAL-002
residual_of: none
residual_items: none
---

# AG-GAL-005 — Separate Body Systems replay from Site inputs

## Intent

Make the ordinary Site build consume an explicit Body Systems export. Give the dated reports, renders and recovery bundle a clear owner.

## Acceptance Criteria

- [x] Move the active display index and its 132 referenced WebPs as one slice, or document their retained package ownership. Preserve model, source image, display hash and route identities.
- [x] Rebuild using the Site-owned setup from [AG-GAL-001](AG-GAL-001-name-and-verify-gallery.md). Check the eleven collection entries and matched views after moving their display inputs, including a missing or corrupt display file.
- [x] Exercise the historical replay and backup member paths that the move affects. Preserve the inputs and recovery paths for retained evidence. If only the old report or loopback viewer breaks, record its lost interaction for the walkthrough. Compact obsolete output after verifying a replacement or recovery.

## Context and Trade-offs

The [survey package](../../../sites/body-systems-survey/README.md) owns the replay and teaching archive. The [local build](../../../sites/anatomy-gallery/tools/gallery_runtime.py) consumes the display index. Its viewer inputs have a separate [Site lock](../../../sites/anatomy-gallery/viewer.lock.json).

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Current Site dependencies identified during the directory review |
| 2026-11-20 | Codex | deferred | done | Display, ordinary preview, report replay and archive verified locally. |

## Implementation Ledger

### Local result

The maintained [Body Systems collection](../../../lessons/body-systems/README.md) owns the display index and 132 WebPs. The [dated survey](../../../sites/body-systems-survey/README.md) owns its builders, old report/3D replay and teaching archive. The Site routes, WebP sizes and digests, original render digests, camera evidence and model identities passed the move. The moved knee source has a current local path for replay preflight and its original published path at the pinned source revision.

The ordinary Site built from its own Three.js lock. Chrome opened the eleven systems and matched details, and the loopback server delivered all 132 WebPs with their exact media type, size and hash. A missing and a same-length corrupt file returned 503, and the browser kept the other view and the source links accessible. The restored file returned 200 with its exact bytes. The exporter ran into a fresh output root and reproduced all 132 WebPs and their display index.

The 127,459,034-byte teaching archive matched its recorded SHA-256 and all 327 members passed after fresh extraction. The dated reports rebuilt and their historical Chrome suite passed, including matched views, the loopback 3D launches and the s1233 comparison. Three byte-identical loose copies of the prompt file, jobs and revision marker were removed from the ignored report directory. The maintained builders and unique inputs, media, receipts and replay archive remain with their owners.
