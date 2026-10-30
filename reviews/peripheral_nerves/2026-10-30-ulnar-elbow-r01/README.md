# Right ulnar nerve at the elbow — regional supplement

![Source study v1 / v2, matched whole and detail views](evidence/comparison.png)

![Source-bound teaching views](evidence/teaching.png)

**A small nerve–bone relationship becomes identifiable through native bony
context and bound landmark labels.** The historical whole-body draft is preserved
as a separate schematic. Related: #150; no closure, replacement or count promotion.

## What changed

V1 selected `Ulnar nerve.r`, `Humerus.r`, `Ulna.r` and `Radius.r` from the pinned
Z-Anatomy scene in its native evaluated world coordinates. The independent v1
review found the four-part relationship useful, with no reason to reroute the
nerve, but required bound landmark labels, clearer shading, whole context and
explicit limits. V2 darkens illustrative materials and adds a bilingual teaching
sheet with three bound locators, a detail-region box and source-extent markers.
The GLB's binary geometry, mesh definitions and transforms are unchanged from v1.

The initial 24-sample v1 images and their original bindings remain in `v1/`.
Fair v1/v2 comparison captures use the same cameras, lighting, scale, exposure,
background and 128-sample settings in `v1/matched-128` and `v2/raw-128`.
Both are fresh clean reimports of the exact exports. The failed first v2 label
layout is retained under `v2/initial-label-layout`: its extent leaders crossed
their text; final composition ends the leaders outside the text. No geometry
was changed for that correction. A failed denoiser configuration produced no
image; the render recipe now uses the available non-denoised Cycles path.

## Original scaffold evidence belongs to a separate review

The coordinator's independent native agent `build_second_asset_fix`
inspected the actual historical contact pixels at **2026-10-30 03:00 UTC**.
Its assessment: pale isolated generic limb routes, repeated disconnected central
segments, finger-like fans and marked side-view collapse; no elbow bones, medial
epicondyle, olecranon or named locally traceable ulnar relationship. This supports
a limited regional-context gap, **not a diagnosis of an incorrect nerve route**.

The implementing executor never received those baseline bytes: the supported
Library transfer and its single permitted retry failed without creating a file.
No further acquisition was attempted. The coordinator explicitly accepted its
independent baseline review as the basis for this separate licensed supplement.
That assessment is not relabelled as this builder's visual inspection.

[Historical static Blender contact](https://anatomy-verification.landy123007.chatgpt.site/review/evidence/canonical/draft_peripheral_nerves__2026-10-23-v10-exterior-review/0f8add5d026e7b55fc8cb6182f146dada1443a4e1f84fa7476c7d5820bd41f9b.webp)
is context only, not a matched cross-source comparison or browser screenshot.
Parent-recovered binding: asset `draft_peripheral_nerves`, revision
`v10-837077aeece2`, source GLB SHA-256
`fce4ff0a0500b618b9ee014c56eef10164560d60b7efe7e287b619383d29b712`;
capture `2026-10-23T01:34:27.647601Z`; original PNG SHA-256
`0f8add5d026e7b55fc8cb6182f146dada1443a4e1f84fa7476c7d5820bd41f9b`;
display WebP **38,790 bytes**, SHA-256
`2020be843344f381988f0380e695af7d211e1b30625f90eba92b1bdba58a0ac1`.
The original GLB was not inspected, rebuilt or republished. Its creator ownership
is not inferred from metadata. Neither accepted spinal r04 roots nor the existing
eight-part elbow bone/ligament study supplies this nerve–bone view.

## Sources and separate gates

[AAOS's anatomy description](https://orthoinfo.aaos.org/en/diseases--conditions/ulnar-nerve-entrapment-at-the-elbow/)
supports locating the ulnar nerve behind the medial epicondyle. It does not validate
these coordinates, caliber, pose or a patient's anatomy. No reference illustration
or textbook text is copied. Provider landmark endpoints are recorded in the
render recipe; leaders end at exact reimported mesh vertices. Semantic target
accuracy is independently reviewed in the images.

| Gate | Evidence and limit |
|---|---|
| Source | Exact pinned archive/member hashes checked; named four-part selection and source-compatible license retained |
| Technical | [Local validation receipt](validation.md): source and deterministic v2 replay; six scoped tests; exact geometry/transform preservation; payload, camera and locator checks; 189 aggregate tests |
| Visual | Independent v1 findings addressed in v2; [final review accepted with limitations](independent-v2-review.md) |
| Anatomy/clinical | Gross relationship reference-screened; no clinical, complete-tunnel or full-route certification |
| Runtime | Unverified; no browser test or motion evidence |
| Publication | Separate from local review; see delivery receipt when available |

Source-coordinate evidence in `v1/native-check.json` screens all four vertex
clouds bidirectionally against the full native scene: maximum difference
`1.23e-7` native units, below the `1e-6` numerical screen tolerance. This tolerance
concerns export precision, not anatomical accuracy. Nerve-versus-bone BVH screens
returned zero triangle-overlap candidates; no formal clearance/self-intersection
proof is claimed. Retained humerus open/nonmanifold source edges and coarse bone
form remain. Binary preservation makes those geometric findings applicable to v2.

Skin, muscles and retinaculum are omitted; the source endpoints do not establish
anatomical origins or termini. There is no modeled cubital tunnel enclosure,
complete nerve tree, patient registration, physical-scale or motion validation.
The 3D supplement is suitable only for the reviewed static gross relationship.

V1 GLB: `206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5`,
186,792 bytes. V2 GLB:
`94a7bde3f8a2882cc632082301d7701a737a769e1d1afe0f55629ecac3013ac3`,
187,708 bytes. [Recipe and checks](../../../tests/peripheral_nerves/ulnar-elbow-r01/README.md).

Selected geometry and derived renders: **CC BY-SA 4.0**. **Z-Anatomy — The libre
3D atlas of anatomy — CC BY-SA 4.0**; **BodyParts3D — The Database Center for Life
Science — CC BY-SA 2.1 Japan** (historical attribution). Kousaku Okubo, Gauthier
Kervyn and Marcin Zielinski retain their provider-stated roles. No endorsement.
[Provenance and retained provider license](../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json).
Full atlas, source add-on, kidney, inner ear and cranial nerve materials are excluded.
