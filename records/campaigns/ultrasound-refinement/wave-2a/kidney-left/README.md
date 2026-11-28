# Wave 2A · Left kidney r01 candidate

**Lead disposition · Adopt for the named exterior-orientation task.** See the [wave decision](../README.md) for the final scores and chapter binding. The following receipt records the builder’s trial and proposed scores.

The candidate softens the inferior bands and preserves both poles and the medial recess. At the saved s1233 left-flank view, orbiting the probe scene and enabling the tissue overlay exposes the recess. The default view partly obscures it. The proposed score is **4/3/3/4** for fidelity, form, readability and economy. The worker checks passed. The lead subsequently accepted the exterior-orientation task.

## Evidence

| Check | Result |
| --- | --- |
| Frozen input | [Exact baseline, source, pose, planes, landmarks and limits](frozen.json). The previous sweep can be rebuilt by [the abdominal track recipe](../../../../../experiments/ultrasound-sweep/build_abdomen.py) with the public s1233 case and retained atlas inputs. The prior survey chapter still provides the authored schematic. |
| Reimport against CT half-label | Worst bidirectional p95/max **0.86/2.47 mm** globally and **1.02/1.63 mm** across the three planes. The previous sweep is closer to CT globally at **0.63/1.92 mm**. Volume delta **−0.05%**, one closed outward shell with Euler **2**, zero degenerate or intersecting faces. |
| Payload and outline | **25,752 → 4,800** triangles and **463,568 → 86,432** bytes, an **81%** reduction. The projected outline differs by at most **0.71 px** from the dense smooth surface at 3 px/mm in 24 orthographic views. |
| Replays and admission | Two clean replays matched the exact [packaged SHA-256](../../../../../models/kidney_left_s1233/asset.record.json). AssetKit sync, hydrated check-port and validate passed. |
| Negative | Displacing the candidate 6 mm in the superior direction triggered exit **1**. The global maximum rose to **6.80 mm** and the silhouette exceeded **18 px**. |
| Live at frame 12 | Chrome decoded the same probe pose, B-mode and CT-derived overlay in both standalone sweeps. The actual previous and candidate mesh response hashes matched their pins. Verified orbit, torso-opacity control and frame 11 back to 12. The candidate used a disposable staging copy of the original player, with the exact export as its only mesh change. |

[Exact previous vs r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/previous-vs-r01.webp) · [CT and matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/protected-planes.webp) · [Running player](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/live-frame-12.webp) · [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/measurements.json) · [Proposed scores](../../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-left-wave-2a/reviews.json)

The source label resolves the renal exterior and recess. A measured renal length and internal structures require separate acquisition evidence. The shaded surface still has shallow inferior relief.

## Reproduce the decisive checks

Restore the exact Wave 1B delivery and staging tree at the paths in [frozen.json](frozen.json). Use the case and environment in the [package recipe](../../../../../models/kidney_left_s1233/README.md#rebuild). Run these commands from the repository root. The freeze command revalidates the sealed prior mesh and source and regenerates the reference arrays. Perform the package replay into two fresh directories and compare the results with `cmp`.

```sh
export PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}"
checks=records/campaigns/ultrasound-refinement/wave-2a/kidney-left
scratch=.artifacts/us-wave2a/kidney-left
python3.12 "$checks/freeze.py" "$S1233_CASE" kidney-left
python3.12 "$checks/verify.py" kidney-left "$scratch/replay-a/kidney-left.mesh" \
  "$scratch/replay-a/smooth.npz" "$scratch/measurements.json"
python3.12 "$checks/verify.py" kidney-left "$scratch/replay-a/kidney-left.mesh" \
  "$scratch/replay-a/smooth.npz" "$scratch/negative.json" --distort "$scratch/displaced-new.mesh"
```

The second verifier run must exit 1 with failed distance or silhouette gates. Use `--prior` and the baseline path in `frozen.json` to compare the previous sweep using the same CT and plane sampling.
