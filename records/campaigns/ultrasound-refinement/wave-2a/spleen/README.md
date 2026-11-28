# Wave 2A · s1233 spleen

**Lead disposition · Adopt for the named exterior-orientation task.** See the [wave decision](../README.md) for the final scores and chapter binding. The following receipt records the builder’s trial and proposed scores.

At the saved s1233 long-axis sweep stop, locate the convex diaphragmatic face and the recessed medial hilum in 3D and orient the simulated scan to the near and far boundaries. The proposed chapter is the abdominal survey’s `abd-spleen`. Its procedural lesson remains the control for the fictional visit and its authored 113.9 mm span. The standalone s1233 sweep provides the registered geometry baseline. This trial evaluates the exterior and a visible contour recess.

## Frozen inputs and gates

The [freeze](reference.json) predates candidate shaping. It pins the native label grid, exact previous standalone binary, acquisition script, grayscale and tissue-overlay pixels, and the three full parallel cuts through frame 12. The previous surface comes from the s1233 `build_abdomen.py --track spleen` sweep before native spleen export binding. Its axial bands are most visible across the broad face. Compare it and the candidate to the raw 0.5-isovalue from the pinned mask. Use identical neutral-clay views and inspect the hilum from the reverse side. The recovered input is a resampled RAS label grid. The working grid has 1.5 mm isotropic spacing. The source resolution limits what the surface can show about small attachment structures and vessels.

Preserve one outward closed shell, the long convex face, the end margins and the medial recess. Smooth the SDF more along RAS Z to reduce the observed axial bands. Use a narrower kernel near the hilum and tapering margins. Reduce the resulting surface with Blender's quadric collapse. The mask freeze contains one component and zero enclosed background voxels.

Use [measure.py](measure.py) with `freeze spleen CASE BASELINE OUTPUT`, then `evaluate FREEZE BASELINE MESH SMOOTH_NPZ OUTPUT`. The baseline is the sealed Wave 1 compact study. The verifier samples at 0.5 mm or finer and measures to the nearest triangle globally and nearest line segment in each full plane. Limits are bidirectional p95 ≤ 1.5 mm and sampled max ≤ 3.0 mm. Enclosed volume stays within 3% of the half-label surface. The reimport has Euler 2 and zero degeneracy, inconsistent winding or nonincident intersections. The 24-view projected silhouette departure from the approved density input is at most one display pixel at 3 px/mm. The packed mesh is in the 2,500–5,000 triangle band. Exercise the same verifier on a deliberately displaced copy and require a nonzero exit.

Stop after replays, admission, geometry checks, and four matched witnesses from the clean export. Bind the browser capture to the actual served bytes and preserved frame inputs. Submit proposed scores for independent lead review.

## Proposed result

The candidate uses **4,800 triangles and 86,432 bytes**, down 75% from the previous sweep. The broad face has a continuous highlight. Subtle terracing persists near the protected end margins. The reverse view preserves the deep medial indentation. The default player and its axial view give kidney, rib and probe context, and the indentation is clearer in the isolated clay detail and tissue overlay. Proposed scores are **4 / 3 / 3 / 4** for fidelity, form, readability and economy. The lead subsequently adopted the orientation task in the local survey.

| Gate | Result |
| --- | --- |
| Reimported mesh | Single outward shell, Euler 2, zero open or nonmanifold edges, inconsistent winding, degeneracy or nonincident intersections. Volume +0.098%. |
| CT distance | Worst directional p95/max globally 0.76/1.75 mm and in the three cuts 1.15/2.81 mm, with the worst location at the medial shoulder. |
| Turning silhouette | 0.71 px maximum versus the smooth pre-decimation surface in 24 views at 3 px/mm. |
| Clean replay and admission | Both fresh package replays matched SHA-256 `76e01c95fe395952d2bfae3333fb9d228b75ff2016e736a5ebe67bd1a02b5a03`. Workspace sync, hydrated check-port and validate passed after historical and new revisions were combined under the canonical owner. |
| Negative | The same verifier rejected a disposable 14% compression along voxel X with exit 1. Global max rose to 7.27 mm. |
| Study player | A fresh s1233 spleen sweep and complete compact build opened in disposable Chrome. Both previous and candidate requests returned their expected mesh bytes and the same pose, grayscale and overlay files. Frame 12 rendered in oblique and axial presets. The named chapter still uses its procedural model. |

Tested from `e3961e616c8e` using the [package replay](../../../../../models/spleen_s1233/README.md#replay), Wave 1 compact baseline and isolated staging. The initial broad pass exceeded cut tolerance at the hilar shoulder. Applying a narrower kernel in that neighborhood reduced the worst protected-cut error from 4.05 to 2.81 mm.

[Previous and r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/previous-vs-r01.webp) · [Matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/protected-planes.webp) · [Frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/live-frame-12.webp) · [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/measurements.json) · [Proposed review](../../../../../experiments/ultrasound-sweep/development/asset-reviews/spleen-wave-2a/reviews.json)

For visual replay, use [render_clay.py](render_clay.py) with the frozen NPZ, measurement report, prior mesh, r01 mesh and output directory after Blender's `--` delimiter. Use [capture.mjs](capture.mjs) with the baseline URL, rebuilt study URL, capture directory and report. Use [witnesses.py](witnesses.py) to compose the frozen directory, measured directory, clay renders and captures. Scratch material is under `.artifacts/us-wave2a/spleen/`, with retention review due after 30 days.
