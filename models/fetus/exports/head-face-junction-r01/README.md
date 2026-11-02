# Head–face junction · bounded authored study

Related: [#194](https://github.com/qianyizhang/med-assets/issues/194).

- **Original:** a separate face ellipsoid forms a raised mask-like edge.
- **Updated:** blend only its overlap with the head. Preserve pose/proportions,
  nose/eyelids and all 22 unrelated meshes. No developmental-age claim.
- **Scope:** exact authored, non-age-calibrated fetal inset; not a scan or healthy
  fetal-anatomy reference. Existing simplified limbs, body and cord are unchanged.

## Reproduce with the exact original

Python 3 stdlib; no network or package installation. Original source URL/hash and
candidate identity are in [the review](../../../../reviews/fetus/2026-11-02-head-face-junction-r01/review.json).
Source GLB and output media are **not included**. Obtain bytes only through an
authorized route; scripts reject the wrong source and never overwrite outputs.

```sh
python3 models/fetus/exports/head-face-junction-r01/build.py \
  --source /path/to/exact-original.glb --output /new/path/candidate.glb
python3 models/fetus/exports/head-face-junction-r01/check.py \
  --source /path/to/exact-original.glb --candidate /new/path/candidate.glb
blender -b -t 2 --python models/fetus/exports/head-face-junction-r01/reimport.py -- \
  --source /path/to/exact-original.glb --candidate /new/path/candidate.glb \
  --output /new/path/reimport-check
blender -b -t 4 --python models/fetus/exports/head-face-junction-r01/render.py -- \
  --source /path/to/exact-original.glb --candidate /new/path/candidate.glb \
  --output /new/path/matched-views
```

Blender 4.3.2 was used. Render all exports after clean reimport, with identical
camera/light/exposure settings per Original / Updated pair. The script writes
Front/Left/Back whole views and Front/Left detail. Cycles CPU, 24 samples;
optional denoising was unavailable and disabled for both variants.

## Evidence and costs

- Exact-byte deterministic replay verified locally; candidate SHA in review.
- 13 decoded technical checks; 22 unrelated reimported mesh/normal/matrix identities
  exact. Nose/eyelid nodes and original BIN bytes remain unchanged.
- Independent actual-pixel review accepted the bounded transition; no geometry v2.
- 720 sampled projected-support directions per plane: maximum outline differences
  0.0751 mm Front/Back, 0.1054 mm Left, 0.1132 mm Superior. New tessellation is **not**
  exact head-vertex identity. This is a geometric screen, not anatomical tolerance.
- 292,140 → 454,980 B; 12,248 → 18,248 active triangles. Two replaced mesh payloads
  remain inactive in the appended GLB to preserve all original bytes. No measured
  browser performance claim; optimization is not silently substituted.
- Ordinary offline CI runs 4 payload-free refusal tests. It does **not** replay the
  original GLB, render images, or establish anatomy/runtime acceptance.

## Retention and limits

Keep the original GLB, source/native masters, candidate, failed scripts and matched
images distinct. This text package contains only deterministic recipe, scoped QA
and compact evidence identities. Original source archive, new GLB, PNGs and Blender
scene remain private; publication and Site integration are separate decisions.
No clinical, gestational-stage, anatomical completeness or live WebGL pass.
