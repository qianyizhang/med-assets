# Rebuild and verify

Tested dependencies: Blender4.3.2 with bundled NumPy; Python3/Pillow; Noto Sans CJK Regular at `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`. Native CPU renders, not browser QA. Source archive is external, reusable and pinned in source provenance.json. Extract only Startup.blend; do not open the full atlas scene or enable automatic scripts.

Set `$SOURCE` to hash-verified Startup.blend, `$CONFIG` to a writable Blender config directory, and all output variables to NEW paths. Blender commands use `--python-exit-code 1` so script failures propagate.

```sh
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build.py -- --source "$SOURCE" --out "$BUILD"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify.py -- --source "$SOURCE" --build "$BUILD" --out "$CHECK"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render.py -- --build "$BUILD" --out "$RENDERS"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_baseline.py -- --baseline "$BASELINE" --out "$BASELINE_RENDERS"
python compose.py --renders "$RENDERS" --baseline-renders "$BASELINE_RENDERS" --out "$COMPARISON.png"
python annotate.py --renders "$RENDERS" --out "$ANNOTATED.png"
```

The diagnostic-only path deliberately rebuilds the REJECTED source duct course so the failure remains inspectable. Never use its outputs as the default teaching asset:

```sh
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build.py -- --source "$SOURCE" --out "$REJECTED_BUILD" --diagnostic-original
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify_failure.py -- --source "$SOURCE" --out "$FAILURE_CHECK"
BLENDER_USER_CONFIG="$CONFIG" blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_failure.py -- --diagnostic-context "$REJECTED_BUILD/context.glb" --out "$FAILURE_RENDERS"
python compose_failure.py --renders "$FAILURE_RENDERS" --out "$REJECTION.png"
```

Default build emits `glands-ducts.glb` (only parotid ducts) and `context.glb`; canonical copies are named `glands-and-parotid-ducts.glb` and `same-source-context.glb`. Bytes are identical. Source hash and model hashes are guarded; output paths must be new. Compositors guard exact model binding IDs, not environment-dependent PNG metadata.

Baseline source SHA865717807c724b375f25fdc745e231525730ed80a374042a1e4f89cf32b8b4b6:
https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/assets/drafts/head/salivary-glands.glb

Approximate tested shared-CPU times: build15–45s, source check15–45s,6native views1–3min,3failure views1–2min. Diagnostic transparency is explicitly a display technique, not transparent tissue or a physical cut. No silent geometry repair or complete clinical/anatomy proof.
