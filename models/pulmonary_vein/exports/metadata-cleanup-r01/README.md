# pulmonary vein — metadata-only alternative

Corrected scene metadata for this existing baseline geometry; **0 new approved studies**. Original baseline is retained. This recommendation concerns metadata correctness only, not visual quality and not preference over other separately reviewed models.

- Static export with no animation clips.
- Retained source-derived s1233 display; any teaching sections/routes remain authored, not segmented anatomy.
- Only reviewed scene extras change. Geometry, materials, transforms, source-node attribution, BIN and actual animation data remain identical.
- Prior visual status: **unreviewed**, not upgraded. Anatomy **unreviewed**; browser/runtime **unverified**.
- Source/license notices remain in the original asset and repository. For segmented surfaces see TotalSegmentator v2.0.1 (https://zenodo.org/records/10047263); CC BY 4.0 source attribution and retained Apache 2.0 label notice are preserved. No author endorsement or clinical claim.

## Exact replay

From repository root, with the original baseline LFS file already fetched:

```sh
python tests/scene_metadata/pulmonary_vein/patch_metadata.py ORIGINAL_BASELINE.glb /tmp/pulmonary_vein-metadata-replay.glb
python tests/review_records/validate_record.py reviews/pulmonary_vein/2026-10-23-metadata-cleanup-r01/record.json
```

`approved-patch.json` pins the input SHA/size and every old/new field value. Output must not exist. Python standard library only. Verification record describes exact checks; native offline comparison images are deferred, not represented as included. No browser or PR CI claim.
