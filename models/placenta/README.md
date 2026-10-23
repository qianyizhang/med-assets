# Full-term placenta: material-only teaching refinement

One HRA v1.1 source and exact r02 derivative. Eight named layers; no geometry or topology repair. The maternal basal and fetal chorionic surfaces are distinct. Full term only, not an inferred numerical gestational week. Colors, roughness and amnion transparency are illustrative—not measured tissue appearance, optical transmission, perfusion or exchange.

494 boundary /505 total non-two-incidence edges remain. Scoped static visual improvement was accepted from exact-export contacts; anatomy unreviewed and browser runtime unverified.

Source metadata/license: sources/datasets/hra/placenta-full-term-v1.1. Review/gates, two explicitly lossy WebP display images, original-render metadata and a lighting recipe are in reviews/placenta/2026-10-23-hra-v1.1-r02. Original lossless PNGs/native Blender scene are deferred, not silently replaced with display derivatives. Historical audit text is retained; earlier pending status is not the current scoped verdict.

## Reproduce without the native Blender scene

After git lfs pull, from repository root:

```sh
python tests/placenta/rebuild_material_variant.py --source sources/datasets/hra/placenta-full-term-v1.1/3d-vh-f-placenta-full-term.glb --output /tmp/placenta-rebuild.glb --audit /tmp/placenta-material-audit.json
python tests/review_records/validate_record.py --root . reviews/placenta/2026-10-23-hra-v1.1-r02/record.json
blender --background --factory-startup --disable-autoexec --python tests/placenta/render_exact_export.py -- --model models/placenta/exports/hra-v1.1-r02/placenta_full_term.glb --review reviews/placenta/2026-10-23-hra-v1.1-r02 --output /tmp/placenta-render-new
```

Outputs must be new paths; retained evidence is never overwritten. Material replay must reproduce exact accepted SHA. Render replay uses original cameras, named inspection visibility and lights extracted from the retained authored scene; it is not a promise of identical PNG bytes across platforms.

## Import verification, 2026-10-23

- Deterministic material replay reproduced accepted SHA `7f9f215f810003fddc76ede225f051dc7014c67216e804403a4632d628ad82aa`; BIN and non-material geometry/transform JSON unchanged. Independently repeated by a second reviewer.
- Fresh Blender 4.3.2 replay completed all 6 declared views; generated-image hashes checked. Recipe execution is not a new visual/anatomy/runtime approval.
- All four LFS payloads (9,991,596 bytes) independently downloaded from GitHub outside Actions at 08:54:38 UTC; SHA, size and file magic matched before pointers. Transport run: https://github.com/qianyizhang/med-assets/actions/runs/39927906059 . Compressed transport and decoded candidate hashes both verified.
- Local record/hash validation passed; no model-quality CI claim.
