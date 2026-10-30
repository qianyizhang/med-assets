# Sciatic nerve: posterior hip skeletal locator

![New regional study: whole locator, posterior hip and oblique detail](v2/teaching.png)

**Locate the retained sciatic course using posterior hip landmarks.** This separate
licensed supplement addresses [#166](https://github.com/qianyizhang/med-assets/issues/166),
related to collection #150. The original scaffold, ulnar PR161 and median PR165
remain separate.

- **Built:** 559,144-byte GLB, four objects, 24,154 stored triangles. Sciatic nerve,
  right hip bone, sacrum and full femur preserve their native spatial relationship.
- **V2:** three bilingual landmark labels, orientation, whole-region locator and
  source-end notes resolve identification and endpoint ambiguity. V1 geometry,
  materials, cameras and raw pixels are unchanged.
- **Scope:** skeletal localization only. Partial proximal strands and distal source
  cutoff remain; the native piriformis relationship is unresolved and excluded.

## Separate gates

| Gate | Result |
|---|---|
| Source/license | Pinned ZIP/member rehashed; [CC BY-SA 4.0 and provider attribution](../../../sources/datasets/z-anatomy/sciatic-hip/provenance.json) retained |
| Technical | Exact replay; all stored surface triangles/transforms checked; six visible label targets; five scoped tests passed. Export/import limits below |
| Visual | [Independent V2 review accepted](independent-review.md), 07:47:06 UTC; color is preferred to grayscale |
| Anatomy | Gross skeletal landmark reference-screening only; no complete pelvis/plexus/foramen or soft-tissue validation |
| Runtime/clinical | Unrun; no motion, physical-scale, surgical or live-viewer claim |
| Repository/delivery | **205 offline tests**, 26 manifests, 25 foundation records, 591 import references and 771 LFS pointer identities passed; fresh remote readback pending |

GLB SHA-256: `72077a97a8a935a7a4623443c1c0fd61ab48a9bf4ad895af058345b7a372abd6`.
[Recipe and checks](../../../tests/peripheral_nerves/sciatic-hip-r01/README.md).

<details><summary>Original / Updated context</summary>

**Original:** [historical whole-body peripheral scaffold](https://anatomy-verification.landy123007.chatgpt.site/review/evidence/canonical/draft_peripheral_nerves__2026-10-23-v10-exterior-review/0f8add5d026e7b55fc8cb6182f146dada1443a4e1f84fa7476c7d5820bd41f9b.webp),
independently viewed by the parent: isolated leg lines without pelvic landmarks.
**Updated:** the new regional study above. Different models, independent cameras
and scales, no registration; this shows added teaching context, not an incorrect
original nerve trajectory.

Historical asset `draft_peripheral_nerves`, revision `v10-837077aeece2`;
source GLB SHA `fce4ff0a0500b618b9ee014c56eef10164560d60b7efe7e287b619383d29b712`.
The implementer did not receive baseline image bytes or inspect its GLB. No
baseline transfer was retried, and the original is not rebuilt or replaced.

</details>

<details><summary>Source/export QA and retained rejected scope</summary>

The canonical [source binding](source-bindings.json) records four source objects
and effective matrices. [Capture bindings](v1/bindings.json) record fixed cameras,
lighting, exact raw images and six vertex/first-visible-object label checks.
[Composition bindings](v2/composition.json) reuse those inputs without duplicate
GLBs or captures. Source preservation is QA, not the teaching improvement.

The initial all-vertex reimport check failed because the source Sacrum contains
21 unused vertices that GLB export omits. A second difference is one narrow
source triangle `(2712,2713,2771)`, retained in the GLB but omitted by Blender 4.3.2
import (native double-area `1.942817136463481e-8`). The [corrected check](source-check.json)
decodes the stored GLB separately: all **24,154** source surface triangles match;
the reimport has **24,153**, with only that exact omission allowed. No route or
surface repair was made. Source masters and initial failed check diagnostics are
retained; this resolves check semantics, not anatomy.

All surface vertex clouds and effective matrices are checked, with `1e-6`
float32 precision tolerance—not anatomical accuracy. The fresh extraction replay
reproduced the exact GLB. This is separate from the five scoped tests and ordinary
offline gate.

Five [native diagnostic views](preflight/bindings.json) compare skeletal and shown
soft-tissue states using matching cameras. They visibly make the nerve appear to
emerge through piriformis. The native BVH screen found 150 nerve–piriformis
candidates and none with the three bones/two ligaments; this is not clearance,
penetration or variant validation. The soft-tissue lesson was rejected. Hiding it
does not repair that source relationship. Independent review accepted the
narrower skeletal question; details and primary references are in its record.

</details>

Geometry and derived renders: **CC BY-SA 4.0**. **Z-Anatomy — The libre 3D atlas
of anatomy — CC BY-SA 4.0**; **BodyParts3D — The Database Center for Life Science
— CC BY-SA 2.1 Japan** (historical attribution). No full atlas or source add-on
is republished.
