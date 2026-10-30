# Median nerve: native wrist and hand skeletal localization

![New regional study: whole locator, palmar hand and oblique wrist detail](v2/teaching.png)

**The selected median nerve groups become traceable against wrist and hand
landmarks.** This is a separate licensed supplement for
[#164](https://github.com/qianyizhang/med-assets/issues/164), related to #150.
The original schematic and merged ulnar/elbow PR161 are preserved.

- **Built:** practical 834,404-byte GLB, 33 source objects / 38,414 triangles.
  Median trunk, common/proper palmar digital groups, native humerus/radius/ulna,
  eight carpals, five metacarpals and fourteen phalanges.
- **V2:** bilingual group/landmark labels, full-subset locator and source-end notes.
  Exact V1 GLB and raw captures are reused; geometry and materials are unchanged.
- **Scope:** skeletal localization. Soft tissues and the disputed flexor/nerve
  relationships are excluded; no complete branch, skin-territory, tunnel, clinical,
  physical-scale, motion or live-runtime claim.

## Original / Updated context

**Original:** [existing whole-body scaffold contact](https://anatomy-verification.landy123007.chatgpt.site/review/evidence/canonical/draft_peripheral_nerves__2026-10-23-v10-exterior-review/0f8add5d026e7b55fc8cb6182f146dada1443a4e1f84fa7476c7d5820bd41f9b.webp),
independently inspected by the parent: sparse planar routes and finger-like ends
without wrist landmarks. **Updated:** the separate native regional study above.
These are different models with independent cameras/scales, without registration;
the comparison concerns added teaching context, not an incorrect-route diagnosis.
The implementer did not receive or inspect the original GLB or baseline image
bytes, and no failed baseline transfer was retried for this task.

Historical binding: `draft_peripheral_nerves`, revision `v10-837077aeece2`, source
GLB SHA-256 `fce4ff0a0500b618b9ee014c56eef10164560d60b7efe7e287b619383d29b712`;
static capture `2026-10-23T01:34:27.647601Z`. Display derivative SHA-256
`2020be843344f381988f0380e695af7d211e1b30625f90eba92b1bdba58a0ac1`.
Historical image ownership is not inferred from GLB metadata. No old scaffold is
rebuilt, replaced or republished by this package.

## Separate gates

| Gate | Result and boundary |
|---|---|
| Source/license | Pinned archive and native member rehashed; CC BY-SA 4.0 and historical BodyParts3D attribution retained |
| Technical | [Validation receipt](validation.md): exact source replay; all 33 surfaces/transforms preserved; six visible leader checks, six scoped tests and 205 aggregate tests passed |
| Visual | [Independent V2 review accepted with limitations](independent-review.md); color/detail views preferred because grayscale nerve–bone contrast is reduced |
| Anatomy | Gross course reference-screened; unresolved soft-tissue relationship remains excluded |
| Clinical/runtime | Unverified; no motion or physical-scale validation |
| Publication | [Bounded upload and fresh GitHub payload readback passed](delivery.json); draft PR and runtime remain separate |

The [recipe](../../../tests/peripheral_nerves/median-wrist-r01/README.md) describes
exact replay and separate scoped tests. The broader offline gate covers only its
documented repository scope. GLB SHA-256:
`6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50`.

<details><summary>Source/export verification and retained failed trials</summary>

Source pin: Z-Anatomy `c08bde5325e35a46404d86a6bd458c484297cc2d`,
`Z-Anatomy/Startup.blend`, SHA-256
`9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`.
[Complete provenance](../../../sources/datasets/z-anatomy/median-wrist/provenance.json)
includes source archive/member sizes and hashes, selected names, modifications
and exact retained license references. Source scripts and add-on are disabled.

The native soft-tissue context was inspected first. Main flexor `.r` objects have
muscle and tendon regions; `.er` insertion markers were not mistaken for tendons.
The four [soft-tissue diagnostics](preflight/soft-tissue/bindings.json) show the
retinaculum present versus hidden as **visibility states**, not changed anatomy.
Even with it hidden, the median trunk was obscured by flexors. A visible lateral
branch must not be relabelled as the trunk.

[Surface screening](preflight/relationship-screen.json) found wrist-region median
nerve overlap candidates with FDP (131), radial FDS (60) and humero-ulnar FDS
(204). These are screening candidates, not a quantitative penetration or clearance
proof. Together with the pixels, they leave the stronger soft-tissue lesson
unsupported. Omission does not repair that source relationship. The independent
reviewer and parent inspected the narrower [skeletal preflight views](preflight/skeletal/bindings.json)
and found useful localization value; that review alone did not accept the export.

The exact-GLB V1 [raw views](v1/renders/bindings.json) were independently inspected.
The [source/reimport check](v1/source-reimport-check.json) found maximum vertex
difference `1.22028140481234e-7` native units with `1e-6` numerical tolerance.
This is export precision, not anatomical accuracy. All 38,414 evaluated triangles
were compared after exact coincident-source-coordinate seam welding; source
surface topology was not repaired or fused.

V2's first header overlap is retained in `v2-initial-layout`. The next trial's
scaphoid leader was attached to a source vertex hidden by the trapezium in both
labelled views; the failed [visibility receipt](v2-occluded-landmark/locator-check.json)
and images remain. The corrected point is scaphoid reimport vertex 47, visible in
both views. [Six corrected leader checks pass](v2/locator-check.json). Only the
annotation binding changed; [reused captures](v2-captures/bindings.json) retain
the exact raw image bytes, cameras, lights and scale. These verification steps are
separate from the Original/Updated teaching-context comparison above.

Reference screening: [AAOS's gross median wrist/hand course](https://www.orthoinfo.org/diseases--conditions/carpal-tunnel-syndrome/)
and [Meyer et al.'s nerve/flexor relationship](https://pmc.ncbi.nlm.nih.gov/articles/PMC6032467/).
Neither validates this source's coordinates, branch completeness or clinical use.
No reference illustration or textbook passage is copied.

</details>

Geometry and derived renders: **CC BY-SA 4.0**. **Z-Anatomy — The libre 3D atlas
of anatomy — CC BY-SA 4.0**; **BodyParts3D — The Database Center for Life Science
— CC BY-SA 2.1 Japan** (historical attribution). Provider roles and limits are in
the model README and source record. No full atlas, cranial nerve, inner-ear,
kidney or source add-on payload is included.
