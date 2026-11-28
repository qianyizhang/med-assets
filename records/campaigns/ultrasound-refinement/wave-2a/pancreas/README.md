# Wave 2A · s1233 pancreas

**Current decision.** [Pancreas r02](orientation-r02/README.md) is adopted for 3D exterior orientation. Exact scan-section claims remain held.

## Earlier r01 decision

**Lead disposition · Hold the pancreas trial and keep the existing chapter.** See the [wave decision](../README.md) for the final scores and chapter binding. The following receipt records the builder’s trial and proposed scores.

At the saved s1233 frame-12 epigastric stop, use the pancreatic body and the posterior venous landmark to orient the model. Follow the broad head, uncinate curve, body and tapered tail in 3D and relate the visible contour to the simulated scan. The proposed chapter is the abdominal survey’s `abd-pancreas`. The current procedural chapter teaches the head and body in the fictional visit. The limited pancreas assessment and separate tail chapter have their own acquisitions.

The [focused contour trial](contour-trial/README.md) recovered the two targeted exterior intersections. Full raw sections and additional grazing cuts still exceed tolerance, so the hold stands.

## Frozen inputs and gates

The [freeze](reference.json) predates candidate shaping. It pins the original s1233 delivery from `build_abdomen.py --track pancreas`, exact frame-12 pose and image data, the CT label's native-grid affine, and three full parallel cuts at −1.5, 0 and +1.5 mm. Compare the new export and exact prior export against the unsmoothed 0.5-isovalue of the pinned CT label, plus matched whole and reverse neutral-clay views. The resampled RAS grid is isotropic at 1.5 mm. Its label represents exterior shape and limits interpretation of thin structures. The frozen source has one connected component and 42 enclosed background voxels. Carry the raw reference into the whole-surface gate and localize any enclosed background before making an exterior interpretation.

Preserve the thin neck and tail with local SDF smoothing and check the smallest regions separately in the overlays. The broad head, uncinate curve, body and tapering tail remain on one exterior. Avoid claiming duct anatomy or inferring unseen structures at the saved stop.

Use the [frozen verifier](../spleen/measure.py) with `freeze pancreas CASE BASELINE OUTPUT`, then `evaluate FREEZE BASELINE MESH SMOOTH_NPZ OUTPUT`. The baseline is the sealed Wave 1 compact study. Compare at ≤0.5 mm lattice spacing to the nearest triangles globally and nearest line segments within the planes. Require bidirectional p95 ≤ 1.5 mm and sampled max ≤ 3 mm. Require volume within 3% of the half-label surface, Euler 2, outward winding, no degeneracy or intersecting nonincident faces, and a 2,500–6,000 triangle export. For density, compare the reimported mesh to the smooth input across 24 orthographic views at 3 px/mm and allow ≤1 px departure. Require nonzero exit on a deliberately displaced copy.

Stop after replay, admission, geometry checks, and four matched witnesses from the clean export. Bind the browser capture to the actual served bytes and preserved frame inputs. Submit proposed scores for independent lead review.

## Proposed result

The **5,800-triangle, 104,432-byte** exterior uses 65% fewer triangles and bytes than the exact previous sweep. The frozen raw CT comparison fails. Proposed **2 / 2 / 3 / 4** scores reflect that failure, visible residual head and uncinate relief, recognizable landmark placement in the isolated view and overlay, and measured reduction. The full protected cuts and qualified use need independent review.

The largest raw whole-surface error is 7.58 mm on the wall of an internal 16-voxel gap around RAS −16.1, 202.9, 361.5 mm. The raw half-label has three enclosed native-mask gaps of 22, 16 and 4 voxels. The worst raw protected-cut errors land on loop contours at the body gaps. The supplied label cannot establish what the gaps represent. The exterior trial fills them while the raw evidence and simulated overlay preserve them.

The filled-label diagnostic has worst bidirectional p95/max of 0.66/2.44 mm globally. Its three dominant contours are within 0.81 mm p95 and 2.65 mm maximum. The full filled-label sections still have 3.15 mm and 6.81 mm errors on separate 3.39 mm and 0.17 mm perimeter tangential loops in the −1.5 mm and saved planes. The saved plane's worst such loop is near RAS −1.1, 196.9, 353.9 mm on the anterior body. Green squares identify those exterior diagnostic maxima, and white circles identify the raw full-cut maxima. Full cuts remain decisive. The narrowed comparison records what the closed-shell representation preserved.

| Gate | Result |
| --- | --- |
| CT distance | **Fail**. Raw global p95/max 0.72/7.58 mm, three protected cuts 7.72/10.18 mm at worst from raw label to r01. Reverse protected maximum 1.16 mm. |
| Local exterior diagnostic | Filled-label candidate maxima are 2.09 mm in the superior tail selection, 1.21 mm at the central neck and 2.41 mm in the inferior uncinate selection. |
| Reimported topology and volume | One outward shell with Euler 2 and zero open or nonmanifold edges, inconsistent winding, degeneracy and nonincident intersections. Raw volume +0.23%. |
| Turning silhouette | 0.79 px maximum versus the smooth pre-decimation input over 24 views at 3 px/mm. |
| Clean replay and admission | Both fresh replays matched SHA-256 `4f853b98b4ec8048cee6a53562478be63faf4a668c158f34490a7535fd17fda0`. Workspace sync, hydrated check-port and validate passed. |
| Negative | The verifier rejected a disposable 14% compression along voxel X with exit 1. The reverse global maximum rose to 5.55 mm and volume also failed, independent of the candidate's existing raw-gap discrepancy. |
| Study player | A fresh s1233 sweep and compact build rendered the exact two meshes at frame 12 in disposable Chrome. Both served identical pose, grayscale and overlay files. The named survey chapter uses its procedural scene in the baseline. |

Tested from `e3961e616c8e` using the [package replay](../../../../../models/pancreas_s1233/README.md#replay), Wave 1 compact baseline and isolated staging. Pass `--pancreas-case CASE` to [measure.py](../spleen/measure.py) for the additional filled exterior and contour diagnostics. The [spleen replay procedure](../spleen/README.md#proposed-result) describes the shared rendering and capture scripts. Keep scratch under `.artifacts/us-wave2a/pancreas/` and review retention after 30 days.

[Previous and r01](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/previous-vs-r01.webp) · [Matched surfaces](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/matched-surfaces.webp) · [Protected planes](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/protected-planes.webp) · [Frame 12](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/live-frame-12.webp) · [Measurements](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/measurements.json) · [Lead review](../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/reviews.json)
