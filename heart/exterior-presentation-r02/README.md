# Static opaque heart exterior r02

The recommended static exterior in the local Anatomy Gallery is [`exports/static-opaque-exterior-repacked.glb`](exports/static-opaque-exterior-repacked.glb). The lossless repack retains the 124 selectable exterior objects of the Workshop derivative and saves 5,543,680 bytes (61.93%). The [review](../../reviews/heart_exterior/2026-11-21-static-repack/README.md) records clean reimport, exact decoded geometry and materials, and identical pixels at both matched views.

| Export | Bytes | SHA-256 |
| --- | ---: | --- |
| [Original static r01](../exterior-presentation-r01/exports/static-opaque-exterior.glb) | 8,951,936 | `595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f` |
| Static r02 | 3,408,256 | `221c8be48c44f49ebbc4a52b2ce4094a5c4b15ea1be01db39038ac8a8f4a52b5` |

## Local recovery

Use `git lfs checkout heart/exterior-presentation-r02/exports/static-opaque-exterior-repacked.glb` to hydrate a pointer from the local Git LFS store. If the object is absent, follow the [r01 recipe](../exterior-presentation-r01/README.md#static-repack-candidate) with a fresh output path. Verify the result against the r02 identity above. With the working path absent or containing its unchanged Git LFS pointer, copy the verified GLB to `exports/static-opaque-exterior-repacked.glb` in this package. The read-only Gallery preview checks the bytes at request time. **Retry 3D** loads the restored file.

## Scope and delivery

The model depicts the project-authored analytic Cardiac Atlas. The [r01 attribution and limits](../exterior-presentation-r01/README.md#attribution-and-limits) still apply. Vessel joins, surface gaps and internal anatomy have the same presentation limits. The r01 static delivery, repository-source animation and unavailable fitted animation retain their own identities and Gallery records.

The r02 route is local-only. Public delivery requires publication of the exact Git LFS object, authorized R2 upload and verification, and a Gallery release with public route and browser readback. [AG-GAL-020](../../records/work-items/items/AG-GAL-020-adopt-static-heart-repack.md)
