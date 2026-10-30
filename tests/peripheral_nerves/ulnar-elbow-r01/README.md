# Reproduce the regional study

Requirements: Python 3.11+, Pillow, Blender 4.3.2 with glTF I/O, DejaVu Sans and
Noto Sans CJK fonts at the paths in `compose.py`. No source add-on is installed
or executed. Use `--factory-startup --disable-autoexec`. Obtain the exact external
Startup.blend using the [pinned source record](../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json).
Outputs must be new; existing files/directories are refused.

From repository root:

```sh
blender --background --factory-startup --disable-autoexec \
  --python tests/peripheral_nerves/ulnar-elbow-r01/extract_source.py -- \
  --source /path/to/verified/Startup.blend --out /tmp/ulnar-source-new

python3 tests/peripheral_nerves/ulnar-elbow-r01/build.py \
  --input reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v1/native-elbow.glb \
  --output /tmp/right-ulnar-elbow-new.glb

python3 tests/peripheral_nerves/ulnar-elbow-r01/test_build.py
python3 tests/peripheral_nerves/ulnar-elbow-r01/verify_package.py
python3 tools/verify.py offline
```

Source replay must produce v1 SHA-256
`206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5`.
Presentation replay must produce v2 SHA-256
`94a7bde3f8a2882cc632082301d7701a737a769e1d1afe0f55629ecac3013ac3`.
The six scoped tests check exact replay, source/output guards, retained geometry
and transforms, and explicit identity/limitations. They are **not selected by
the ordinary offline suite** and must be invoked separately.

To render either exact GLB, call `render.py` through Blender with
`-- --glb FILE --sha256 HASH --out NEW_DIRECTORY`. The camera/light contract is
fixed in the script and recorded in each output's `bindings.json`. Both matched
sets use 128 samples, denoising off. Existing initial 24-sample v1 views are
historical diagnostics, not the matched comparison inputs. The local Blender
build lacks OpenImageDenoise, so the unsuccessful denoiser attempt was replaced
with higher sampling for both variants.

`compose.py --review REVIEW_DIRECTORY` requires v1 renders under
`v1/matched-128` and v2 renders under `v2/raw-128`, then creates a new `evidence`
directory. Keep old evidence before rerunning. Numeric leaders bind source mesh
vertices; independent actual-pixel review must judge semantic target placement.
The provider's named graphical landmark endpoints identify the starting regions;
projection alone does not prove anatomical identity or visible-surface selection.

`verify_package.py` hashes actual payloads, checks matched conditions and all
six locator bindings, and confirms exact raw pixels in the comparison panels.
It does not inspect pixels, establish anatomy, verify remote delivery or run a
browser. The broader offline gate checks the repository's documented text/pointer
scope; it does not imply this package's geometry or runtime acceptance.
