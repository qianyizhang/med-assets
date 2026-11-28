# Wave 2A · Gallbladder r01 candidate

**Lead disposition · Adopt for the named exterior-orientation task.** See the [wave decision](../README.md) for the final scores and chapter binding. The following receipt records the builder’s trial and proposed scores.

The candidate preserves the broad fundus, body and narrowing toward the neck. It recovers about 0.8 mm at the label's superior end and smooths the central surface. The lower orbit and tissue overlay expose the taper. The liver partly obscures it in the default camera. The proposed score is **4/3/3/4** for fidelity, form, readability and economy. The worker checks passed. The lead subsequently accepted the exterior-orientation task.

## Evidence

| Check | Result |
| --- | --- |
| Frozen input | [Exact prior mesh, source, pose, planes, landmarks and limits](frozen.json). The prior root gallbladder sweep came from [build_study.py](../../../../../experiments/ultrasound-sweep/build_study.py) and [prepare_scenes.py](../../../../../experiments/ultrasound-sweep/prepare_scenes.py). The gallbladder supplied as context in the liver sweep is a distinct payload. |
| Reimport against CT half-label | Worst bidirectional p95/max **0.74/1.64 mm** globally and **0.68/1.28 mm** across the three planes. The previous sweep was **0.91/2.56 mm** globally. Volume delta **+0.29%**, one closed outward shell with Euler **2**, zero degenerate or intersecting faces. |
| Payload and outline | **2,136 → 1,940** triangles and **38,480 → 34,952** bytes, a **9%** reduction. The projected outline differs by at most **0.56 px** from the dense smooth surface at 3 px/mm in 24 orthographic views. |
| Replays and admission | Two clean replays matched the exact [packaged SHA-256](../../../../../models/gallbladder_s1233/asset.record.json). AssetKit sync, hydrated check-port and validate passed. |
| Negative | Displacing the candidate 6 mm in the superior direction triggered exit **1**. The global maximum rose to **6.64 mm** and the silhouette exceeded **18 px**. |
| Live at frame 12 | Chrome decoded the same probe pose, B-mode and CT-derived overlay in both sweeps. The actual prior and candidate mesh response hashes matched their pins. Verified orbit, torso-opacity control and frame 11 back to 12. The candidate used a disposable staging copy of the original player. |

[Exact previous vs r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/previous-vs-r01.webp) · [CT and matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/protected-planes.webp) · [Running player](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/live-frame-12.webp) · [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/measurements.json) · [Proposed scores](../../../../../experiments/ultrasound-sweep/development/asset-reviews/gallbladder-wave-2a/reviews.json)

A shallow inferior shoulder remains in the neutral-clay view. The source label supports exterior orientation. Wall thickness, the duct junction, and stone motion require separate evidence.

## Reproduce the decisive checks

Restore the exact Wave 1B delivery at the paths in [frozen.json](frozen.json). Use the case and environment in the [package recipe](../../../../../models/gallbladder_s1233/README.md#rebuild). Run from the repository root. The freeze command validates the sealed inputs and regenerates the reference arrays. Perform the package replay into two fresh directories and compare with `cmp`.

```sh
export PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}"
checks=records/campaigns/ultrasound-refinement/wave-2a/kidney-left
scratch=.artifacts/us-wave2a/gallbladder
python3.12 "$checks/freeze.py" "$S1233_CASE" gallbladder
python3.12 "$checks/verify.py" gallbladder "$scratch/replay-a/gallbladder.mesh" \
  "$scratch/replay-a/smooth.npz" "$scratch/measurements.json"
python3.12 "$checks/verify.py" gallbladder "$scratch/replay-a/gallbladder.mesh" \
  "$scratch/replay-a/smooth.npz" "$scratch/negative.json" --distort "$scratch/displaced-new.mesh"
```

The second verifier run must exit 1 with failed distance or silhouette gates. Use `--prior` and the baseline path in `frozen.json` for the previous comparison.
