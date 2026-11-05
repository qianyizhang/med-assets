# Testis–epididymis native study — issue #150

**Pass with limitations:** a separate, static 3D gross-form supplement for
`draft_testes`. Four named Z-Anatomy source parts show a curved superior
epididymal mass and tapering profile against each testis. This improves on the
historical flat-strip schematic without inventing duct connections or internal
coils. Original `draft_testes` remains **Needs revision**, ledger count delta **0**.
Completed 2D teaching issue #129 is unchanged.

## Current review evidence

| Paired context | Posterior detail | Isolated side detail |
| --- | --- | --- |
| ![Current paired context](evidence/v2-pair.png) | ![Current posterior detail](evidence/v2-posterior-close.png) | ![Current isolated side detail](evidence/v2-side-close.png) |

These are fresh imports of the current exact GLB. Close views isolate the same
source-named right side without repositioning it. Tan identifies testis and rose
identifies epididymis; these are illustrative display colors. Camera names denote
native source directions, not independently validated anatomical axes.
[Render bindings](render-v2.json) retain current cameras and exact image identities.

V1 was rejected for a faceted superior contour, doubled-side detail and obscuring,
unvalidated deferens routing. V2 uses source render subdivision, isolates one side
for detail and excludes deferens. The rejected V1 renders and routine execution
receipts are retired; the findings remain in the independent review. Committed
old output remains in Git history.

The [historical flat-strip image](../2026-10-23-v10-exterior-review/draft_testes/screenshots/contact.png)
was also inspected. Its original GLB is external to this checkout:
`71c760a96d57798b83bfc4af9d94c577606591f13d59c6c102be79986e500f09`
(80,204 bytes). It is a different, unregistered model; no matched old-draft/source
shape or physical-size comparison is claimed.

## Artifact, source and checks

- [Current GLB](../../../models/testes/exports/z-native-epididymis-r01/testicular-region.glb):
  **220,184 bytes**, SHA-256
  `e35457062c7bba79d938700beab7de851c75fa8dbbbbc76872d47290f2833d0d`.
  Four meshes / **14,304 triangles**; static, no animation.
- [Source provenance](../../../sources/datasets/z-anatomy/testicular-region/provenance.json)
  and [attribution/license](../../../sources/datasets/z-anatomy/testicular-region/ATTRIBUTION.md):
  pinned Z-Anatomy CC BY-SA 4.0, with its required historical BodyParts3D
  CC BY-SA 2.1 Japan attribution. No per-object rights audit is implied.
- [Independent pixel review](independent-review.json): v1 rejected for faceted
  superior contour, doubled-side detail and obscuring/unvalidated duct routing.
  V2 uses source render subdivision 2, isolates one side for details and excludes
  both ductus deferens objects. Whole/detail/grayscale v2 passed within scope.
- [Exhaustive source/export check](source-export.json): four bijective position
  maps and oriented triangle sets match native render evaluation. Maximum error
  **6.01e-8 native units**, under the **2e-7** float32 export tolerance. All four
  meshes have zero boundary/nonmanifold edges, duplicate or zero-area triangles.
  This does not test all self-intersections or tissue-to-tissue interfaces.
- [Seven scoped checks](replay.json) passed: build, rebuild, byte equality,
  source/export mapping, wrong-source refusal, overwrite refusal and static
  four-object/failure-output checks. GLB replay is byte-identical.
- Historical delivery on 2026-10-30: direct LFS upload and fresh GitHub HTTPS
  size/hash readback passed. This is a past delivery result, not a current remote
  availability check. No Site or credential change was included.

## Scope and uncertainty

The source remains simplified smooth masses. This study does **not** establish
complete head/body/tail anatomy, efferent ducts, internal tubules, lumen, duct
continuity, tissue interfaces, scrotal layers, histology or anatomical dimensions.
Source bilateral labels are retained; the source appears mirrored and is not
evidence of individual variation. Native transforms are preserved, with no
whole-body registration. No specialist, clinical, motion or browser-runtime
approval is claimed. The original broader asset is not replaced or promoted.

The exclusion of deferens removes an unsupported default teaching relationship;
it is not a repair of the source junction. V1 source-context GLB identity remains
`1442a5d7f90bc301467e819e0467e01bafbac4c145e5131ffd832b8e3c3453a2`
(261,972 bytes). Its rejected output is retired; the initial recipe is preserved in commit
`e4c101bb9aaf17c9226ef4e4b49f95f94eb9f76a`. Only the current GLB is packaged.

## Replay

Use Blender **4.3.2**, Python 3 and the exact external `Startup.blend` specified
in provenance. No upstream scripts execute. The source-derived geometry and
renders retain CC BY-SA 4.0; reference figures are not reproduced.

```sh
python3 models/testes/recipes/replay.py --source /path/Startup.blend --out /tmp/testes-new-check
blender -b --factory-startup --python-exit-code 1 --threads 6 \
  --python models/testes/source/z-native-epididymis-r01/render.py -- \
  --artifact /tmp/testes-new-check/first/testicular-region.glb --out /tmp/testes-new-views
python3 tools/verify.py offline
```

The default builder emits four parts at native render detail. The diagnostic
`--surface-level 1 --include-deferens` flags retain the v1 geometry scope. PNG
metadata includes render time, so compare decoded pixels and camera receipts
when replaying images; do not expect identical PNG byte hashes. The initial
verifier failed because Blender mutated an assigned name list; copying that list
fixed the check. `--python-exit-code 1` is required so a script exception cannot
masquerade as process success.
