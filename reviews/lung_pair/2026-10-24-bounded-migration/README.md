# Combined HRA female lung study · bounded migration

One existing scoped study, not two lung assets. Exact unchanged [GLB](../../../models/lung_pair/exports/hra-female-normals-r02/lung_female_hra_normals_r02.glb) plus three current selected WebPs. This migration adds no model count or quality gate. It is not a fresh anatomy review, runtime pass or portable rebuild.

## Scope and retained limitations

- Female HRA v1.3 lung/lobe pair with provider intrapulmonary branches. Only selected NORMAL bytes were changed in r02; source coordinates, topology, hierarchy, materials and frame remain unchanged. This local migration changes no media bytes.
- All 56 component meshes retain open annotation boundaries. Four additional right tertiary cartilage non-boundary non-manifold edges remain under the historical 0.1 µm diagnostic weld. This is not an exact-tuple topology proof or watertight model.
- Provider v1.3 removed larynx, trachea and main bronchi. No full airway, continuous lumen, tissue microanatomy, breathing transfer, CT/whole-body registration or clinical claim. Anatomy remains unreviewed; runtime remains unverified.

## Artifacts and evidence

- [Scoped record and concise failure lesson](record.json)
- [Combined provider geometry contact](display/8ee967465ea8ff3385988b11b55257dae93029e2ae961af2a2d17bf537ffb52c.webp)
- [Supplied intrapulmonary branches contact](display/1b3b3978041a989e522772c69d8e4fd3cbdd98807f0b60a9d6453da4c2f4ea4b.webp)
- [Original vs NORMAL-only comparison](display/f9dfe46b6a068bbaa867ab7ef4732c728ee6a3d630859af791dde33f96c1b8e4.webp)
- [Historical technical scope](historical-technical-scope.json) · [local byte comparison](local-byte-identity-check.json) · [camera/visibility recipe](camera-visibility.json)
- [Source/license map](../../../sources/datasets/hra/lung-female-v1.3/bounded-migration-2026-10-24/external-source-map.json) · [CC BY 4.0 attribution](../../../sources/datasets/hra/lung-female-v1.3/bounded-migration-2026-10-24/ATTRIBUTION.md) · [dependency boundary](../../../sources/datasets/hra/lung-female-v1.3/bounded-migration-2026-10-24/dependency-manifest.json)

The comparison has two source bindings and is not a single tested mesh. Its existing association warning is retained. The original source GLB is external, not bundled. WebP display hashes and native PNG hashes are distinct; native PNGs and nonselected historical views are external references. Camera recipes retain native glTF metres/+Y; they are not browser-executed proof.

## Identity checks

From the repository root:

```sh
python tests/hra_lung/verify_bounded.py
# Optional: exact isolated-draft file closure, not for a populated repository
python tests/hra_lung/verify_bounded.py --strict-package
```

Default verifies only [declared files](FILE-HASHES.json); unrelated repository content is allowed. [File list](FILE-LIST.md), [transport manifest](transport-manifest.json) and [verification report](verification-report.json) define the migration boundary. Existing public gzip/WebP URLs are preserved without a fresh availability/readback claim. Source metadata/license are retained records, not a new provider fetch.

**简要教训：** 拼片法线会造成假性明暗条带。先区分几何缺口、材质反光和法线伪影；只协调同肺叶保守范围内的法线，不能据此声称补全气道、呼吸或临床解剖。
