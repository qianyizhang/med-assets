# Reuse the dental editorial placement

The source sets are **not naturally aligned**. A one-time offline fit placed them
in the native BodyParts3D frame for comparison. This small replay applies those
fixed matrices; it does not rerun registration or infer anatomy for new meshes.

## Run

Python 3.11+, standard library only. Obtain the exact original GLB payloads through
an authorized source first; Git LFS pointers are not meshes. From the repository:

```sh
python3 tools/dental/replay_alignment.py fdi31 \
  models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb \
  /tmp/FDI31-editorial-aligned.glb
python3 tools/dental/replay_alignment.py support35-37 \
  models/dental-root-support/v3/molar-support-v3.glb \
  /tmp/molar-support-editorial-aligned.glb
python3 tools/dental/replay_alignment.py pdl35-37 \
  models/dental-root-support/v3/synthetic-pdl-v3.glb \
  /tmp/pdl-editorial-aligned.glb
```

Outputs must be new paths. The script checks input and output SHA-256, adds one
common scene-root matrix, and leaves all existing nodes and binary chunks intact.
An input change or an already-aligned input is rejected. No downloads, automatic repository
changes, per-part repositioning, deformation or camera changes occur.

## What was fitted

- **Target:** unchanged BP3D exteriors, SHA-256
  `82bfaeead46bb51b1fa5bdfdb06c918dfd01aa23b28acae733ab75ec2cd6897f`.
  FDI31/FJ1258, 35/FJ1257, 36/FJ1254, 37/FJ1256.
- **Method:** area-weighted surface sampling; proper rotation, translation and
  uniform scale; symmetric 92%-trimmed nearest-point fitting. FDI31 used multiple
  principal-axis starts with crownward-direction screening. Support paired each
  tooth only to its matching FDI exterior; PDL and bone did not drive the fit.
- **FDI31:** scale 1.19850159; four tissues move together. Sampled RMS 0.670 mm,
  P95 1.471 mm. Alternatives were nearly tied (next RMS 0.683 mm), so buccolingual
  correspondence is unresolved. Enamel/dentin samples include internal interfaces.
- **35–37:** scale 1.05216040; teeth, PDL and bone use one identical matrix. RMS by
  tooth: 0.662 / 0.929 / 0.786 mm. These are different-source shape residuals,
  not clinical registration accuracy. Native inter-tissue positions are preserved.
- **UFF:** no alignment preset. Tooth identity, laterality and anatomical
  orientation are unknown. Keep it in a separate shot/specimen view.

The [pinned manifest](../../tools/dental/editorial-alignment-20261103.json) is the
reusable transform and input/output identity record. New source geometry needs a
new, explicitly reviewed fit, not a changed hash to bypass this check.

## Cross-set video

Load the unchanged BP3D GLB plus the selected aligned output in one scene. Retain
their transforms and use one camera path, projection and scale while changing
visibility. Do not auto-center or fit-to-view each model independently: that would
undo the common frame and cause scale/position jumps. When combining support and
PDL, show their duplicate cortical/alveolar bone only once; the meshes match.

Matrices are row-major in JSON, act on column vectors, and are converted to GLTF
column-major storage. Coordinates are GLTF right-handed **Y-up metres**, in the
original BP3D world frame (around Y=1.45 m, not near zero). Blender's GLTF importer
maps `[x,y,z]` to `[x,-z,y]`; do not apply a second axis correction after import.
A camera-friendly origin shift, if needed, must be common to the atlas and every
aligned group. This replay does not provide animation or validate a video runtime.

Use “provisional editorial comparison” in the shot. The placement does not make a
shared patient, validate tissues against atlas gingiva, repair BP3D tooth contacts,
or establish occlusion. Prepared FDI31 and synthetic nominal 0.25 mm PDL retain
their original limitations. No clinical or anatomical registration approval.

## Provenance and checks

Source attribution remains per package: [BP3D](../../models/teeth_gums/exports/r02/ATTRIBUTION.md),
[SWIRendo, CC BY-SA 4.0](../../models/swirendo_fdi31/exports/balanced-20261028/README.md),
and [synthetic support, CC BY 4.0](../../models/dental-root-support/v3/README.md).
The replay adds editorial placement only; the SWIRendo derivative retains its
share-alike license. No mesh copies or new visual revisions are committed here.

```sh
python3 -m unittest discover -s tests -p test_dental_alignment_replay.py
python3 tools/verify.py offline
```

Actual-payload replay was also compared to all three reviewed aligned GLBs on
2026-11-03: every output SHA-256 and binary payload matched exactly. This proves
replay fidelity, not a new anatomy, rendering, video or WebGL pass.
