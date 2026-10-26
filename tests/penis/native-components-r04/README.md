# Local replay

Dependencies tested: Blender4.3.2 (bundled NumPy), Python3 + Pillow, Noto Sans CJK Regular at `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` for labels. No source add-on or automatic scripts. The large external source archive is not embedded; exact pinned URLs/hashes are in source provenance.json. Extract only `Startup.blend` (SHA9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd). Reuse an existing hash-verified source copy.

Run with a writable Blender config directory; do not open the full source scene:

```sh
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build.py -- --source "$SOURCE" --out "$NEW_BUILD"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify_export.py -- --source "$SOURCE" --candidate "$NEW_BUILD/source_components.glb" --out "$NEW_CHECK"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render.py -- --candidate "$NEW_BUILD/source_components.glb" --out "$NEW_RENDERS"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_baseline.py -- --baseline "$BASELINE" --out "$NEW_BASELINE_RENDERS"
python compose.py --renders "$NEW_RENDERS" --baseline-renders "$NEW_BASELINE_RENDERS" --out "$NEW_COMPARISON.png"
python annotate.py --renders "$NEW_RENDERS" --out "$NEW_CONTEXT.png"
```

All output paths must be new. Build/verify/render input hashes are guarded. Compositors check exact model binding IDs, not path-dependent PNG container metadata. Set variables to your local paths; scripts contain no private workspace dependency. Build/export ~15–40s, verification ~10–30s,5views ~1–2min on tested shared CPU; load varies.

Baseline SHA8bf7e4b3e66731df07a3167b1a18b033280e1195f76a9ff3205249b5c16f926a:
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/assets/drafts/pelvis/penis.glb

Actual build byte equality and decoded image replay results are recorded separately. These are native Blender render checks, not browser visual/runtime QA. No claim of clinical validation or exhaustive self-intersection analysis.
