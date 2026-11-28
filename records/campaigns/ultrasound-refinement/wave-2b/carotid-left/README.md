# Wave 2B · s1127 left common carotid

Follow the thin left common carotid course from the transverse stop at frame 12 to the longitudinal stop at frame 48. The separate s1127 exemplar accompanies the fictional duplex's `carotid-normal / left-cca-gray` at worked frame 14. The scope is 3D exterior course and orientation. Plaque, wall thickness, lumen patency and flow interpretation remain with separate evidence.

## Frozen comparison and result

The [freeze](frozen.json) pins both previous display meshes, the [asset package](../../../../../models/carotid_left_s1127/README.md) source and frame, plus scan, overlay and pose inputs. The full left mask has 1,712 voxels across source slices 356–408. The standalone [371, 407) crop has 904 voxels. Both extents are a single connected label with zero enclosed gaps. Source slice 408 is the scan's superior limit. No separate bifurcation or branching reconstruction was added. The cited profile and cut positions represent one case.

Both packed candidates passed the raw-label comparison, including saved cuts and adjacent full cuts at frames 12 and 48 for the neck export, cap-adjacent cuts for both extents, and a null cut beyond each superior cap. Compare at 0.5 mm or finer in both directions. Limits are 1.5 mm p95, 3 mm sampled maximum, 3% volume delta and 1 pixel silhouette departure across 24 directions at 3 pixels/mm.

| Check | Neck sweep crop | Full label and thyroid context |
| --- | ---: | ---: |
| Triangles · bytes | 1,650 · 29,732 | 1,900 · 34,232 |
| Whole-surface p95 / max | 0.35 / 0.77 mm | 0.31 / 0.81 mm |
| Protected-plane maximum | 0.74 mm | 0.32 mm |
| Enclosed volume delta | −0.48% | −0.36% |
| Turning-silhouette maximum | 0.50 px | 0.56 px |

Both clean exports are closed outward Euler-2 shells. Neither has open or nonmanifold edges, flipped shared edges, degenerate triangles or nonincident intersections. Double replay matched both governed payloads. Hydrated AssetKit sync and check-port passed, as did native show, impact, validate, economy and review check. The same geometry checker rejected both meshes compressed by 25% transversely, returning exit 1 for each. Chrome rendered both frozen frames, with matched pose, grayscale and overlay bytes and the exact requested neck mesh. The [wave delivery](../README.md) records the independent chapter review and adoption.

See the [measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-left-wave-2b/measurements.json) and the [four matched witnesses](../../../../../experiments/ultrasound-sweep/development/asset-reviews/carotid-left-wave-2b/previous-vs-r01.webp). Replay via [freeze_carotid.py](../carotid/freeze_carotid.py) and [measure.py](../aorta/measure.py). Scratch files under `.artifacts/us-wave2b/carotid-left/` are retained for 30 days.
