# Blood-cell form study — authored teaching model

- Exact reviewed GLB: `exports/authored-r05/blood-cell-authored-study-r05.glb`.
- Editable, path-sanitized baked source: `source/blood-cell-authored-study-r05-public.blend`.
- Closed biconcave RBCs; connected contained neutrophil nucleus; labeled intact/cutaway; illustrative platelets. Arbitrary display units, not microscopy reconstruction or measured biology.
- Static teaching readability only. Reference screening is qualitative; anatomy/clinical validation and browser runtime are not established. Historical `draft_blood` remains unchanged and failed.

## Reproduce the stored export

Use Blender 4.3.2, from the repository root:

```sh
python tests/blood_cell_study/replay.py --output /tmp/blood-baked.glb
```

This reopens the baked editable source and checks the exact reviewed GLB SHA. It does **not** rebuild the historical remesh recipe. One retained procedural rebuild matched geometry/shading but not bytes; a fresh procedural run failed strict geometry equivalence on 4 meshes. Its cause is unestablished. The historical recipes and failure summary are retained for learning, not advertised as deterministic.

## Evidence and rights

See `reviews/blood_cell_study/authored-r05/record.json` and `source/PROVENANCE.md`. Four public WebP display derivatives are included; native PNG history is deferred. The CDC comparison explicitly identifies the lower neutrophil and arrowhead lymphocyte (not modeled). Only separately credited public-domain reference pixels are included; restricted reference images are excluded. No new license is assigned to the authored model.
