# Optional tongue p11 recipe — external source required

This is a small **additive recipe/dependency audit**, not a self-contained model package or a claim of fresh full-pipeline regeneration. It does not replace the reviewed asset or its historical failures.

## Verified here

- New portable extraction script was run against the immutable public HRA raw source and reproduced the historical five-patch subset **byte for byte**: 16,647,708 bytes, SHA-256 `a76dc3c882994ff1515f30f9047872a634a6cdf9275e1eec7b4aa9ba13633d12`. Binary `cmp` against the frozen subset passed.
- The historical material-only intermediate digest was verified by streaming its serialization into SHA-256; no 103 MB intermediate copy was written.
- Nine required construction/check scripts were copied unchanged from the frozen handoff, syntax-parsed, and audited for file dependencies. Shell syntax was checked. Exact script hashes are in `receipts/script-audit.json`.
- **Not executed here:** the full raw→authored p11 chain, new renders, anatomy review or runtime testing. The separately retained prior receipt establishes only the already recorded p08→p11 final-step replay.

## External source, licensing and target

Provide HRA Mouth Female v1.0, Heidi Schlehlein / HRA-HuBMAP, **CC BY 4.0**:
- [Versioned raw GLB](https://cdn.humanatlas.io/digital-objects/ref-organ/mouth-female/v1.0/assets/3d-vh-f-mouth.glb)
- [Release](https://lod.humanatlas.io/ref-organ/mouth-female/v1.0) · [DOI](https://doi.org/10.48539/HBM856.VZWZ.422)
- 103,690,760 bytes; SHA-256 `bd8e24e9d52b49719c6a1cafa1f54fc40c1d3f811b9d32df78d5c20ebb78c197`.

No raw source, baked NPZ, candidate GLB or image is copied into this recipe package. License text is included. Source and generated subset exceed the 10 MB evidence-package budget; they are explicit external/generated dependencies, not silently omitted prerequisites.

Expected reviewed target: 4,983,044 bytes; SHA-256 `efabd58b235b72682f067113cf079e3f70fbaceac47062f2b937f09540c1ee1a`.

The target is an **AUTHORED educational gross-exterior tongue hybrid**, not a source-exact whole mesh or patient/clinical model. Static visual review is recorded separately; no internal musculature, floor/frenulum attachment, vessels, motion or runtime claim is added. Source-exact triangle positions coexist with authored lower body, seam and tip transitions. The original HRA cup study remains unpromoted; whole-mouth failure remains open.

## Optional clean reconstruction

Use a **new output directory** and the pinned toolchain in `receipts/toolchain.json` (Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, Matplotlib). No network request is made by the wrapper. Blender is unnecessary for this geometry-only recipe; the original Blender reviews are not rerun.

```bash
bash tests/tongue_authored_study/optional_recipe/scripts/rebuild_optional.sh /absolute/path/3d-vh-f-mouth.glb /absolute/path/new-tongue-run
```

The wrapper refuses an existing output directory, copies only the small recipe scripts into that fresh workspace, generates all NPZ prerequisites from the raw source, runs the construction/check chain, and stops if the final GLB digest differs from the frozen candidate. A digest mismatch must not be relabeled a successful replay. Expect at least 100 MB of generated working files beyond the external raw source; allow additional headroom. The run is optional and was **not launched during this audit**.

The historic scripts intentionally retain their serialized prototype metadata so an exact-byte reproduction remains possible. Separate review documentation, not a metadata rewrite, records the later static visual decision.

## Dependency closure and size boundary

`DEPENDENCIES.json` lists exact observed sizes/hashes and producers. The active chain is:

1. `extract_hra_tongue.py` → historical five-patch GLB.
2. `inspect_source.py`, `analyze_upper_patch.py` → source analysis NPZ.
3. `select_exterior_p07.py` → `excluded_components_p07.py` → `restore_enclosed_source_p07.py` → `trim_upper_join_p07.py` → selected source exterior NPZ.
4. `export_prototype_p08.py` → authored p08 geometry, provenance NPZ and build JSON.
5. `refine_tip_p11.py` → final p11 geometry/provenance; `verify_candidate_p11.py` checks against the generated source analysis.

There is **no mandatory pre-existing private NPZ input** in this inspected chain. p01–p06 and p09/p10 rejected tongue prototypes are not needed to execute it; their history remains preserved elsewhere.

A final-step-only bootstrap would instead require three baked files: p08 GLB 4,980,852 bytes + p08 provenance NPZ 2,881,008 bytes + p08 build JSON 2,077 bytes = **7,863,937 bytes**. Their public download availability is not guaranteed and they are **not packaged**. Adding the accepted p11 GLB would total 12,846,981 bytes before images/scripts, above the 10 MB cap. The raw-source recipe avoids that hidden bootstrap dependency; it does not make the whole package self-contained.
