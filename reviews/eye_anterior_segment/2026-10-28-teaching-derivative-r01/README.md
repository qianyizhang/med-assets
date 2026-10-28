# Three-structure eye order study — local draft derivative

This successor to [issue100](https://github.com/qianyizhang/med-assets/issues/100)
and [PR113](https://github.com/qianyizhang/med-assets/pull/113) removes unsupported
ciliary/zonular geometry from an actual export. It retains only cornea, iris and
lens for the already accepted broad anterior order. **Draft; parent visual/scope
review pending.** It is separate from the unchanged diagnostic export and approved
assets. No binary or new LFS pointer is included in this code/text package.

The [accepted claim/reference decisions](../2026-10-28-teaching-scope-r02/README.md)
apply unchanged. The pupil is an opening surrounded by the iris; the opaque blue
disk is the lens behind that opening. The omission must not imply that living eyes
lack support tissues. This is neither a normal atlas nor an attachment lesson.
No corneal shape/thickness, optical, accommodation, surgical or clinical validity
is claimed. Illustrative transparency, opaque lens, double-sided surfaces and
inherited open/faceted boundaries remain limitations. No source defect is repaired
or relabeled to imply anatomical validity.

## Exact derivation and preservation

The [recipe](../../../tools/eye_teaching/build.py) accepts only the exact existing
[diagnostic export](../../../models/eye_anterior_segment/exports/hra-v1.3-r01/anterior_segment.glb),
SHA-256 `457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750`,
10,054,784 bytes. Its seven nodes are independent scene roots with no nonidentity
ancestor relationship to reconstruct. Copying the three selected nodes preserves
their local/world relationship. Node extras retain source labels as provenance,
not independent anatomical proof.

The derivative deletes the ciliary body, ciliary muscle, ciliary processes and
suspensory ligament nodes, their meshes/materials and unused accessors/buffer data.
The nine referenced accessors retain exact indices, positions and normals; retained
node metadata/transforms and materials compare exactly. Unreferenced historical
normal arrays are removed too. No geometry simplification, new surface, cap,
normal regeneration or material change occurs. Root extras carry draft status,
scope, exact baseline hash and the original provenance extras.

The [build receipt](build-receipt.json) identifies the local output
`eye-order-study.glb`: SHA-256
`f19ee7388a85d9661f8cad7cec7a1033d5406e2fda3ee8e4b98597572d8ba2da`,
2,594,032 bytes, 3 mesh nodes and 44,301 triangles (baseline: 150,793 triangles).
Size/triangle reductions describe this omission; they are not measured viewer
performance improvements. Original diagnostic and raw source bytes stay intact.
The provider-specific metadata/distribution discrepancy remains unresolved.

Source: HRA Eye Male Right v1.3, Kristen Browne and Heidi Schlehlein; Visible Human
Male / National Library of Medicine. [Attribution and CC BY 4.0](../../../models/eye_anterior_segment/ATTRIBUTION.md),
[intact source/provenance](../../../sources/datasets/hra/eye-male-right-v1.3/source.json).
Derivative change: editorial omission and compact repacking only. No endorsement.

## Reproduce locally

Python 3.11+ uses only the standard library for export/integrity. Blender 4.3.2 is
needed for clean native import and pixels. Supply an already authorized exact
diagnostic payload; the recipe does not download or hydrate it. Use new output
directories; existing artifacts are never overwritten.

```sh
python3 -m unittest discover -s tests -p test_eye_teaching_derivative.py
python3 -O -m unittest discover -s tests -p test_eye_teaching_derivative.py
python3 tools/eye_teaching/build.py --source /path/to/anterior_segment.glb --output /tmp/eye-order-NEW
python3 tools/eye_teaching/build.py --source /path/to/anterior_segment.glb --output /tmp/eye-order-REPLAY
cmp /tmp/eye-order-NEW/eye-order-study.glb /tmp/eye-order-REPLAY/eye-order-study.glb
blender -b --python tools/eye_teaching/review_blender.py -- --baseline /path/to/anterior_segment.glb --candidate /tmp/eye-order-NEW/eye-order-study.glb --output /tmp/eye-order-NEW/review
python3 tools/verify.py offline
```

The six focused tests cover removal, changed retained data/material/transform,
hidden unused payload, reintroduced nodes, unsupported hierarchy/dependencies,
wrong source, malformed output and missing scope/provenance. The same checks run
under optimized Python without relying on assertions. Actual replay binds the
pinned payload and byte-identical output separately from synthetic CI checks.

The native review imports both actual exports into clean scenes, compares retained
imported geometry/normals, transforms and material assignments, then renders two
matched pairs: anterior context and superior oblique detail. Camera, framing,
lighting, exposure and background are shared; no visibility trick hides candidate
nodes. The detail is diagnostic evidence of omission, not an attachment lesson.
Inspect actual pixels separately from the technical receipt.

## Gates and remaining work

- Technical: focused tests and exact deterministic replay passed; native reimport
  and visual results are being collected for this draft.
- Visual: parent review of matched context/detail is pending.
- Anatomy: reuse only the accepted broad-order reference screening; no new approval.
- Runtime: browser/actual review-gallery acceptance remains unverified. The existing
  `ci/glb_runtime_probe.py` is restricted to its reviewed GitHub Actions job; it was
  not run locally or bypassed. Issue99 consumer work remains paused and separate.
  Native Blender import/render does not establish browser runtime.
- Delivery: code, recipes and text receipts only. GLB/PNG outputs remain local.
  No Site, transport, LFS publication or canonical promotion. Parent reviews before
  merge; publication and downstream consumer work require separate acceptance.
