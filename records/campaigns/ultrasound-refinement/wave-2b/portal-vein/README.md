# Wave 2B · s1233 portal and splenic vein

Orbit the combined vein surface in the `portal-vein` sweep at the saved frame-12 long-axis stop. Follow the curved course and visible joins in relation to the liver and probe. The r02 model is a selectable companion to the worked `abdomen-survey / abd-portal-doppler` chapter. The existing color and spectral acquisition action remains a separate worked exercise.

## Frozen reference and decision rules

The [freeze](reference.json) was produced before shaping at source revision `abe213c44df8`. It identifies the original abdominal builder output in the staging tree, the identical compact route, the saved frame pose and images, the worked visit, and the raw 0.5-isovalue and three full oblique cuts at −1.5, 0 and +1.5 mm. The case reference uses the TotalSegmentator v2.0.1 s1233 combined label on its 1.5 mm RAS grid. The working label supplies no separate branch taxonomy or acquisition slice orientation.

The label has 6,045 foreground voxels in one connected component. Its half-label has one closed orientable shell and one handle. There are zero enclosed background voxels, and the label terminates at least 65 voxels from any CT grid boundary. Preserve the handle and all visible terminal geometry. Treat the visible source junctions as regional geometry within the combined label. Keep the source endpoints as segmentation endpoints.

Require sampled bidirectional p95 ≤ 1.5 mm and maximum ≤ 3 mm globally and in each raw cut. Preserve RAS bounds within 1.5 mm and enclosed volume within 3%. Test 24 turning silhouettes against the dense shaped reference at 3 px/mm with departure ≤ 1 px. Accept 1,500–6,000 oriented triangles with one closed shell, Euler characteristic zero, and zero nonmanifold, degenerate, misoriented or intersecting features. A translated mesh must fail the same executable checker. Preserve the frame and existing action, and inspect the four matched witnesses before deciding whether to adopt.

The checker uses the [Wave 1 geometry primitives](../../wave-1/measure.py) for exact nearest primitive distance over a 0.5 mm sampling lattice, the [Wave 2A full-cut comparator](../../wave-2a/spleen/measure.py), and the [Wave 1B turning-mask comparison](../../wave-1b/measure.py). Start with the unchanged previous export for the raw gate, then compare clean reimports of both exports against the same reference.

## Candidate receipt

R02 keeps one closed shell and the source handle. Bidirectional worst global / section distances are 0.99 / 2.63 mm. The matched frame-12 plane is within 0.89 mm. Volume changes by +0.87%, RAS bounds by 0.70 mm, and the 24-view silhouette by 0.56 px against the dense shaped surface. The old mesh has Euler characteristic 2 and is 8.76% smaller than the raw reference by volume. Its three protected cut distances pass. R02 reduces the previous 11,316 triangles and 203,720 bytes to 6,000 triangles and 108,008 bytes. The 9 mm translated control exits 1 and fails geometry gates in both directions. Two clean replays reproduced the registered mesh SHA-256 byte-for-byte.

| Witness | Evidence |
| --- | --- |
| Prior and r02 | [Matched clay, reverse and junction detail](../../../../../experiments/ultrasound-sweep/development/asset-reviews/portal-vein-wave-2b/previous-vs-r02.webp) |
| Three surfaces | [Exact prior, raw half-label and r02](../../../../../experiments/ultrasound-sweep/development/asset-reviews/portal-vein-wave-2b/matched-surfaces.webp) |
| Raw contours | [Three full protected cuts and worst sampled locations](../../../../../experiments/ultrasound-sweep/development/asset-reviews/portal-vein-wave-2b/protected-planes.webp) |
| Saved sweep | [Actual study player at frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/portal-vein-wave-2b/live-frame-12.webp) |

[Measurements and Chrome identity receipt](../../../../../experiments/ultrasound-sweep/development/asset-reviews/portal-vein-wave-2b/measurements.json). The browser compared the compact baseline with a disposable copy containing the exact r02 payload at its existing deduplicated route. The previous and r02 scenes served identical pose, grayscale and overlay bytes. In both live scenes, the liver partly obscures the venous joins. The isolated matched clay views reveal them. Minor undulations remain near the source endpoints. Raw clay shows the underside relief. R02 softens its shoulders and the axial bands on the upright limb, with a flatter central patch still visible. R01 remains available for replay and comparison. The [wave delivery](../README.md) records independent ratings and the integrated Doppler chapter check.

To reproduce the geometry evidence, run [measure.py](measure.py) with `freeze CASE BASELINE OUTPUT`, then `evaluate REFERENCE_NPZ BASELINE MESH SMOOTH_NPZ OUTPUT`. The baseline root supplies `stage` and `final`; the candidate [replay](../../../../../models/portal_vein_s1233/README.md#replay) supplies the last two geometry inputs.
