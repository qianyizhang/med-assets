# Prostate reference zones and accessory structures

Unchanged HRA Prostate Male v1.1 source, retained once as the model. The URL uses HRA release v1.2; that is not a new organ version.

- Static teaching scope only; zones and accessory structures are source references.
- Separate gray bladder appears only in context evidence; it is not in the prostate GLB.
- Open annotated patches remain. No continuous lumen, full system, motion or clinical claim.
- Visual scope passed; anatomy reference-screened only; runtime unverified.

## Reproduce

Run `git lfs pull`, then with Blender 4.3.2 on PATH:

```sh
python tests/prostate/replay.py --output /tmp/prostate-source-replay
python tests/review_records/validate_record.py --root . reviews/prostate/2026-10-23-hra-v1.1/record.json
```

Replay checks both original hashes, imports the exact source in its native frame, renders original layers and separate context, and runs an exact-coordinate edge audit. Output must be new; historical evidence is never overwritten. Fresh rendering is not an automatic visual or runtime pass. Layer hiding is an inspection aid, not a modeled cut surface.

The 2 WebP images are lossy display derivatives, not original lossless pixels. Original PNG hashes and context binding are explicit. Native PNGs/scenes and earlier failed prototypes remain deferred. Full metadata and CC BY 4.0 attribution are retained.
