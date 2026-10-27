# Lymph-node editorial window r03 — WIP

Related: [issue 101](https://github.com/qianyizhang/med-assets/issues/101).

The earlier capsule/medulla window exposes internal layers, but the dense front
network still obscures the follicles and paracortex. R03 applies that same
editorial window to the front of the network, retaining its rear/peripheral
surfaces and the enclosing context. It is useful for inspecting the source's
named regions. The vascular identity remains unresolved; see
[the primary-evidence decision](LABEL-DECISION.md).

This draft contains a reproducible recipe and review evidence in text form.
Generated GLBs, PNGs and Blender scenes remain local. No new LFS pointers,
transport manifest, upload, canonical replacement or catalog promotion is part
of this proposal. The intact source remains the exterior reference.

## Local result

The later [display comparison](DISPLAY-REPAIR.md) repairs invalid raw normals
and verifies colors/culling. Full corner splitting fixes Blender normal validity
at a substantial byte/vertex cost, with no observed visual benefit. Keep it as a
diagnostic and make no canonical change; the original r03 results below remain
unchanged.

The [follow-up import review](IMPORT-REVIEW.md) distinguishes intact geometric
support from lost winding and single-sided visibility. It preserves the original
106-face failure, adds executable source-pair accounting and negative tests,
and leaves the generated candidate unchanged.

Matched intact/r02/r03 exports were rendered at whole, second-oblique, reverse
and detail views using the same cameras, scale, source materials and lighting.
Actual pixels were inspected. The green region and blue follicles are easier
to see; the rear network remains visible from the front. The reverse capsule
outline remains, although the pink fringe formerly visible at the window edge
is omitted. This is a visibility trade-off, not a repair of vessel anatomy.

In the first controlled object-ID view, visible follicle pixels increase from
22,519 to 27,144 (+20.5%) and paracortex pixels from 27,933 to 72,396 (+159.2%).
Both improve in the second oblique and detail views too. These are screen
visibility measurements, not tissue quantities or anatomical coverage.

The source and candidate retain the same transforms, materials and provider
metadata. Four source meshes are unchanged. Capsule and medulla arrays equal
the earlier r02; the network is the only additional edited mesh. Retained
fragments remain on their assigned source triangles within 5e-8 m after float32
export. No tissue caps, synthetic interiors, displacement or palette change
are introduced. The clipped surfaces are open editorial omissions.

The first candidate failed on two zero-area fragments after float32 export.
Removing only those exposed a third fragment with reversed orientation. Both
failed drafts remain local. The final builder tests serialized coordinates and
omits all three precision-invalid fragments, totaling 2.332989191070387e-13 m²
of pre-quantization fragment area. This is not the area of their source parents.
The verifier's nonzero-area, positive-orientation and distance criteria were
kept unchanged.

| Gate | Result |
| --- | --- |
| Pinned GLB surfaces and deterministic replay | Passed within the declared clipping scope; actual negative controls reject corruptions. |
| Visual usefulness | Pass with limitations for source-region inspection; tissue and vessel continuity are intentionally omitted. |
| Direct GLB-to-Blender oriented preservation | **Failed:** Blender drops 18 medulla and 88 network opposite-winding duplicate faces inherited from the source. No unique unoriented surface was lost. |
| Additional surface-support audit | Exact supports and unambiguous winding pass with individually source-traced exceptions; single-sided front-face support and exact normal preservation fail separately. No appearance-equivalence claim. |
| Blender import → export → reimport | Exact oriented triangle multisets and coordinates match for all seven already-imported meshes. This narrower pass does not erase the preceding failure. |
| Anatomy / clinical | No new acceptance; no histological identification, flow or patient-specific reconstruction. |
| Browser runtime | Untested. Local Blender rendering is the demonstrated workflow. |
| Publication / canonical status | Code-and-text WIP only; generated payload delivery and candidate acceptance remain pending. |

R02 has 217,275 raw triangles / 10,347,068 bytes; r03 has 167,367 triangles /
14,190,680 bytes. The source-prefix and full-attribute approach makes the file
37.1% larger despite 23.0% fewer triangles. This is not a download-size
optimization. The final r03 build took about 21 s and 198 MiB peak process RSS;
four material renders, four ID passes and roundtrip took about 176 s and
687 MiB on Blender 4.3.2 / four CPU threads. Shared-host timings are not a
benchmark or interactive viewer measurement.

## Reproduce into new output directories

Prerequisites: Python 3 standard library for build/check; Blender 4.3.2 for
render/reimport. The original source GLB must be hydrated through the existing
repository LFS workflow. Missing inputs or dependencies fail; no suite is
silently skipped. No downloads, installations or credentials are performed by
these scripts.

```sh
python3 tools/lymph_node/editorial_window_r03/build.py \
  --source models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb \
  --output /tmp/lymph-r03-new

python3 tools/lymph_node/editorial_window_r03/check.py \
  --source models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb \
  --candidate-dir /tmp/lymph-r03-new \
  --replay-output /tmp/lymph-r03-replay-new \
  --report /tmp/lymph-r03-check-new.json

blender --background --factory-startup --disable-autoexec --threads 4 \
  --python-exit-code 1 \
  --python tools/lymph_node/editorial_window_r03/render.py -- \
  --input /tmp/lymph-r03-new/lymph-node-editorial-window-r03.glb \
  --build-receipt /tmp/lymph-r03-new/build-receipt.json \
  --output /tmp/lymph-r03-renders-new --roundtrip --all-views
```

Require the final render receipt and actual images, not just a process exit.
The render roundtrip checks the representation after first Blender import;
its receipts explicitly preserve the direct-import limitation above.
The reviewed artifact identities and original local evidence hashes are in
[decision.json](decision.json). The first ready decision still needs scoped
anatomical review, supported runtime evidence and an approved payload delivery
decision; this WIP does not close issue 101.

Source: Kristen Browne; Heidi Schlehlein. 2022. *3D Reference Organ for Lymph
Node, Male v1.2*. [DOI 10.48539/HBM299.VVXH.634](https://doi.org/10.48539/HBM299.VVXH.634),
CC BY 4.0. Modified for editorial display; no endorsement. Preserve attribution
and change notices when reusing generated derivatives.
