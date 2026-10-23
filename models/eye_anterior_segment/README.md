# Right anterior-segment layer study

**Static seven-component teaching study, not a complete eye or replacement for the failed whole-eye draft.**

- Source: HRA Eye Male Right v1.3, CC BY 4.0; native source frame.
- Exact source and selected candidate are included with Git LFS. Run `git lfs pull` first.
- POSITION/index/UV bytes and transforms retained. Materials are illustrative; only lens/cornea normals receive a guarded change. Corneal rim faceting remains.
- 16 source meshes excluded; no extraocular muscles/optic nerve in the source. Zonule insertion, optics, motion and anatomy completeness are not validated.
- Visual scope passed only for layer readability. Anatomy remains unreviewed; runtime unverified.

## Reproduce

From the repository root, with Python 3 and NumPy installed:

```sh
python tests/eye_anterior_segment/replay.py --output /tmp/eye-study-replay
python tests/review_records/validate_record.py --root . reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/record.json
```

The fresh output directory contains all four exact deterministic variants and preservation checks. Optional `--render` requires Blender 4.3.2 on PATH and produces offline Cycles views; render PNG hashes can vary by runtime and are not automatically visual passes. Hidden-layer views are inspection aids, not physical cutaways. The zonule isolation is diagnostic only.

The 3 WebP review images are lossy display derivatives; original PNG hashes and the 3 distinct comparison-artifact hashes are recorded. Native PNGs, broader diagnostic history and old BP3D failure evidence are deferred, not silently claimed as uploaded. Historical review paths describe the original package, not this smaller repository layout.
