# Skeletal-context teaching supplements

Two bounded views of existing BodyParts3D source geometry, **0 new accepted models**. Historical `draft_cartilage` remains **Needs revision**.

- Second costal cartilage with selected ribs, sternum and T1/T2.
- L3–L4 exterior disc with both vertebrae. Not annulus/nucleus, facet contact, biomechanics or full cartilage coverage.
- Static teaching readability only. Coarse seams remain; anatomy unreviewed, runtime unverified. Diagnostic colors are not tissue colors. Keep context structures visible.

## Source dependency (not included or automatically fetched)

`source/dependencies.json` declares the official **64,888,505-byte** ZIP, SHA-256 and exactly **12 OBJ members / 2,431,724 raw bytes** with hashes and identities. The URL includes LATEST, so verify the pinned hash and stop if it differs. No source archive/OBJ payload is part of this PR.

The optional narrow adapter verifies delivered exports against those exact sources. The original broad wrapper needed 71 OBJ files and 2 metadata files; it is not falsely described as a 12-input recipe. Geometry-preserving roundtrip passed; fresh generated GLB byte identity is not assumed.

```sh
blender --background --threads 4 --python tests/skeletal_teaching/build_wrapper_narrow.py -- --source-root /path/to/content-addressed-obj --dependency-map assemblies/skeletal-teaching/source/dependencies.json --output-root /tmp/skeletal-check --verify-exports assemblies/skeletal-teaching/2026-10-23 --skip-renders
```

BodyParts3D © The Database Center for Life Science, CC Attribution 4.0 International under the current official notice: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html . Unchanged source OBJ headers retain their historical CC BY-SA 2.1 Japan notice. Source coordinates are preserved, with uniform mm→m and export-axis conversion only; no unrelated-atlas registration.

See `reviews/skeletal_teaching/2026-10-23/record.json` for exact evidence, labels, limits and failed-marker lesson. Eight WebPs are display derivatives, not byte-identical native PNGs. Reference links only; no external textbook images included.
