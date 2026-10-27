# L3 — metadata-only refinement

**Same existing L3 asset; 0 new approved candidates.** The original baseline file stays unchanged. This named alternative corrects stale cardiac scene metadata, not anatomy or geometry.

- Output: `exports/metadata-cleanup-r01/vertebrae_L3.glb` (2,034,520 bytes).
- Source: existing repository `body/anatomy-workshop-r1/meshes/vertebrae_L3.glb`; exact input SHA is pinned in the patch.
- Only 7 scene-extra fields change. BIN, other JSON, geometry, transforms and materials remain identical.
- Visual scope: previously reviewed gross static L3 exterior. Fine anatomy remains **unreviewed**; browser/runtime **unverified**. Retained s1233 segmentation, repair and smoothing limitations still apply.
- No default whole-body replacement, spine-completeness, animation, cutaway or clinical claim.

## Replay from repository root

```sh
python tools/patch_scene_metadata.py --patch tests/vertebrae_L3_metadata/approved-patch.json body/anatomy-workshop-r1/meshes/vertebrae_L3.glb /tmp/L3-metadata-replay.glb
python tests/review_records/validate_record.py reviews/vertebrae_L3/2026-10-23-metadata-cleanup-r01/record.json
```

Python standard library only; output must not already exist. Fetch the existing LFS source normally before replay. The script refuses unexpected source/output hashes, changed binary chunks or changes outside scene extras.

The retained independent offline comparison found **0 changed RGBA pixels** in front and superior views. PNG hashes differ because render metadata differs. The report and exact image hashes are included; native PNGs and editable inspection scene are deferred, not silently substituted with other renders. These are offline tests, not browser QA or CI claims.

See the dated review record for concise failure/cause/fix/retest/lesson and source notices for attribution.
