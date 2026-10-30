# Reproduce this bounded study

Use Linux, Blender **4.3.2**, Python **3.12**, Pillow, and the DejaVu/Noto CJK
fonts named in `compose.py`. The pinned `Startup.blend` source is retained
separately; [provenance](../../../sources/datasets/z-anatomy/sciatic-hip/provenance.json)
gives its exact identity and source/license links. No source script or add-on runs.
Every output directory/file must be new.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/sciatic-hip-r01/build.py -- \
  --source /path/to/Startup.blend --out /tmp/sciatic-new-build

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/sciatic-hip-r01/check_source.py -- \
  --source /path/to/Startup.blend \
  --glb /tmp/sciatic-new-build/right-sciatic-hip.glb \
  --sha256 72077a97a8a935a7a4623443c1c0fd61ab48a9bf4ad895af058345b7a372abd6 \
  --out /tmp/sciatic-new-check.json

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tests/peripheral_nerves/sciatic-hip-r01/render.py -- \
  --glb /tmp/sciatic-new-build/right-sciatic-hip.glb \
  --sha256 72077a97a8a935a7a4623443c1c0fd61ab48a9bf4ad895af058345b7a372abd6 \
  --out /tmp/sciatic-new-renders

python3 tests/peripheral_nerves/sciatic-hip-r01/compose.py \
  --renders /tmp/sciatic-new-renders --out /tmp/sciatic-new-teaching
python3 tests/peripheral_nerves/sciatic-hip-r01/test_package.py
python3 tools/verify.py offline
```

The five scoped tests are separate from ordinary offline CI. They inspect the
actual GLB and evidence bytes, source/output guards and deterministic composition.
The Blender check compares all stored source surfaces; it separately allows only
the exact documented importer omission. Read its result, not process status alone.

Compactness: one canonical GLB, one source binding, one raw capture set reused by
V2, one source-check summary. No full per-vertex dump or duplicate GLB. Preflight
images retain the rejected soft-tissue lesson and its native comparison.
