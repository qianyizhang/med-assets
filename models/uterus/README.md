# Uterus exterior-only study

HRA Female Uterus v1.1 derivative: two overlapping anterior/posterior wall solids are omitted. The preserved original source is available alongside the derivative.

- Retained exterior patches keep source frame and materials. No cavity is created.
- No full tubes, ovaries, complete reproductive system, clinical or runtime claim.
- Visual acceptance is exterior-only; anatomy reference-screened, not complete; runtime unverified.
- Original annotated patches can remain open.

## Reproduce

After `git lfs pull`, with Blender 4.3.2 on PATH:

```sh
python tests/uterus/replay.py --output /tmp/uterus-exterior-replay
python tests/review_records/validate_record.py --root . reviews/uterus/2026-10-23-hra-v1.1-r02/record.json
```

The output must be new. Replay rebuilds the exact export, renders 7 offline views, checks every retained world-coordinate set rounded to 0.1 micrometre and triangle counts, and records exact-coordinate edge incidence. This is not byte-identical coordinate comparison or an automatic anatomy/runtime pass.

The 2 WebPs are lossy display derivatives. The contact retains its historical UNREVIEWED header; later personal review accepted only the documented static exterior scope on 2026-10-23. Original pixels are not rewritten. Native PNGs/scenes and broader failures remain deferred, not claimed as uploaded.
