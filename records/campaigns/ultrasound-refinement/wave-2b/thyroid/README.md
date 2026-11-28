# Wave 2B · s1127 bilateral thyroid

Follow each lobe from the transverse thyroid sweep into its longitudinal view at frame 48 in `thyroid-right` and `thyroid-left`. Relate the saved scan to the matching lobe and to the central bridge in the 3D scene. The two worked `thyroid-normal` longitudinal chapters have authored frame-12 acquisitions. The original right-sweep bridge assessment stays bound to the exact historical R01 export and its own observations. This packet evaluates the s1127 native long-axis views for 3D orientation.

## Frozen source and checks

The [freeze](reference.json) pins both exact prior sweeps, including their identical gland bytes, and the compact deduplicated export. It records both sides’ frame 0, 12 and 48 poses, scan images and tissue overlays, the worked visit control, and the raw mask and grid. The source has one component of 4,640 voxels, zero enclosed voids, and no source-grid boundary clips. The lobe names identify regions of the combined source label.

Use the raw half-label for global bidirectional fidelity and the three full parallel planes on either side at frames 12 and 48. Protect the transverse entry and five sagittal cuts at the isthmus. The frozen limits are 1.5 mm p95, 3 mm maximum, 3% volume change and 1.5 mm RAS extent change. Check one outward closed shell, Euler characteristic 2 and zero nonmanifold edges, misorientation, degeneracy and nonincident triangle intersections. The unchanged admission trial allows the previously reviewed 6,248 triangles in a 1,500–6,500 band. Reduction must preserve the dense shaped surface within 1 px across 24 turning views at 3 px/mm.

## Why the byte-equivalent admission failed

The historical model has a global worst sampled distance of 1.46 mm and preserves the isthmus. In the left longitudinal plane and its +1.5 mm neighbor, the old surface loses small loops where the raw plane grazes the shoulder. The in-plane errors are 5.69 and 14.98 mm. The same points lie only 0.62 and 0.89 mm from the 3D surface. At ±0.75 mm in the neighboring oblique sections the contours join the lobe or disappear. Native axial slices show the source shoulder moving past these points one voxel at a time. The old export also loses 3.89% of raw volume. The original bridge rating and its tested task remain valid.

## R03 candidate

R03 limits the worst global distance to 1.23 mm, the three right long-axis cuts to 1.31 mm, and the three left cuts to 2.33 mm. Its worst isthmus cut is 0.75 mm. Enclosed volume changes by −1.00%, RAS extents by 1.01 mm, and turning silhouettes by 0.50 px at the tested zoom. It uses 5,900 triangles and 106,232 bytes. Local preservation restores small left shoulder features visible in the raw cuts. The restored region carries more voxel-scale relief than the smoother historical model. The anterior bridge remains continuous. R03 softens the bridge and shoulders compared with r02 while a visible left shoulder ridge remains. One stronger smoothing trial loses a left longitudinal grazing loop and fails at 6.00 mm. [Matched shoulder progression](shoulder-refinement.webp)

Two clean replays of each revision returned identical registered bytes. The 9 mm translated copy failed the geometry gate. Hydrated r03 check-port and LFS tracking passed. Disposable Chrome loaded the prior and r03 compact sweeps with exact matching pose, grayscale and overlay bytes on each side. The longitudinal reference controls reached frame 48. The separate integrated worked-chapter checks and independent ratings are the lead’s responsibility.

| Evidence | Witness |
| --- | --- |
| Prior and r03 | [Matched overview, reverse and bridge details](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/previous-vs-r03.webp) |
| Raw half-label comparison | [Prior, raw label and r03 under fixed clay lighting](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/matched-surfaces.webp) |
| Protected cuts | [Bilateral long axis](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/protected-planes.webp) and [isthmus](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/isthmus-cuts.webp) |
| Live study | [Matched frame 12 sweep](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/live-frame-12.webp) and [actual frame 48 learner action](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/live-frame-48.webp) |

See the [measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-wave-2b/measurements.json) and the [asset replay](../../../../../models/thyroid_s1127/README.md#replay). Run [measure.py](measure.py) with `freeze CASE BASELINE OUTPUT`, then `evaluate REFERENCE_NPZ BASELINE MESH OUTPUT --dense SMOOTH_NPZ` for a shaped revision. Baseline supplies `stage` and `final`; replay provides the packed mesh and dense shaped surface. Keep trial variants and scratch captures under `.artifacts/us-wave2b/thyroid/`.
