# FDI 31 Balanced educational LOD and focus viewer

Related: [#120](https://github.com/qianyizhang/med-assets/issues/120). This is a bounded review record, not clinical acceptance or canonical promotion. [Public review preview](https://dental-fdi31-focus-review-oct28.landy123007.chatgpt.site/fdi31/) is Site v3, source `b6d5ed873aacd1f39e65e1f0645d4e78108b1faf`; this repository does not deploy or replace it.

## Artifact and visual disposition

Balanced is a separate teaching-resolution draft: 105,370 triangles, 2,052,220 GLB bytes, SHA-256 `90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7`; deterministic-gzip file 888,210 bytes, SHA-256 `182fd3b511e77598bf081a631c3c332ac8a7c14c165212d1d8c2a3a2c037a877`. Four named source labels retain their shared specimen frame. The retained detailed candidate (1,328,980 triangles, 26,524,356 bytes; SHA-256 `c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014`) and master are unchanged. Neither model is included in this PR.

[Matched overview and detail](matched-overview-detail.jpg) is a compressed copy of an existing offline Blender CPU comparison, not a viewer screenshot. It shows the detailed baseline and three drafts with matched camera, scale and lighting, including a 12 mm detail field; the original PNG SHA-256 is `54aea4ae4b60c94397dac69fcd37936beb3fe58d6b74e46c6a5e661d88332448`. Balanced preserves recognizable teaching-scale form and layer relationships while smoothing fine tooth surfaces and coarsening bone. The user accepted the Balanced offline appearance; this is not proof of global non-overlap, clinical accuracy or runtime behavior. Source segmentation islands, open/nonmanifold interfaces and boundary truncation remain. Roughly 1% of overall size is a guide, not a certified error bound.

Source: Benz, Heck & Walter (2024), *Data: Visualization of Pulpal Structures by SWIR in Endodontic Access Preparation*, [DOI 10.5282/ubm/data.477](https://doi.org/10.5282/ubm/data.477), CC BY-SA 4.0. Derivative changes: per-tissue mesh simplification and visible smoothing; source labels and frame retained. Prepared T2 specimen, not a healthy reference or validated complete root canal.

## Reproduction recipe

The original build script and material helper are preserved under `recipe/` in their expected relative layout. Provide the four **unbundled** derived PLY inputs as `recipe/dental-interface-repair-20261027/replay/derived/A_1_31_T2_SEG_na__{enamel,dentin,pulp,bone}.ply`, then from the repository root run:

```sh
python3 reviews/swirendo_fdi31/2026-10-28-balanced-focus/recipe/dental-teaching-lod-20261028/scripts/build_lod.py --preset balanced
```

Requires compatible NumPy, trimesh and PyMeshLab; exact build versions were not locked, so byte-identical output is not promised. Verify input and output hashes before comparing. The script selects each largest face-connected component for QEM (target counts enamel 14,000, dentin 25,000, pulp 5,000, bone 40,000); small components are retained, simplification is in millimetres and export returns to metres. The QEM filter requests topology, boundary and normal preservation; these settings do not certify that the result is manifold or free of defects. It uses no exact-interface collar. Gzip uses level 9 and `mtime=0`. The script writes to `recipe/dental-teaching-lod-20261028/drafts/balanced/` and **overwrites files there**; use a clean copy or back up prior outputs. It does not write the master.

| Input layer | SHA-256 |
| --- | --- |
| enamel | `2cf89de6126c036e3fa82409fcd7e80d67ec7861c099e6022c4e69f95699df0b` |
| dentin | `e4d21b55e18a0c7dc4ddbc47a24722286f2b52329ef4460b17d5969e1fabf2ce` |
| pulp | `ffa544da258a4a25b2500cd34c0da24324789b0126af647896eec4f87fa0294e` |
| bone | `8155937f04903bac86e97db9309248e56c86e41b57e235b9493979ffbef72677` |

## Viewer source and verification

`viewer-source/` retains the exact v3 FDI31 page, styles, controller, model contract, manifest and focused tests. It is a source subset, **not a standalone deployment**: the existing Site supplies its Three.js vendor modules, review images and exact model files at the root-relative paths in the page and manifest. Do not silently replace those assets; identities are checked by the controller. A host must supply the declared dependencies before running it. Quality selection loads only the selected file; selection and camera are intended to persist across quality changes, while restore resets context and view.

At exact Site source `b6d5ed873aacd1f39e65e1f0645d4e78108b1faf`, `node --experimental-vm-modules --test tests/fdi31-quality/*.test.mjs` passed 14 scoped tests under Node 24.22.1 with the actual Site dependencies and model bytes. These include actual GLTFLoader parsing, hash and node binding, and synthetic controller/renderer checks for lazy selection, races, failure/retry, reset and context lifecycle; they are not live 3D tests. Signed-out browser checks observed default selection, idle quality/language changes and the detailed-attributed fallback image. No 3D-open action was made in that v3 check. The retained fallback is **Detailed**, not Balanced.

Cloud WebGL was disabled, so Balanced render, pointer/touch controls, actual quality switching, orbit/zoom/reset in 3D and measured performance remain **unverified**. The user authorized unavailable runtime testing not to automatically block this bounded PR or authorized merge; that is not a runtime pass. Follow up on a WebGL-capable authorized device and record its browser/device and findings. No clinical validation, full geometry audit, payload transport, Site change or LFS publication is implied. Issues #95, #96 / PR #109, #97 and paused #99 remain independent and unchanged.
