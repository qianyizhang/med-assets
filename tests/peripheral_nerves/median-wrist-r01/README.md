# Median wrist/hand replay and checks

Python 3.11+, Pillow, Blender 4.3.2 with glTF I/O, DejaVu Sans and Noto Sans CJK
at the paths in `compose.py` are required. The exact source is external; use the
[pinned provenance](../../../sources/datasets/z-anatomy/median-wrist/provenance.json).
No source add-on or embedded script is executed. All output locations must be new.

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/median-wrist-r01/build.py -- \
  --source /path/to/verified/Startup.blend --out /tmp/median-wrist-new

blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/median-wrist-r01/check_source.py -- \
  --source /path/to/verified/Startup.blend \
  --glb /tmp/median-wrist-new/median-wrist-v1.glb \
  --sha256 6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50 \
  --out /tmp/median-source-check-new.json

python3 tests/peripheral_nerves/median-wrist-r01/test_package.py
python3 tools/verify.py offline
```

Expected GLB: **834,404 bytes**, SHA-256
`6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50`.
V2 is a teaching-composition change; final GLB bytes are identical to V1.
The six scoped tests are **separate from ordinary offline CI**. They check
actual payload/evidence bindings and deterministic composition as well as guards.
The source check compares all 33 evaluated vertex clouds, surface triangles and
effective world matrices. Its `1e-6` tolerance is for float32 export precision,
not anatomy. Read the receipt's result; Blender's default Python-exception exit
behavior is not a pass, so use `--python-exit-code 1`.

`render.py -- --glb FILE --sha256 HASH --out NEW_DIRECTORY` runs through Blender
with the same startup/exit flags. It captures full subset, palmar hand and oblique
wrist views from an exact clean GLB reimport. Camera, lights, sampling and hashes
are recorded. Current source uses the corrected visible scaphoid point.

The original V1 raw captures stay unchanged. `rebind_landmark.py` reproduces the
V2 annotation-only correction from that exact original binding file:

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/median-wrist-r01/rebind_landmark.py -- \
  --glb models/peripheral_nerves/exports/median-wrist-r01/right-median-wrist.glb \
  --captures reviews/peripheral_nerves/2026-10-30-median-wrist-r01/v1/renders \
  --out /tmp/median-captures-new

python3 tests/peripheral_nerves/median-wrist-r01/compose.py \
  --renders /tmp/median-captures-new --out /tmp/median-teaching-new
```

`check_locators.py -- --glb FILE --bindings FILE --out NEW_FILE` checks six
leaders against exact reimport vertices and the first visible source object.
An original scaphoid point was hidden by the trapezium; that failed screen and
composition are retained. The final point is visible in both labelled views.
Ray hits establish surface targeting, not semantic anatomy; independent image
review remains required. No geometry, rerouting, fusion or source-master edits.

No browser, animation, physical-scale, complete territory or tunnel validation.
The source soft-tissue relationship screen remains unresolved and excluded.
