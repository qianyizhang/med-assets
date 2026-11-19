# HRA female kidney pair replay

- **Outcome** · Exact left and right matte-reference exports from the pinned HRA female v1.3 kidney sources.
- **Inputs** · Hydrated GLBs under `sources/datasets/hra/kidney-female-*-v1.3/`, Python and a fresh output directory. Run without Python `-O`.
- **Acceptance** · Exact source/export hashes, unchanged BIN, reversible original JSON and preservation of the left source's two collapsed triangles. Optional Blender 4.3.2 `--render` produces diagnostic views.
- **Limits** · Native HRA frame. Static visual acceptance for exterior and isolated pyramids/source-labeled tips. Capsule-only is diagnostic. Columns + medulla overlap is rejected for teaching. Open annotation surfaces remain. Pelvis, calyces, ureter and vessels are absent. Anatomy unreviewed, runtime unverified.
- **Evidence** · [Left review](../../../reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/record.json) · [Right review](../../../reviews/kidney_right/2026-10-23-hra-female-v1.3-r02/record.json). Retained WebPs are lossy derivatives. Full native renders/scenes, raw-mask trials and rejected overlap history remain deferred.

```sh
python3 assemblies/kidney-pair/recipes/replay.py --output "$fresh_output"
```
