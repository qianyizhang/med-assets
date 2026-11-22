---
description: Use exact-file review plates at two existing Anatomy Gallery teaching stops.
scope: loopback Anatomy Gallery teaching use cases
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: TAQ-008
work_status: done
work_kind: build
added: 2026-11-22
tags: gallery, teaching, evidence
depends_on: TAQ-003, TAQ-006
---

# TAQ-008 — Use reviewed plates in existing lessons

[Teaching asset review campaign](../../campaigns/teaching-asset-review.md)

| Teaching stop | Exact file and use |
| --- | --- |
| `#/use-cases/one-breath` | [Breathing Assembly](../../../body/breathing/Breathing_Assembly.blend). Compare expiration and peak inspiration from the same front and side views. The new local phase pair accompanies the original bilingual storyboard and preserves its authored-mechanics scope. |
| `#/use-cases/systems/lymphatic?detail=lymphatic-node-transit` | [HRA single node](../../../models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb). Compare the intact capsule and named tissue layers in one matched view. The separately labeled source view accompanies the lesson’s enlarged, authored flow illustration. |

The [lesson review plate](../../../sites/anatomy-gallery/app/src/content/gallery/LessonReviewPlate.jsx)
binds the selected campaign image to the export identity in local delivery. It appears
after the image loads at its reviewed dimensions. Both the regular hosted origin and
a failed local proof request display the ordinary lesson media. This change makes no
new claim about the disputed HRA vascular mesh or measured physiology.

## Verification

The protected Gallery build and [focused Chrome check](../../../sites/anatomy-gallery/tools/verify_lesson_review_plates.mjs)
passed on `e0eae25c3914c27cfd81fb72436e443b023bf487` plus the local teaching changes. The
generated HTML SHA-256 was `17d430f5e0330811f196f8a1d672a4030a62400e9b21722ab75f5056b0ba8c2c`.
The check exercised both routes at 1280 and 1024 pixels, confirmed each image’s
dimensions and response digest, and moved focus to each full-size image link. It
also forced an evidence 503, simulated a non-loopback host, and checked the adjacent
Nodal entry detail. Original lesson images stayed available. Inspected screenshots
are kept in ignored `.artifacts/taq-008/browser/`. The offline gate passed 448 tests,
26 transport manifests, 25 foundation records, 394 import references and 937 LFS pointer identities.

Start the read-only preview as described in the [Gallery workflow](../../../sites/anatomy-gallery/README.md).
Run the focused check with the Gallery Playwright and browser environment variables.

```sh
node sites/anatomy-gallery/tools/verify_lesson_review_plates.mjs
```
