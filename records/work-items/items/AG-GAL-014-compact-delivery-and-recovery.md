---
description: Consolidate delivery and recovery for one identified set of assets.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-014
work_status: deferred
work_kind: build
added: 2026-11-20
tags: transport, repository
depends_on: AG-GAL-007
residual_of: none
residual_items: none
---

# AG-GAL-014 — Apply the first verified storage change

## Intent

Apply the choice supported by [AG-GAL-007](AG-GAL-007-plan-r2-and-recovery.md) and measure the change in maintained copies, stored bytes or recovery steps.

## Acceptance Criteria

- [ ] Identify canonical files, SHA-256 values, sizes, required delivery routes and backup members before the change. Name the copies to consolidate and any unique material to preserve.
- [ ] Apply the accepted change through the [transport workflow](../../../transport/README.md). Fetch the exact files on demand in a fresh checkout and restore each affected retained archive, verifying its required members. Check missing or corrupt remote data and preservation of existing local edits.
- [ ] Verify affected consumers and any public file routes through their supported entry points. Under the applicable authorization, retire superseded copies once recovery passes. Record the before/after result and any compatibility copy that still has a consumer. If the study finds no redundant copy, close with the evidenced retention decision.

## Context and Trade-offs

This item owns the asset and storage change. [AG-GAL-012](AG-GAL-012-consolidate-transport-tools.md) owns the tool and index path moves. Preserve historical manifests and source-specific rights.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Codex | — | deferred | Consolidate delivery and recovery for one identified set of assets. |

## Implementation Ledger

### Decision · Retain the public Airway downloads

Airway v8 still serves the original same-origin `trachea-open.glb` and `trachea-cutaway.glb`, and their linked bytes matched the evidence pins after handoff. Keep both backing copies while the review and evidence file consume them. The [recovery study](AG-GAL-007-plan-r2-and-recovery.md) identified 2,527,180 bytes in deployment inputs. An alternate backing source would need to prove both original addresses still serve the pinned bodies before any copy qualifies for retirement. The [public release record](AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) owns the version and independent rollback.

### 2026-11-22 retention and file rollback rehearsal

The legacy r06 HTML uses two explicit download links under [`/review/trachea-r06/models/`](https://anatomy-airway-review.landy123007.chatgpt.site/review/trachea-r06/). Its [`evidence.json`](https://anatomy-airway-review.landy123007.chatgpt.site/review/trachea-r06/evidence.json) pins both independently of the 13 Airway manifest URLs. The [build record](../../../reviews/trachea/2026-10-29-open-airway-r06/build-record.json) and Gallery delivery index agree. Both old links downloaded the exact files in the stand-in browser. Both legacy and both Gallery URLs passed full GET verification locally and through the dated live readback. Keep both legacy files and their original paths, along with the bilingual raster comparison which links to them.

For local reversibility, the stand-in served each original URL from the same verified backing bytes as Gallery, then exercised a cross-origin 302 and unavailable backing. Restoring the original copy at the original path returned the expected complete GLB for both files. In a future authorized rollback, restore the previous origin mapping and retained copies together. Reopen the original review, download both files, and verify HTTP status, GLB content type, entire body and SHA-256 against `evidence.json`. Confirm the exact Gallery Library exports independently and check routes again from a fresh client after cache invalidation if required. This rehearsal changes zero storage copies and zero tracked LFS bytes.


### Hosted file-service result

The exact owner-source Airway copy kept the two model paths and the bilingual five-raster comparison through its handoff. Full reads of both private legacy and private Gallery model addresses matched the production evidence pins. The retained Airway HTML still resolves each download control to its original same-origin model path. Redeploying the private Airway baseline independently restored both exact model responses, all 13 other pins and the original page behavior. Keep both copies and their original paths through public cutover and any rollback. The [joint hosted evidence](AG-GAL-013-reconcile-gallery-coverage.md#legacy-host-release-rehearsal) records the runtime checks. The maintainer accepted the [private download limitation](AG-GAL-013-reconcile-gallery-coverage.md#whole-gallery-release-assessment).
