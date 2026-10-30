# Pulmonary vein: same-case context

An additive EN/中文 teaching presentation compares the retained left-sided
pulmonary-vein component alone and beside the source case's heart and five lung
lobes. A posterior overview locates a matched detail view. The largest-component
limit is visible on the presentation; no named branch, restored component or
lumen continuity is inferred.

[Open the reviewed teaching sheet](pulmonary-vein-context.png). The left column
shows the original retained component; the right adds same-case context. Both
columns use matched overview and detail cameras.

This addresses the pulmonary-vein coverage/context row of issue #150. It uses
the old source-case heart only as anatomical context, independently of the
authored-heart work. Gallbladder teaching and the diaphragm preflight are outside
this change. Original masters, source JSONs and history are untouched.

## Inputs and scope

The exact retained GLB is
`models/pulmonary_vein/exports/metadata-cleanup-r01/pulmonary_vein.glb`,
SHA256 `9e0454c0a920bcd9292d1aced370ff781b97aa8fb87b0439eb1f0ac21517a593`.
The same-case JSONs are retained under
`body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy/`.
All inputs are hash-pinned in the generator. Source case is s1233, tb3 revision
`75ec4e6530abe4d434b07958e90bdc9dec062bef`.

Source coordinates remain RAS millimetres. The retained builder's shared mapping
is `(-R/1000, -(A-155)/1000, (S-430)/1000)` into Blender metres; glTF positions
map to Blender as `(x, -z, y)`. No independent fitting, vertex smoothing,
joining or reconstruction is performed. Display copies preserve every decoded
position and triangle. Smooth display shading and illustrative materials are
render choices, not tissue properties. Context appears translucent and does not
change illumination of the selected component.

The extraction receipt records four source-mask components and retains only the
largest (3,953 voxels). The original mask is unavailable in this checkout;
that count is not a fresh recomputation and the other components are not named
as missing veins. Context meshes are coarse and original intersections remain.
Posterior patient left is screen left, checked against source coordinates and
the named left/right lung meshes.

## Build the local presentation

Requirements: Blender 4.3.2, Python 3.11+, Pillow, Inkscape 1.4 and Noto Sans CJK
SC for editable SVG text. Rendered PNGs are portable. Use a checkout containing
the exact hydrated GLB; a Git LFS pointer fails closed. Commands create local
outputs only and require new output directories.

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/pulmonary_vein_context/render.py -- \
  --root . --output /tmp/pulmonary-context-renders
python3 tools/pulmonary_vein_context/build.py --root . \
  --renders /tmp/pulmonary-context-renders --output /tmp/pulmonary-context-teaching
inkscape /tmp/pulmonary-context-teaching/pulmonary-vein-context.svg \
  --export-type=png --export-filename=/tmp/pulmonary-context-teaching/pulmonary-vein-context.png
inkscape /tmp/pulmonary-context-teaching/overview-comparison.svg \
  --export-type=png --export-filename=/tmp/pulmonary-context-teaching/overview-comparison.png
inkscape /tmp/pulmonary-context-teaching/detail-comparison.svg \
  --export-type=png --export-filename=/tmp/pulmonary-context-teaching/detail-comparison.png
python3 tools/pulmonary_vein_context/check_visuals.py --root . \
  --renders /tmp/pulmonary-context-renders --output /tmp/pulmonary-context-teaching
python3 -m unittest discover -s tests -p 'test_pulmonary_vein_context.py' -v
```

The output contains a combined teaching sheet and separate Original/Updated
overview/detail comparisons. Original means a new matched render of the retained
component, not a historical screenshot replay. SVGs embed the bound render bytes;
composition is deterministic for those bytes. Blender version, lighting,
materials, camera matrices, source geometry hashes and output hashes are recorded.
Cross-version bit-identical rendering is not claimed.

The visual-binding check verifies every embedded image and all native exported
pixels outside the editorial side labels and detail locator. This presentation
does not export a new GLB. Source-coordinate/face checks and SVG-to-PNG binding
checks support the static presentation only; browser, anatomy and clinical gates
remain separate.

For the camera-only v1 → v2 revision, append
`--reuse-detail-from /path/to/exact-v1-renders` to the Blender command. This
accepts only the recorded v1 receipt and its exact detail PNGs; it renders the
overview pair and copies the unchanged detail pair. Lighting, materials and
source inputs remain identical. The overview's projected context margin is
recorded on every side; a 24 px minimum prevents the v1 near-edge framing.
V2 has 68.93 px minimum margin at the native 900×700 resolution.

## Attribution

Jakob Wasserthal and the TotalSegmentator contributors, University Hospital
Basel, [TotalSegmentator v2.0.1](https://zenodo.org/records/10047263).
Retain [CC BY 4.0 and source notice](../../body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy/NOTICE.md)
and the [label-source Apache-2.0 notice](../../body/anatomy-workshop-r1/docs/licenses/TotalSegmentator-v2.0.1-LICENSE.txt).
The change adds editorial display materials, same-case visibility comparisons
and bilingual typography. No source author endorsement is implied.

The v1/v2 technical and independent static review is recorded in
[the review record](../../reviews/pulmonary_vein/2026-10-30-context/README.md).
