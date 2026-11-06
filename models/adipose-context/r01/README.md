# Adipose region context — issue #151

New private source-scene reconstruction; not recovery of the unavailable historical derivative `1175f2d87fed6bed651840637910dc53b3b0a077`.

![Original / Updated — overview and matched detail](comparison-en.png)

[中文 comparison](comparison-zh.png). Takeaway: 4 unchanged authored pads gain a clearly illustrative body locator and abdominal/flank labels.

## Delivery and evidence
- Selected GLB: 49,724 bytes; 4 meshes, 1,760 triangles. No source/master replacement.
- Original commissioned geometry; no third-party CC license asserted. Source archive `Body_Atlas_Expansion_Blender_Sources_v9.zip`: 7,197,553 bytes, SHA256 `27fc64be3aebf7776e952fdf739b122fee3a26193656580502de158863fec9b0`.
- Separately retained source `Network_Systems_Draft.blend`: 10,587,644 bytes, SHA256 `5f7947838971b88f2c29e992290086e21169eee2c72bb5394948e72aee4bad25`. Not included here.
- [Geometry receipt](geometry-verification.json): canonical world triangle multisets and unique positions at 1e-6 m after clean reimport.
- [Independent prior visual review](independent-review.json): EN/中文 and grayscale pixels, with exact bindings. Grayscale/raw/source files remain in the original private reconstruction, not this minimal package.
- [Prior replay](replay-verification.json): exact GLB and final EN/中文 bytes reproduced; raw PNG byte identity not established.
- [Camera/source bindings](build-receipt.json). These inherited receipts describe the original reconstruction run, not a new packaging replay.

## Checks and optional replay
`python3 verify_package.py` checks pinned package bytes and every GLB primitive. It does not prove anatomy or rendering.

`python3 prepare_replay.py --source /path/Network_Systems_Draft.blend --output /new/output` validates source identity and creates a fresh replay folder. It does not invoke Blender. In that folder, with Blender 4.3.2, Python 3/Pillow and NotoSansCJK Regular/Bold TTC installed:

```sh
blender -b -t 4 --python build.py
python3 plate.py
blender -b -t 2 --python verify_geometry.py
```

CPU Cycles, 32 samples, no denoising. Keep the reviewed output unchanged. Compare new GLB/final plates against this package manifest; raw PNG containers are not promised byte-identical.

## Boundaries
Educational region-context study, not fitted skin, full adipose anatomy, volume/body-habitus measurement, clinical acceptance or live-runtime proof. No live browser, interaction or performance test. New private reconstruction identity `de0c9e73a515a61f8b6b446d94cfed8a1645e2bd` stays distinct from the missing old derivative. No public delivery authorized by creation of this package.
