# Lymph collecting routes — source-context reconstruction r01

For [issue #152](https://github.com/qianyizhang/med-assets/issues/152). New source-scene reconstruction, not recovery of the historical `99d19b3d15e4086e2f899b6376c4f2030e497c06` derivative. All delivered media are unchanged from reconstruction `fada107113ab77544cb965c346ea463ff653721d`.

![Original / Updated: matched overview and route detail](comparison-en.png)
![Original / Updated: 中文总览与路径近景](comparison-zh.png)

- **Change:** highlight the source-named thoracic duct and identify upper/lower source caps, against dimmed collecting scaffold.
- **Geometry:** 7 source objects, 372 triangles; preserved canonical world-space triangle multisets and unique positions at 1e-6 m after clean GLB reimport.
- **Presentation:** matched cameras/scale; Original shows all selected routes, Updated intentionally dims contextual routes. Editorial body silhouette is a locator, not validated fitted registration.
- **Limits:** source names do not establish anatomy. Caps are not verified venous junctions or continuous lumen. Other tissues omitted; detail crops peripheral routes, not selected endpoints. No physiological flow, anatomical/clinical approval, runtime or performance claim.

## Evidence and provenance

`build-receipt.json` records source selection, geometry and cameras. `geometry-verification.json`, `replay-verification.json` and `independent-review.json` are unchanged prior receipts. The independent reviewer inspected actual EN/中文 and grayscale images plus code/receipts; did not perform a second independent Blender replay. Builder's actual second replay matched final GLB/plate bytes and raw decoded RGBA pixels; raw PNG container hashes differed. This packaging step does not claim a fresh replay.

`source-identity.json` pins the commissioned source scene and archive. No CC or repository-wide license is inferred. Full scene/masters and raw render layers remain separate private recovery assets; not bundled. To supply source, extract the archive member named `Network_Systems_Draft.blend` from the pinned archive and verify its exact size/hash. Do not substitute a historical GLB or similarly named scene.

## Verify or explicitly replay

From this directory, Python 3.11+:

```sh
python3 verify_package.py
python3 replay.py --source /path/to/Network_Systems_Draft.blend --output /tmp/lymph-NEW --check-only
```

Preflight verifies package, exact source and a nonexistent output directory; it writes nothing. For an explicit full replay omit `--check-only`: Blender 4.3.2, Python Pillow and NotoSansCJK Regular/Bold at `/usr/share/fonts/opentype/noto/` are required. CPU Cycles, 32 samples, seed152, denoising off. Wrapper copies the packaged recipes and exact source into a new output directory, never modifies delivered files, and compares final GLB and bilingual/grayscale bytes. Keep mismatching output for review. Raw layers are regenerated only on explicit replay. No network or uploads.

Recipes preserve behavior; one trailing space was removed from build.py for diff hygiene (original SHA256 `63781b5961354d1293072d6ce61e1b7b31cf37d40a704465a147ac935b2068fc`). They retain obsolete helper naming/comment: `*-pads.png` denotes collecting scaffold, not adipose pads. The original cap markers derive from source vertex rings before reimport changes ordering.

Run repository `python3 tools/verify.py offline` separately. Offline gate does not hash hydrated media; this package validator does. This scoped family is not a foundation review record and is not automatically added to repository-wide payload checks. No new clinical, live viewer or publication approval follows from either check.
