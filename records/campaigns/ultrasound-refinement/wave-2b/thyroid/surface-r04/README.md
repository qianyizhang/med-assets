# s1127 thyroid r04 · left shoulder correction

[Blind shoulder comparison](shoulder-test.webp) · [Matched r03 and r04 exports](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-r04/previous-vs-r04.webp)

R04 replaces r03 on the two thyroid sweeps, their long-axis chapter companions and the two carotid sweeps that show the gland as context. Both meshes have 5,900 triangles and occupy 106,232 bytes. The improvement is visible on the superior left lobe, on the right of the front image. R03 has steps along the silhouette and a broken diagonal highlight. R04 has a rounded crown and a continuous highlight in front and side light. The isthmus remains visible, with softer fine relief around the bridge and lower lobes.

## Visual test

Open the blind sheet before reading the key. Follow the highlighted shoulder from the overview into both close-ups. Compare continuity of the outer edge and the highlight, then check that the lobe and bridge still have distinct shapes.

<details><summary>Show identities and independent judgment</summary>

A is historical r01, B is r04, and C is r03. The independent reviewer ranked **B, A, C** before seeing revision names, triangle counts or metrics. The differences between C and the other surfaces were visible in both close-ups. The B–A difference was smaller and most apparent at close range. The original wave underweighted the r03 defect. Left-shoulder form on r03 was revised from 3 to 2. The right-lobe-only assessment retains its original form score.

</details>

## Why the correction works

The old smooth r01 already stayed within 1.46 mm of the raw reference globally. Its 14.98 mm left-section error came from a grazing loop only 0.89 mm away in 3D. Blending the raw label back into r03 recovered this loop and transferred voxel-scale steps onto the shoulder. R04 starts from a smooth field. Six broad Gaussian supports gently displace it near the inner and outer loops. Only their locations and inside/outside signs are used. A smooth control without local support missed a frozen cut by 9.84 mm. A narrower 2.4 mm trial also passed, but left a small dimple in the side view. The selected 4 mm support retained the smoother highlight.

| Check on the delivered surface | Result |
| --- | --- |
| Global raw half-label distance | Worst direction p95 0.54 mm, maximum 1.44 mm. Within the superior left region the worst distance is 1.16 mm, compared with 1.29 mm for r01 and 0.85 mm for r03. |
| All 18 original protected cuts | Pass. Right frame-48 maximum 1.41 mm, left maximum 2.32 mm, five sagittal isthmus cuts at most 0.84 mm. |
| Eight additional parallel cuts | Worst in-plane distance 4.13 mm on the left at +0.75 mm. The nearest point on the 3D surface is 0.64 mm away. R03 measured 2.63 mm in that plane. This limits any arbitrary-section contour claim. |
| Topology, volume and extent | One outward closed shell. Zero open, degenerate, nonmanifold, misoriented or intersecting features. Volume −0.71% against raw. Maximum bounds change 1.08 mm. |
| Economy and replay | Maximum turning-silhouette departure 0.50 px over 24 views at 3 px/mm. Two clean builds reproduced the registered SHA-256. A copy translated 9 mm failed the original checker. |

The independent four-axis scores are **4/3/3/4 for the right** and **3/3/3/4 for the left**, in fidelity, form, readability and economy order. Both sides support exterior orientation at the authored pose. The additional left grazing cut limits fidelity for arbitrary section matching. The camera and probe overlap the target in the default view, and the transverse entry and axial orbit clarify the isthmus. These are agent assessments of the teaching surface.

[Exact measurements and live response hashes](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-r04/measurements.json) · [Bilateral frame 48](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/thyroid-r04/live-frame-48.webp) · [Delivery receipt](delivery.json)

## Reproduce

Replay the [asset recipe](../../../../../../models/thyroid_s1127/README.md) in two fresh directories. Run the [existing geometry evaluator](../measure.py) with `evaluate REFERENCE_NPZ BASELINE R04_MESH OUTPUT --dense SMOOTH_NPZ --previous-revision r03`. The frozen Case reference and Wave 2A baseline still identify the original label and r01. The previous-export comparison in this corrective receipt uses r03. Run [check_neighbors.py](check_neighbors.py) with the same reference and an output JSON path for regional 3D distances and the eight additional cuts.

The [clay renderer](../../portal-vein/render_clay.py) takes the frozen reference, measurements, r03 mesh, r04 mesh and fresh output folder, then `--preset thyroid --thyroid-control R01_MESH`. [blind.py](blind.py) composes the blind plate from these clean-import renders. Trial meshes, numerical arrays, uncropped screenshots and build logs are under ignored `.artifacts/us-wave2b/thyroid-fix/`.
