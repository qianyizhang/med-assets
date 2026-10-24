# Aortic subset, auricles and parotid pair — bounded migration draft

Exactly **3 unchanged GLBs + 8 selected current presentation WebPs**, **11 unique media objects / 2,954,416 bytes**. No new model, quality, build, camera, anatomy, clinical or runtime claim; **zero count/gate changes**. All paths below are repository-root relative. No root README or root file manifest is introduced.

## Scope preserved
- **Aorta:** 15 source structures in 9 exterior meshes; open rims and unfused branch surfaces remain. Not complete circulation, closed volume or continuous lumen.
- **Ears:** auricle/pinna exterior only; 36 source regions, historical seam weld/interpolation, medial cut/open boundaries retained. No canal, tympanum, middle/inner ear or watertightness claim.
- **Parotids:** bilateral outer envelopes only; no ducts, deep lobes or complete salivary-system replacement. Mandible in contact evidence is context, not part of this GLB.

Only two baseline images are selected: vessel baseline and ear baseline have different original GLB bindings. Parotid has no selected baseline. Do not rebind a baseline to an accepted candidate, treat contact context as exported coverage, or substitute original PNG hashes for WebP display hashes.

## Source/license and dependency boundary
`sources/datasets/z-anatomy/small-static-studies/dependency-manifest.json` records one shared commit-pinned external archive and Startup.blend member with exact hashes, selected source names and unbundled replay dependencies. The archive, source OBJ/BLEND/intermediates and build/render code are not copied. This is **not** full rebuild closure. All geometry remains Z-native and unregistered to BP3D/CT. The current public map reports no complete numeric camera contract for these studies; no camera reconstruction is claimed.

Geometry and derived candidate renders retain **CC BY-SA 4.0**, with historic BodyParts3D attribution. See the shared attribution and upstream license. Existing baseline/source bindings remain distinct.

## Evidence/transport
`selected-public-map.json` retains the exact selected identities, roles, bindings, scope and gates from the stored public map. `transport-manifest.json` distinguishes existing gzip endpoint bytes from decoded GLB bytes; all three rawCandidate entries are null. Stored local gzip objects were hash-checked and decoded against the canonical GLBs. Initial package preparation was local-only. The subsequently approved reusable transport verified all sources and independently downloaded all 11 GitHub LFS objects at 2026-10-24 09:03:41 UTC; see `transport-receipt.json`. This is transport identity, not a new anatomy, runtime or reconstruction pass.

`presentation-notes.json` records preservation of exact already-public historical evidence. Image wording refers to prior scoped visual review, not new validation; pixels remain unchanged. Final file list and bounded scope were reviewed before transport; unchanged model/evidence identities are retained.

## Local verification only
Run `python tests/z_small_studies/verify_bounded.py`. Default mode verifies only files declared in this review's `FILE-HASHES.json`, so unrelated repository files do not fail the check. Use `--strict-package` only for isolated-package exact-file closure. Hash manifest excludes itself. Neither mode downloads, rebuilds, renders, updates gates/counts or establishes clinical/runtime validity.
