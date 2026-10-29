# Focused trachea r06 checks

These scripts use Blender 4.3.2 and existing local GLBs. They make no network
requests and do not fetch or publish media. Use `--python-exit-code 1`; Blender's
ordinary exit status alone can conceal a script failure. New output paths are required.
Run from the repository root after the [build](../../models/trachea/exports/open-airway-r06/README.md).

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tests/trachea_open_airway/check_geometry.py -- \
  --candidate /tmp/trachea-r06-new/trachea-open.glb \
  --out /tmp/trachea-r06-new/open-geometry.json
blender --background --factory-startup --python-exit-code 1 \
  --python tests/trachea_open_airway/check_geometry.py -- \
  --candidate /tmp/trachea-r06-new/trachea-cutaway.glb \
  --out /tmp/trachea-r06-new/cutaway-geometry.json
blender --background --factory-startup --python-exit-code 1 \
  --python tests/trachea_open_airway/check_lumen.py -- \
  --baseline models/trachea/exports/host-conforming-cbands-r05/trachea_host_conforming_illustration.glb \
  --candidate /tmp/trachea-r06-new/trachea-open.glb \
  --record /tmp/trachea-r06-new/build-record.json \
  --out /tmp/trachea-r06-new/lumen-check.json
```

Geometry checks reimport the actual export, weld UV/float seams within 1e-8 m,
check edge incidence, degenerate faces and signed volume, then screen nonadjacent
shell triangles using BVH candidates and a separating-axis test with 1e-10 m gap
tolerance. Shared-vertex triangle pairs are excluded. Band/shell overlap is intentional;
this is not exhaustive all-object intersection proof or an anatomical tolerance.

The lumen check samples a 1.2 mm grid with 0.15 mm wall clearance inside the source
cast, constrains it to the cut planes and tests neighboring steps against shell
triangles. It checks whether all three opening seeds connect. It does not establish
flow, normal lumen caliber or exhaustive absence of isolated voids. The retained V6
result has 10,484 connected samples out of 10,487; all three openings connect.

For the final V7, the V6 lumen/detail evidence was reused only after
`bind_reuse.py` established exact decoded shell attributes, indices and node
transforms. V7 changes only the band caps. That helper needs both retained versions;
a new reproduction can run the lumen check directly as above. Do not relabel V6
PNGs as V7.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tests/trachea_open_airway/render.py -- \
  --baseline models/trachea/exports/host-conforming-cbands-r05/trachea_host_conforming_illustration.glb \
  --candidate-dir /tmp/trachea-r06-new --out /tmp/trachea-r06-renders-new
blender --background --factory-startup --python-exit-code 1 \
  --python tests/trachea_open_airway/project.py -- \
  --baseline models/trachea/exports/host-conforming-cbands-r05/trachea_host_conforming_illustration.glb \
  --candidate-dir /tmp/trachea-r06-new --out /tmp/trachea-r06-svg-new
python3 tools/verify.py offline
```

`render.py` uses clean reimports, matched cameras/scale, AgX and fixed lighting,
900×1000 pixels, Cycles 32 samples. `--views whole,proximal` and `--current-only`
select affected views for an iteration. PNG byte identity is not guaranteed by a
repeat render; GLB replay identity is recorded separately.

`project.py` creates illustrative SVG triangle projections from the same exports.
They are not screenshots or Cycles renders; simplified visibility and flat shading
cannot replace actual-pixel review. Both scripts emit camera and SHA256 bindings.
The ordinary offline gate covers repository integrity, not these media checks,
clinical validation or the supported browser viewer.
