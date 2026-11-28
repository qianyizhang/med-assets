# Wave 2B · s1127 trachea

Use the separate s1127 transverse acquisition at thyroid sweep frame 0 to locate the air column deep to the isthmus. The named route is `thyroid-normal / thyroid-axial` at worked frame 12. The carotid crops give nearby 3D context. Their saved transverse and longitudinal planes do not intersect the tracheal label. Wall layers, cartilage, obstruction and clinical dimensions remain outside this comparison.

## Frozen labels, crops and cuts

The [freeze](reference.json) pins the [package's](../../../../../models/trachea_s1127/README.md) source, grid, exact earlier track binaries, poses and pixels. The label spans voxel Z 312–389. The full reference has 7,550 voxels and shows a distal split into two branches. The thyroid crop [344, 409) retains 5,046 voxels. The carotid crop [369, 407) retains 2,480. Each is a single 3D component with no enclosed gaps. The frozen axial cuts protect the full bifurcation, the route-specific caps and the original superior boundary. The thyroid planes cover both sides at their saved stops and parallel offsets. The frame-0 raw cut crosses shared mesh edges. Its contour freeze merges coincident edges within 0.0000001 mm and retains every distinct nonzero segment.

The first candidate failed two thyroid cuts. The +1.5 mm plane near thyroid-right frame 12 reached 1.505 mm p95 at the taper around slices 381–382. The −1.5 mm plane near thyroid-left frame 48 reached 3.36 mm in plane on a short grazing crop-edge loop, only 0.24 mm from the 3D surface. Native slices 342–344 support that lower shoulder, and the upper shoulder recedes between 382 and 383. Localized pulls of at most 0.36 mm reduced the worst final in-plane error to 2.19 mm and passed the unchanged 1.5 mm p95 and 3 mm maximum limits. The raw offset frame-0 plane can still split into additional short loops. The accepted geometry check measures the complete cuts and the exemplar teaches midline orientation.

| Check | Thyroid crop | Carotid crop | Full label |
| --- | ---: | ---: | ---: |
| Triangles · bytes | 2,900 · 52,232 | 2,000 · 36,032 | 3,800 · 68,432 |
| Whole-surface maximum | 1.26 mm | 1.26 mm | 1.20 mm |
| Protected-plane maximum | 2.19 mm | 0.52 mm | 0.53 mm |
| Enclosed volume delta | −0.20% | −0.42% | −0.20% |
| Turning-silhouette maximum | 0.50 px | 0.50 px | 0.56 px |

All three clean exports pass the closed outward Euler-2 checks and preserve the protected empty planes. The thyroid crop is 52% smaller than its prior display mesh. Two independent fresh replays match the governed bytes for all three exports. The hydrated AssetKit sync and check-port, native show and impact, validate, economy and review check pass. The verifier rejects a 6 mm lateral shift of each export with exit 1. The frozen geometry comparisons use nearest triangles globally and nearest contour segments with ≤0.5 mm samples. The turning silhouettes use 24 views at 3 pixels/mm.

The Chrome witness exercises the exact thyroid port with preserved scan, overlay and pose bytes at frame 0 and frame 12. At frame 0 the tissue overlay locates the trachea under the isthmus. The smoother trunk remains visible in both clay views. Some contour bands remain near its ends and on the full label's distal branches. The [wave delivery](../README.md) records the independent review and adoption.

[Previous and r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/trachea-wave-2b/previous-vs-r01.webp) · [Matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/trachea-wave-2b/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/trachea-wave-2b/protected-planes.webp) · [Live frame 0 and 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/trachea-wave-2b/live-frame-12.webp) · [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/trachea-wave-2b/measurements.json)

The freeze and measurement commands are [freeze.py](freeze.py) and [measure.py](../aorta/measure.py). The shared [clay](../aorta/render_clay.py) and [player](../aorta/player.mjs) tools render the exact exports. [witnesses.py](witnesses.py) composes the four views. Scratch under `.artifacts/us-wave2b/trachea/` is retained for 30 days.
