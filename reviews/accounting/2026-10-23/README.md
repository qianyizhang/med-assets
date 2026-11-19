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
- **Credits** · Source-specific notices stay with the originals. Segmented s1233 surfaces use [TotalSegmentator v2.0.1](https://zenodo.org/records/10047263), CC BY 4.0, with the separate Apache 2.0 label notice retained.

```sh
python3 tools/patch_scene_metadata.py --patch "$approved_patch" "$baseline_glb" "$fresh_output"
python3 tests/review_records/validate_record.py "$review_record"
```
