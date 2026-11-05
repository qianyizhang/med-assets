# Reproduce central focal fairing

Dependencies actually available for this run: Blender 4.3.2 with bundled NumPy; standalone Python 3 with NumPy/SciPy for exported mapping. PNG comparisons use Pillow. These dependencies are not vendored. No install/network operation is performed by scripts.

Input (external, not duplicated):
https://media.githubusercontent.com/media/qianyizhang/med-assets/52b9e7f6973036e5b69e2fc9814ef892d3d07fbe/models/bronchial_tree/exports/authored-lobar-fairing-r09/bronchial_lobar_fairing.glb

Input SHA256: `8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4`.
Expected candidate SHA256: `c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587`.

Run from any directory, substituting actual script/input/output paths:

```sh
blender -b --python-exit-code 1 --python refine.py -- --input R09.glb --out NEW_REPLAY_DIRECTORY
python check_invariants.py --work NEW_REPLAY_DIRECTORY
python check_export.py R09.glb NEW_REPLAY_DIRECTORY/candidate.glb NEW_REPLAY_DIRECTORY/vertex-invariants.npz
python check_sections.py --source R09.glb --candidate NEW_REPLAY_DIRECTORY/candidate.glb --output NEW_SECTION_JSON
blender -b --python-exit-code 1 --python render.py -- --source R09.glb --candidate NEW_REPLAY_DIRECTORY/candidate.glb --output NEW_RENDER_DIRECTORY
```

Refine/render hash-check inputs before requiring a fresh output directory; section verifier requires a fresh output file. Do not use existing output paths. `--python-exit-code 1` propagates Blender Python exceptions. Generated vertex arrays are transient verifier inputs, not a second deliverable model.

GLB serialization can reorder vertices and indices. `check_export.py` checks a unique coordinate bijection and oriented faces, not raw-index identity. Positive face normal dot and manifold tests do not exhaustively prove absence of all self-intersections. `check_sections.py` excludes aperture-open cuts; valid sampled solid sections are not lumen validation or an everywhere caliber bound.

Exact replay statements and tested guards are in the review receipt. Render wrapper uses identical saved camera/light settings and imports the exact GLBs; any actual wrapper replay status is recorded separately, not presumed from static inspection.
