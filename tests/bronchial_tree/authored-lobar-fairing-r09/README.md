# Reproduce scoped local fairing

Blender4.3.2 (bundled NumPy), no network or external geometry library. Obtain the exact r07 source GLB from commit7797d3f1aa29585e9e93a663dceb727dda380079, models/bronchial_tree/exports/authored-junction-repair-r07/bronchial_authored_junction_repair.glb. SHA3408ca8e8f394dd268b1dbeafdc59fdc8cc104c0976628e455dbc070ae0a7993.

`blender -b --python-exit-code 1 --python refine.py -- --input <EXACT_R07_GLB> --out <NEW_DIRECTORY>`

Hash validated before output directory creation; existing output rejected. Generates candidate.glb, geometry-qa.json and vertex-invariants.npz (transient verification arrays, not extra geometry). Source external to avoid duplicate11MB baseline. No claim of installed dependencies on other machines. Rendering proof uses matched Inkscape-free Blender Cycles scenes, not browser runtime. Independent mapped checker additionally requires NumPy/SciPy.

Optional local checks: `blender -b --python-exit-code 1 --python check_local.py -- --source <R07> --work <REPLAY_DIRECTORY>`. Export mapping: `python check_export.py <R07> <REPLAY_DIRECTORY/candidate.glb> <REPLAY_DIRECTORY/vertex-invariants.npz>` (NumPy/SciPy). Exact matched render: `blender -b --python-exit-code 1 --python render.py -- --source <R07> --candidate <R09> --output <NEW_RENDER_DIRECTORY>`. Render guards both GLB hashes; no existing directory overwrite. Support-mask PNG separately visualizes baseline selected faces (not altered material in deliverable).
