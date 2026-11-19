# Baseline review accounting · 23 October 2026

| Ledger | Outcome and limits |
| --- | --- |
| [Original baselines](baseline-decisions.json) | 62 initial decisions: 26 failed, 27 need revision, 7 need review, 2 scoped visual passes. The 28 later visual decisions bind original GLB identities and public URLs to 32 unmodified native inspection PNGs. Four source-limited cases remain needs-review. |
| [Metadata equivalence](metadata-equivalence.json) | 16 derivatives with commit-pinned paths and verified LFS pointers. Visual status inherits only the linked scope supported by unchanged BIN and non-metadata JSON. No fresh derivative-pixel or pixel-identity claim. |
| Independent scope | The separate 35 scoped studies do not change original-baseline counts. Historical reviews retain their own dates, evidence and limits. Anatomy, clinical use and intended-consumer runtime require separate review. |

## Metadata-only replay

- **Outcome** · Corrected scene extras. Original baseline, geometry, materials, transforms, source-node attribution, BIN and animation data retained. No new study approval or browser/hosted CI claim.
- **Inputs** · Exact original GLB bytes and the asset's approved patch. Python standard library and a fresh output path.
- **Acceptance** · Patcher verifies pinned source/target hash and size and reviewed old/new values. Record validator checks the bound evidence. Current visual scope comes from the linked review, with deferred native comparisons identified there.
- **Display** · Motion, source-derived and authored scope live in the individual patch and review. Bladder, brain and bronchial tree are authored schematics. Teaching sections and routes in source-derived displays are authored where present.
- **Credits** · Source-specific notices stay with the originals. Segmented s1233 surfaces use [TotalSegmentator v2.0.1](https://zenodo.org/records/10047263), CC BY 4.0, with the separate Apache 2.0 label notice retained.

```sh
python3 tools/patch_scene_metadata.py --patch "$approved_patch" "$baseline_glb" "$fresh_output"
python3 tests/review_records/validate_record.py "$review_record"
```

### Patches and reviews

| Export | Approved changes | Exact review |
| --- | --- | --- |
| [aorta](../../../models/aorta/exports/metadata-cleanup-r01/) | [Patch](../../../models/aorta/recipes/metadata/approved-patch.json) | [Review](../../aorta/2026-10-23-metadata-cleanup-r01/record.json) |
| [bladder](../../../models/bladder/exports/metadata-cleanup-r01/) | [Patch](../../../models/bladder/recipes/metadata/approved-patch.json) | [Review](../../bladder/2026-10-23-metadata-cleanup-r01/record.json) |
| [brain](../../../models/brain/exports/metadata-cleanup-r01/) | [Patch](../../../models/brain/recipes/metadata/approved-patch.json) | [Review](../../brain/2026-10-23-metadata-cleanup-r01/record.json) |
| [bronchial_tree](../../../models/bronchial_tree/exports/metadata-cleanup-r01/) | [Patch](../../../models/bronchial_tree/recipes/metadata/approved-patch.json) | [Review](../../bronchial_tree/2026-10-23-metadata-cleanup-r01/record.json) |
| [gallbladder](../../../models/gallbladder/exports/metadata-cleanup-r01/) | [Patch](../../../models/gallbladder/recipes/metadata/approved-patch.json) | [Review](../../gallbladder/2026-10-23-metadata-cleanup-r01/record.json) |
| [kidney_left](../../../models/kidney_left/exports/metadata-cleanup-r01/) | [Patch](../../../models/kidney_left/recipes/metadata/approved-patch.json) | [Review](../../kidney_left/2026-10-23-metadata-cleanup-r01/record.json) |
| [kidney_right](../../../models/kidney_right/exports/metadata-cleanup-r01/) | [Patch](../../../models/kidney_right/recipes/metadata/approved-patch.json) | [Review](../../kidney_right/2026-10-23-metadata-cleanup-r01/record.json) |
| [liver](../../../models/liver/exports/metadata-cleanup-r01/) | [Patch](../../../models/liver/recipes/metadata/approved-patch.json) | [Review](../../liver/2026-10-23-metadata-cleanup-r01/record.json) |
| [lung_left](../../../models/lung_left/exports/metadata-cleanup-r01/) | [Patch](../../../models/lung_left/recipes/metadata/approved-patch.json) | [Review](../../lung_left/2026-10-23-metadata-cleanup-r01/record.json) |
| [lung_right](../../../models/lung_right/exports/metadata-cleanup-r01/) | [Patch](../../../models/lung_right/recipes/metadata/approved-patch.json) | [Review](../../lung_right/2026-10-23-metadata-cleanup-r01/record.json) |
| [pancreas](../../../models/pancreas/exports/metadata-cleanup-r01/) | [Patch](../../../models/pancreas/recipes/metadata/approved-patch.json) | [Review](../../pancreas/2026-10-23-metadata-cleanup-r01/record.json) |
| [pulmonary_vein](../../../models/pulmonary_vein/exports/metadata-cleanup-r01/) | [Patch](../../../models/pulmonary_vein/recipes/metadata/approved-patch.json) | [Review](../../pulmonary_vein/2026-10-23-metadata-cleanup-r01/record.json) |
| [spleen](../../../models/spleen/exports/metadata-cleanup-r01/) | [Patch](../../../models/spleen/recipes/metadata/approved-patch.json) | [Review](../../spleen/2026-10-23-metadata-cleanup-r01/record.json) |
| [stomach](../../../models/stomach/exports/metadata-cleanup-r01/) | [Patch](../../../models/stomach/recipes/metadata/approved-patch.json) | [Review](../../stomach/2026-10-23-metadata-cleanup-r01/record.json) |
| [trachea](../../../models/trachea/exports/metadata-cleanup-r01/) | [Patch](../../../models/trachea/recipes/metadata/approved-patch.json) | [Review](../../trachea/2026-10-23-metadata-cleanup-r01/record.json) |
