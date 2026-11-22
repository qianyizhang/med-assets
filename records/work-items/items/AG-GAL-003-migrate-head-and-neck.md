---
description: Prove the first complete legacy collection migration using the salivary study.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-003
work_status: done
work_kind: build
added: 2026-11-20
tags: gallery, evidence, transport
depends_on: AG-GAL-002
residual_of: none
residual_items: none
---

# AG-GAL-003 — Migrate Head & Neck to Anatomy Gallery

## Intent

Deliver the salivary teaching stop, exact Library exports and saved review on the ordinary Site. Keep the published addresses usable through the cutover.

## Acceptance Criteria

- [x] Give every referenced asset an exact Library disposition. Verify the gland and context exports and preserve their attribution.
- [x] Teach gland location and the supported duct course. Describe the unresolved crossing at the relevant lesson view and link to the rejected reconstruction and its evidence in Compare.
- [x] Check the new journey, source limitation, old page bookmarks and actual responses at all nine file addresses against the [migration contract](../../../docs/gallery/migration.md#page-addresses-and-file-addresses). After authorized publication and successful readback, replace the old visitor interface with its compatibility page or redirect. Record its destination, the remaining file routes and live checks.

## Context and Trade-offs

The [Head & Neck manifest](../../../transport/manifests/7b3860f7d29b8cf4e19190dee4bf7499bbe69e9924c7057021460edc4239fe53.json) identifies two GLBs and seven WebPs. The existing delivery index match establishes recorded identities. The collection can finish while its old host still serves compatibility. Full shutdown is tracked in [AG-GAL-008](AG-GAL-008-retire-head-and-neck-host.md).

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Selected as the first complete legacy collection |
| 2026-11-20 | Maintainer and Codex | deferred | ready | Wave 1 passed locally. Proceed with the local migration and review the assembled Gallery before public cutover. |
| 2026-11-20 | Codex | ready | wip | Local journey passed. Hosted acceptance remained open. |
| 2026-11-22 | Codex | wip | done | Both public handoff entries and all nine original file responses passed. |

## Implementation Ledger

### Local journey and legacy disposition

Chrome followed Use Cases → Head & Neck → Parotid duct course → Compare → Asset Library, returned to the selected stop, and checked keyboard activation and 390 px reflow. The loopback responses matched the size, SHA-256 and media type of both GLBs and all seven WebPs in the owner's [review decision](../../../reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json). A failed diagnostic request left its caption and review link usable. The Gallery build refuses a changed delivery binding for the reviewed exports or witnesses. The display retains the original bounded finding and attribution. The rejected reconstruction is represented by its diagnostic image and the owning replay.

On 2026-11-20, read-only legacy GETs returned the [homepage](https://anatomy-head-neck-review.landy123007.chatgpt.site/) and [review root](https://anatomy-head-neck-review.landy123007.chatgpt.site/review/salivary-native-r02/) and matched all nine file URLs exactly, including the two GLBs served as `application/octet-stream`. The superior context WebP matched on retry after a timeout. That check preceded the fragment handoff rehearsal.

### 2026-11-22 release rehearsal

**Local go for Head & Neck.** The homepage and salivary review now have a rehearsed, explicit **Open in Anatomy Gallery** link. Keep the original page beneath it so bookmarked sections, the bilingual toggle, native evidence width control, records and downloads are still available. The fragment changes the link destination without moving the visitor. Browser Back returns to the original URL and fragment, and the original changelog remains at `#changelog` and `/CHANGELOG.md`. An ordinary link to the gland-location stop is present if script execution is unavailable.

| Fragment on either legacy page | Gallery destination |
| --- | --- |
| Empty or `#annotation` | `/#/use-cases/head-and-neck/location` |
| `#native`, `#views` | `/#/use-cases/head-and-neck/duct-course` |
| `#negative`, `#negative-image`, `#comparison`, `#checks`, `#records`, `#record-links` | `/#/compare/salivary-native-r02` |
| `#downloads`, `#media-links` | `/#/library/salivary_glands/z-native-scoped-r02` |

The local browser walked gland locations, the parotid course, rejected crossing, exact Library links and returns. The source limitation and the resolved and unresolved duct evidence remained visible. The [file-service receipt](AG-GAL-008-retire-head-and-neck-host.md#2026-11-22-file-service-rehearsal) traces the nine pins and exercises HTML and file rollback. The [private staging result](AG-GAL-013-reconcile-gallery-coverage.md#owner-only-staging--2026-11-22) covers the hosted journey and all nine files. The [legacy-host rehearsal](AG-GAL-013-reconcile-gallery-coverage.md#legacy-host-release-rehearsal) verified both hosted entries from the exact owner source on a dedicated owner-only copy. The bilingual and full-width controls remained usable. The nine pairs matched and the production destination map passed separately. Head & Neck v2 passed both public handoff entries, Gallery navigation, reload and Back, and all nine original file responses. The [public release record](AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) owns the live version and rollback.
