# Pharynx/larynx: inspect retained cartilage layers

![Matched full context and cartilage isolation](v1/comparison-posterior-oblique.png)

![Matched cartilage detail](v1/comparison-cartilage-detail.png)

*Actual offline Cycles renders of the unchanged GLB, with matched camera, scale,
light and exposure within each plate. These are visibility illustrations, not
browser/UI screenshots or a new model.*

- **Change:** a reusable patch to the v40 isolated viewer for #150 adds cartilage
  (5 parts), muscles plus cartilage (30), reset (33) and an explicit camera-fit
  action. The posterior muscle covering previously prevented interactive
  cartilage isolation; the existing static close-up was cropped.
- **Independent review:** V1 isolation/context/detail/grayscale passed with a
  framing correction. V2 adds “Fit visible parts”; the full cartilage set is
  now centered with margins. No further visual/code correction was requested.
  [Actual reviewer findings](independent-review.json).
- **Preserved:** original source geometry, normals, materials, coordinates, raw
  names and disputed-side overrides. Source epiglottic holes are retained.
  No new supplement, source reconstruction or canonical-data replacement.
- **Limits:** local Chromium aborted before page load because its SUID sandbox
  helper was misconfigured. Actual browser/UI appearance and WebGL behavior
  remain unverified. Live candidate-script access was separately denied to the
  coordinator (`net::ERR_BLOCKED_BY_CLIENT`) and was not retried here. No
  security configuration change, new credentials, Site publication or merge.

## V2 correction

![Explicit camera fit: target and distance intentionally change](v2/comparison-fit.png)

The V1 isolated cartilage group remained low in the full-model framing. The
new fit action uses effectively visible mesh bounds, keeps the view direction
and adjusts only camera target/distance. Layer switches themselves retain the
camera. Reset followed by fit recovers the complete assembly. Both original
reset pairs and the full/reset fit pair have identical decoded pixels.

The new perspective plate uses coordinates produced by the actual controller
on the exact GLB, converted to Blender axes. Its intentional camera change is
captioned. The earlier matched visibility plates remain valid for V2: all
5/30/33 visibility sets are identical and the source artifact is unchanged.
The reviewer also corrected a receipt sentence that wrongly described the fit
pair as visibility-only; that metadata correction required no rerender.

## Binding and provenance

- Model: [r03 GLB](../../../models/pharynx_larynx/exports/r03/pharynx_larynx.glb),
  SHA-256 `d691a60f12d448b9b36d362270429c672c01c7fae0f10a8789ef188dd4c08530`,
  5,050,088 bytes, 33 mesh nodes / 278,720 indexed triangles. All 33 source IDs,
  names and hashes matched the retained source map.
- Five cartilage IDs: FJ2769 cricoid, FJ2770 epiglottis, FJ2775/FJ2792 arytenoids,
  FJ2808 thyroid cartilage. The remaining source parts are 25 muscles, two
  ligaments and the pharyngeal raphe. The latter three are omitted only in the
  explicitly disclosed 30-part context mode.
- BodyParts3D 4.0, OBJ 99% reduction; [pinned member/archive source map](../../../sources/datasets/bp3d-4.0-head-studies/external-source-map.json)
  and [DBCLS attribution](../../../models/pharynx_larynx/exports/r03/ATTRIBUTION.md).
  The publisher license page was freshly read on 2026-10-30 and states CC BY
  4.0, updated 2025-02-27. Historical CC BY-SA 2.1 Japan headers remain retained
  externally. Raw OBJ archives and historical authoring recipes were not rebuilt.
- Relevant viewer baseline: published v40 commit
  `11d91eea72408d8995ad9f60cd1c45b6341bd240`. The coordinator and source owner
  verified candidate controls/data unchanged from `e5d0539`. All seven supplied
  text files independently matched their [expected hashes](source-v40-hashes.json)
  after materialization. This does not claim whole saved-archive byte identity;
  the coordinator reported a different local tar container hash.
- Canonical `review-data.json`: SHA-256
  `a9ed5c5621899b8d99054848d7e8ef3574ffe16cb1cd0c414b6e1711522550f2`,
  1,061,189 bytes. Only the supplied candidate record is retained as a test
  excerpt; it is not a complete dataset or that file's byte identity.

## Checks and delivery

[Viewer patch and replay instructions](../../../gallery/pharynx_larynx/visibility-r01/README.md)
· [Patched file hashes](patched-viewer-hashes.json)
· [Scoped technical receipt](review.json)

Nine scoped Node checks use the actual GLB and pinned Three r180/jsdom 26.1.0.
They cover group membership, hidden-state restoration, source/missing-part
failures, neutral labels, DOM clicks/language changes, direction-preserving fit
at wide/narrow aspects, invisible ancestors and reset/full framing. Five Python
patcher checks cover exact baseline identity, unchanged data/camera path, failure
before writes, deterministic replay and repeated-application refusal.

V1 source is retained in local implementation commit `b2e142c`; its render/state
receipts remain in [v1](v1/). V2 camera correction and records are in [v2](v2/).
The normal offline gate and remote evidence availability are recorded separately
in `review.json` and the delivery receipt when complete. No runtime or clinical
status is promoted by those checks. #150 remains open; this is a viewer patch
for one bounded inspection task, with Site integration/deployment still separate.
