# Bladder / pancreas context replay adapter

Small migration draft only. It reconstructs **two existing exports**, not new anatomy or a new pass:

| Candidate | Accepted SHA-256 |
|---|---|
| `bladder_hra_female_context_r03` | `91f04d1c831a61944da116184f389461517587c90c91fd94e199fba1619aa6b9` |
| `pancreas_hra_female_context_r04` | `aa15f9248027c248886a9cf8d4f5f401b2753176c800851f648b03d88d97ebed` |

## Required external inputs

1. Original HRA united-female v1.10 GLB: **374,505,632 bytes**, SHA-256 `95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422`. Supply an existing file. It is not packaged, copied or downloaded.
2. Existing repository `tests/liver_spleen/recipes/` directory, containing the hash-pinned `extract_exact_subsets.py` and `resolve_shared_source.py`. **This adapter is not self-contained without those two dependencies.** Their exact paths, sizes and hashes are in `dependency-map.json`; `remote-dependency-verification.json` independently confirms their bytes at remote main commit `79c867bad7471562d1c4ddabb4fe2a24d9764f8a`; no other liver/spleen recipe is executed.
3. Python 3 and NumPy already available. Tested with CPython 3.12.14 / NumPy 2.3.5. No installation or Blender is performed. Different numerical environments must still satisfy the final exact-hash checks.

```sh
python3 -B path/to/bladder-pancreas-recipe-staging/replay.py \
  --source /existing/path/3d-vh-f-united.glb \
  --shared-recipes /existing/repo/tests/liver_spleen/recipes \
  --output /new/nonexistent/replay-directory
```

Run without `-O`. The output directory must not exist. The wrapper checks external source and recipe hashes, copies only small script/data files into the new work directory, and creates a symlink to the original atlas. It writes fresh subsets, intermediate/final GLBs, derivation audits and `replay-verification.json` there (about 19 MB in the local test). The original atlas is rehashed after completion. No canonical path or accepted export is modified.

## Reconstruction boundary

- Exact atlas source geometry, accessor payloads and hierarchy → compact named subsets.
- Explicit source node ID **and** source name → reviewed illustrative role/color. Every one of the 21 bladder and 20 pancreas context mesh roles is checked, not fuzzy-matched.
- Bladder: reproduce the existing dome/base-only boundary normal update; neck, trigone, orifices and all context geometry/normals stay untouched.
- Pancreas: reproduce the existing 35° angle-weighted normal trial with dimensionless sliver guard, protected original zeros, slivers/degenerates and crease-separated multifans. Transfer by exact source name/POSITION/NORMAL identity into the context.
- Final hashes must equal both accepted bytes. Accepted GLBs, archived per-vertex normal arrays, render history or large audit archives are **not** build inputs.
- Direct final roles replace the historical wrong fuzzy-role intermediate. In particular, the duodenal ampulla and sphincter are assigned **duodenum** context from the outset; the material ordering and final bytes remain exact. The old failure history is retained separately, not erased or repackaged here.
- The pancreas standalone intermediate is computational/diagnostic only, not a third accepted candidate.

`replay-verification.json` records the successful fresh local reconstruction. No fresh images were rendered: exact-byte identity refers back to the existing reviewer-inspected static visual evidence. Full original source metadata/licenses, frame contracts, failures, detailed audit history and contact sheets remain in the frozen visceral handoff and canonical imported records. This small adapter neither transports nor replaces that evidence archive.

## Preserved limitations

Native source frame is unchanged: no centering, scale, mirroring, registration, POSITION/index/topology changes or invented anatomy. Female teaching context is not a default whole-body or sex-neutral replacement.

Source open annotation/region patches, zero/nonunit normals and technical warnings remain. Bladder source ridge remains and **fill state is unknown**; selected context is not complete pelvis/urinary anatomy. Pancreas retains 101 ill-conditioned triangles, 8 degenerate faces, 222 protected sliver-associated normal indices, 20 original zero/near-zero normals and 8 virtual nonmanifold edges. Two multifan indices are preserved; 47 sound >35° crease edges are not crossed. Duct meshes are selected source context, **not proven continuity/patency/flow**. Illustrative colors and double-sided display do not imply measured tissue colors or wall thickness.

No new visual, anatomical, clinical, normality, microscopic, flow, complete-system, clean-format or browser-runtime approval is granted.

**Failure lessons / 失败教训:** Explicit node maps prevent similarly named context parts from getting the wrong role. Exact byte reproduction is not anatomical validation. / 使用明确节点映射，避免相似名称导致组织角色误配；字节完全复现不等于解剖学验证。 Preserve sliver/zero-normal warnings rather than silently normalizing them. / 保留薄片三角形与零法线警告，不应静默“修复”。

## Attribution

Kristen Browne and Heidi Schlehlein (2026), *3D Reference Organ Set for Female, v1.10*. DOI: https://doi.org/10.48539/HBM637.DWBM.744 . Source and derivatives: **CC BY 4.0**, https://creativecommons.org/licenses/by/4.0/ . Original asset: https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/v1.10/assets/3d-vh-f-united.glb . The locally authored replay describes the existing source subset, illustrative materials and bounded NORMAL-only derivatives; it is not a provider-endorsed anatomy correction.

Transport is not performed by this draft. `transport-manifest.json` inventories the text payload; source and shared recipe dependencies remain external.
