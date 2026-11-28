# Wave 2B aorta builder receipt

Three exports in [Aorta ultrasound-r01](../../../../../models/aorta/README.md) passed the frozen raw-label gates. The abdominal and screening crops replace the same axial display extents used by the previous standalone sweeps. The crop above each scan window is a display boundary. The full exterior preserves the source-labeled arch and distal end. The [independent review](../README.md) adopts the two display ports for their separate orientation tasks.

| Surface | Triangles · previous → r01 | Raw 3D p95 / max | Largest protected cut | Volume | 24-view silhouette |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full source label | 5,986 | 0.42 / 1.71 mm | 1.72 mm | +0.11% | 1.00 px |
| Abdominal crop | 18,320 → 5,790 | 0.42 / 1.09 mm | 1.25 mm | +0.20% | 0.50 px |
| Screening crop | 12,892 → 4,990 | 0.42 / 1.09 mm | 1.07 mm | +0.21% | 0.50 px |

The source label and both crops each have a single foreground component and zero enclosed gaps. The largest full exterior error lies on the upper thoracic limb. The full candidate initially had four degenerate faces after three positions coincided in float32 packing. Welding those positions retained one outward shell and removed the degeneracy and six nonincident intersections. All three final meshes have Euler 2 and zero open, misoriented, nonmanifold, degenerate or intersecting faces. The two cap locations agree with the frozen cut planes to under 0.05 mm.

[Previous and candidate crops](../../../../../experiments/ultrasound-sweep/development/asset-reviews/aorta-wave-2b/previous-vs-r01.webp) · [Raw label and matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/aorta-wave-2b/matched-surfaces.webp) · [Protected contours and crop rims](../../../../../experiments/ultrasound-sweep/development/asset-reviews/aorta-wave-2b/protected-planes.webp) · [Chrome frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/aorta-wave-2b/live-frame-12.webp) · [Checks and exact bytes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/aorta-wave-2b/measurements.json)

## Replay the checks

The [frozen packet](frozen.json) pins the baseline Wave 2A delivery after pancreas r02, under ignored `.artifacts/us-pancreas-r02/{stage,final}`. It checks the compact index's deduplicated mesh bytes against the stage, the saved poses and scan images, and the raw half-label contours. The abdominal crop opens the frame-12 long axis alongside the cava. The screening crop protects frames 12, 30 and 48 with adjacent cuts. AAA-negative uses a separate modeled wall and lumen with registered calipers. Its existing modeled acquisition is the appropriate baseline for that task.

Use the package Replay twice and compare all three outputs with `cmp`. The hydrated mesh identities matched both clean replays. All three exports have the Git LFS filter. Check each export with the same reference and its own dense geometry, and run the displaced copy with `--distort`. Each 6 mm displacement exited 1.

```sh
packet=records/campaigns/ultrasound-refinement/wave-2b/aorta
work=.artifacts/us-wave2b/aorta
base=.artifacts/us-pancreas-r02
export PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}"
python3.12 "$packet/freeze.py" "$S1233_CASE" "$base" "$work/reference"
for name in aorta aorta-abdomen aorta-screening; do
  python3.12 "$packet/measure.py" "$name" "$work/reference/$name-reference.npz" \
    "$work/replay-a/$name.mesh" "$work/replay-a/$name-dense.npz" "$work/replay-a/$name.json"
done
```

The [Chrome capture](player.mjs) starts a loopback server and a disposable Chrome profile, verifies the prior and candidate frame-12 mesh and image response hashes, and captures both oblique and axial views. It swaps the one candidate mesh on each baseline sweep for the matched comparison. The lead verifies the assembled chapter and sweep routes separately. The [clay render](render_clay.py) and [witness layout](witnesses.py) use the frozen reference and the decoded prior and candidate mesh coordinates.

Baseline source revision `abe213c44df81a1510558b5595b2d14ffed74d78`. Retain the pinned exports, four witnesses and measurement receipt. Trial builds, decoded arrays, additional captures and negative meshes live under the ignored Wave 2B work directory.
