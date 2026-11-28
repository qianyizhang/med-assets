# Wave 2B right common carotid builder receipt

The [right carotid r01 exports](../../../../../models/carotid_right_s1127/asset.record.json) passed the raw-label geometry gates. The separate-subject s1127 exterior supports orientation in 3D. The named `carotid-normal / right-cca-gray` task uses the worked frame 14 and the exemplar's longitudinal frame 48. The [wave delivery](../README.md) records the independent chapter review and adoption.

| Export | Triangles | Packed size | Raw p95 / max | Protected max | Volume delta | Turning silhouette |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `neck` · carotid reader | 1,650 | 29,732 bytes | 0.38 / 1.39 mm | 1.33 mm | −0.31% | 0.50 px |
| `carotid` · thyroid context | 1,900 | 34,232 bytes | 0.37 / 1.39 mm | 0.30 mm | −0.32% | 0.50 px |

The center and parallel cuts at longitudinal frame 48 agree within 0.90 mm. The two small loops just inside the lower carotid crop survive. The full label reaches the last imaged axial slice. The reference and candidate both have zero intersections at z = 408.75, just above the z = 408.5 cap. Both reimported meshes have a single outward Euler-2 shell with no degeneracy, nonmanifold edges or nonincident intersections.

[Exact previous and r01 exports](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-right-wave-2b/previous-vs-r01.webp) · [Matched label and mesh](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-right-wave-2b/matched-surfaces.webp) · [Protected CT cuts](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-right-wave-2b/protected-planes.webp) · [Chrome at frames 12 and 48](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-right-wave-2b/live-frame-12.webp) · [Measurement receipt](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-right-wave-2b/measurements.json)

## Reproduce the checks

The [frozen packet](frozen.json) pins the local baseline `.artifacts/us-pancreas-r02/{stage,final}` and raw half-label CT surfaces. Run the [package recipe](../../../../../models/carotid_right_s1127/README.md#replay) twice into fresh directories. Both reruns matched the packaged bytes for each export. The Git LFS filter covers both files. Each candidate shifted 6 mm exited 1 in the same raw-label checker.

```sh
wave=records/campaigns/ultrasound-refinement/wave-2b
work=.artifacts/us-wave2b/carotid-right
base=.artifacts/us-pancreas-r02
export PYTHONPATH="$PWD/experiments/ultrasound-sweep${PYTHONPATH:+:$PYTHONPATH}"
python3.12 "$wave/carotid/freeze_carotid.py" right "$S1127_CASE" "$base" \
  "$wave/carotid-right" "$work/reference"
python3.12 "$wave/aorta/measure.py" carotid-right "$work/reference/carotid-right-reference.npz" \
  "$work/replay-a/neck.mesh" "$work/replay-a/neck.npz" "$work/carotid-right.json" \
  --frozen "$wave/carotid-right/frozen.json"
```

Run the same command with the logical export `carotid-right-full`, its corresponding reference, and `carotid.mesh` and `carotid.npz`. Add `--distort` with a fresh scratch path to exercise the rejection. [Browser capture](../aorta/player.mjs) verified each actual mesh and the frozen scan, overlay and pose responses at both saved frames in a matched Chrome comparison. This replay substitutes one mesh on the previous sweep. The final assembly and chapter binding have their own checks.

The source baseline is `abe213c44df81a1510558b5595b2d14ffed74d78`. Retain the export pair, frozen source receipt and comparison images. Dense surfaces, logs and negative payloads are under ignored Wave 2B staging.
