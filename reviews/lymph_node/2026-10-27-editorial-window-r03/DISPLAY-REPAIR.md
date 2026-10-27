# Normal, color and culling follow-up — local WIP

Related [issue 101](https://github.com/qianyizhang/med-assets/issues/101).
This follow-up compares two local display representations without changing
anatomical surfaces. Recommend no canonical replacement. Retain the fully split
variant as a diagnostic; the source, r03 and failed receipts remain unchanged.

## Intended display and cause

The intended use is inspection of provider-named regions through an editorial
window. Keep the source's single-sided material semantics and existing face
windings; do not infer vessel identity, tissue thickness or anatomical outward
directions. A successful display is not a closed mesh for volume analysis.

R03 contains 164 referenced normal corners that are zero or tiny cancellation
remnants, around 1e-12 to 1e-10. Valid normals are approximately unit length.
Normalizing the tiny remnants assigns an unsupported direction. The repair
preserves valid authored normals exactly and replaces only these 164 invalid
corners with the unit normal of their existing oriented triangle. The 1e-6
classification threshold lies in the measured gap; unexpected intermediate
lengths fail rather than receiving an invented direction.

All used source vertex colors are white RGBA. The previous exported white RGB
with implicit alpha one was already equivalent. This is a verification gap
closure, not a palette repair. Color/alpha loss is now checked explicitly.

Blender 4.3.2's importer stores colors as BYTE_COLOR and validates mesh faces
before assigning custom normals. Merely splitting duplicate indices and repaired
corners still produced 20 medulla and 137 network nonunit corner normals. A
power-of-two local-coordinate scale probe did not fix them. These failed drafts
and probes remain local. Fully separating triangle corners removes the affected
normal-fan sharing, preserving positions, winding and every face occurrence.

## Comparison and disposition

Fully split diagnostic SHA-256:
`5f887b4978d4b1c2edb3d80dee43a5a7d84f7b518849407622ccabb6e32a81be`.
Both variants retain 167,367 triangles and the same geometric support, materials
and colors. The smaller retained candidate has 7,614,472 bytes and 93,453
referenced vertices; the split diagnostic has 22,104,552 bytes and 502,101
referenced vertices. Splitting costs about 2.90 times the compact bytes and
5.37 times its referenced vertices, without an observed visual benefit.

Sequential builds on the same shared host took 1.30 s /117,772 KiB peak child RSS
for the current compact recipe and 2.64 s /169,028 KiB for full splitting. The
current compact recipe differs from the retained comparison only in explanatory
extras (96 bytes); its geometry/material document and binary data are exact.
These are build costs, not viewer, GPU-memory or frame-time benchmarks.

| Check on the fully split diagnostic | Result |
| --- | --- |
| World positions, oriented face multiplicities, colors, materials and transforms | Passed; all 106 previously lost reversed occurrences survive. No geometry displacement or blanket double-sided material change. |
| Finite unit normals | Passed at fresh import, actual stock scene export, and export followed by full corner splitting and fresh reimport. |
| Source-normal direction target of 0.05° | **Failed**, retained. Maximum measured drift is 0.647354° on import and 0.647380° after the explicit roundtrip path. No target was silently enlarged. |
| Visual/usefulness | Matched whole, detail and reverse pixels inspected. No obvious improvement or degradation at those views; the concrete benefit is valid display normals and preserved facing/color semantics. |
| Anatomy, clinical, browser runtime | Unvalidated; vascular identity stays unresolved. No promotion. |

The fully split version has a demonstrated tool-specific correctness benefit:
its imported normals are valid where the smaller candidate still yields 157
nonunit corners, including three zero normals. It also preserves the declared
single-sided facing. This does not prove that all coincident reversed records
are necessary for the teaching view, or that extra bytes improve that view.

**No-change recommendation:** keep both local candidates and their receipts. Do
not select the split diagnostic as the default asset merely to preserve source
multiplicity or meet a precision target. Its 0.05° target was an experimental
fidelity check, not a medical or repository acceptance requirement. The real
remaining decision is supported-viewer normal/culling behavior and practical
performance. There is currently no evidence that justifies a 2.90× payload for
the intended display. The compact candidate is also not certified through the
stock Blender path, so neither becomes canonical from this pass.

The roundtrip derivative comes from Blender's actual exported scene, then
lossless corner splitting before reimport. It is separate from the selected
candidate, whose valid source normal bytes remain unchanged. An unmodified
stock-export/reimport workflow is not certified by this result. Exact normal
identity is not the teaching-use goal, but the stricter failed target remains
visible and other camera/lighting/runtime behavior is untested.

Cycles ignores the material culling flag in the tested path. A controlled plane
probe confirmed this. Both comparison variants therefore use an explicit,
review-only Backfacing-to-Transparent shader treatment; it is never serialized
into the GLB. These images demonstrate offline single-sided visibility, not
browser runtime. Open surfaces and missing continuity remain intentional.

The validator rejects color/alpha loss, absent colors/normals, reversed normals,
lost faces, changed materials and culling. Coincident normal tuples are matched
one-to-one. Independent review also corrected a diagnostic matching bug that
could choose an unnecessarily bad pairing when reporting angular drift; the
diagnostic now minimizes the maximum angle without reusing source occurrences.
The earlier bad measurements and the receipt-count correction remain recorded.

## Reproduce

First build the pinned r03 with the existing [recipe](README.md#reproduce-into-new-output-directories).
Use new output directories for both steps:

```sh
python3 tools/lymph_node/editorial_window_r03/display_repair.py \
  --input /tmp/lymph-r03-new/lymph-node-editorial-window-r03.glb \
  --output /tmp/lymph-display-new --full-split

blender --background --factory-startup --disable-autoexec --threads 4 \
  --python-exit-code 1 \
  --python tools/lymph_node/editorial_window_r03/display_repair_blender.py -- \
  --prepared /tmp/lymph-display-new/prepared-display-repair.glb \
  --baseline /tmp/lymph-r03-new/lymph-node-editorial-window-r03.glb \
  --output /tmp/lymph-display-review-new --render

python3 tools/verify.py offline
```

Read the separate validity and failed angular-budget fields in the receipt;
successful execution means the review completed, not that all gates passed.
The diagnostic artifact, compact comparison hashes and corrected receipt are bound
in [decision.json](decision.json). Keep the PR draft and issue open pending
supported runtime evidence and a separate payload/acceptance decision.
