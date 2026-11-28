# s1233 liver dome pretrial · 2026-11-28

**Keep `anatomy:s1233:liver-window@r01:liver` for the lobe-identification task.** Compared with r01, the candidate has fewer visible terraces along the superior dome. Forty-two previously nondegenerate triangles have a negative dot product between their baseline and candidate normals. A separate calculation on the serialized vertices found 42 reversals and zero new collapses among the failed faces. This fails the [predeclared acceptance criteria](decision-before-candidate.md). The existing lesson pin and its 3/3/4/4 review still apply. [Campaign specification](../../../../docs/ULTRASOUND_REFINEMENT_SPEC.md)

## Matched witnesses

| View | What to inspect |
| --- | --- |
| [Whole liver and two dome details](matched-dome.webp) | The roof terraces soften at both detail angles. Camera, scale, light and shading are matched within each column. |
| [Protected cleft at axial slice 207](matched-cleft.webp) | Gold traces the half-label boundary. Cyan traces the mesh cut. The central slice and both neighboring slices retain the same measured deviation. |
| [Sweep frames 12 and 13](matched-player.webp) | Each row contains crops from the actual player. The liver surface changes in 3D. The simulated scan and tissue overlay match between builds at each pose. |

## Replay and measurement

Tested local source revision `199d2836e55186fe6cd255b9d618327ae5afdaf8`. Input was the [owner's s1233 liver mask and grid](../../../../models/liver_s1233/asset.record.json), with SHA-256 `0e37697cde4bf2f6042fa89d338cfbe71d85b4b44e42801840be5612c4785980`. Credit Jakob Wasserthal, the TotalSegmentator contributors and University Hospital Basel for the TotalSegmentator v2.0.1 source. [Source and license notices](../../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md)

| Export | SHA-256 | Verification |
| --- | --- | --- |
| Active r01 | `27862cad9d34d1d7a7b86a1ce8d92014f5d7db534788c45cb4ef9fd1cce20089` | Clean output from the owner recipe matched the existing export byte for byte. |
| Disposable dome trial | `46005af25fb4c57dccdd737c07e0216fbde7bc2265f29651f88f11d6db89871f` | Replayed to fresh output and passed native hydrated `check-port` in the isolated source copy. Both exports contain 61,604 vertices, 123,204 triangles and 2,217,704 bytes. |

- **Candidate.** From the r01 vertices, take the highest on-grid vertex at each integer XY location and extend into empty columns by nearest neighbor. Smooth this height field with a Gaussian of sigma 1.65 voxels. Interpolate the height correction at each vertex, clamp to ±⅔ voxel, ramp its weight from zero at z=239 to one at z=247, and taper to zero three voxels below the roof. Apply only along z and serialize to the original float32 format. Face indices remain identical. Scientific runtime used NumPy 2.2.6, SciPy 1.16.1 and scikit-image 0.25.2.
- **Reference.** Extract the unsmoothed 0.5 isosurface of the binary source mask. Globally sample vertices, edge midpoints and triangle centroids. For each section, intersect the triangles with the plane and sample at intervals of at most 0.15 mm. Use the larger of the two directed nearest-sample p95s and the larger maximum. These are sampled estimates. The frame cuts are clipped to the rendered sector. The sparse global and dense section samples can produce different maxima. [r01 measurements](replay-r01-metrics.json) · [Candidate measurements](dome-trial-metrics.json)
- **Sector maxima.** The largest baseline errors go from the source contour to the delivered mesh. On frame 12 the worst source voxel position is approximately (179.91, 154.09, 216.50), 58.73 mm inside the sector. On frame 13 it is (179.61, 154.39, 216.50), 59.02 mm inside. Comparing those points with the full unclipped mesh cuts still gives 7.870 and 9.105 mm respectively. A smaller frame-12 mesh-to-source discrepancy near the sector edge fell from 1.466 to 0.211 mm when unclipped. The two large values describe interior cross-section differences. A stronger anatomical claim needs inspection of that location against the case.
- **Dome.** Evaluate roof height on the same 5,351 mask columns for both meshes. The RMS residual from a local Gaussian trend fell from 0.357 to 0.123 mm. This measures surface texture. No new observation establishes a higher teaching score.
- **Playback.** Reassembled a baseline from the retained regional stage. Rebuilt the liver through the normal track builder against the disposable native pin, then assembled a separate delivery. Loopback Chrome for Testing 158 fetched each expected liver SHA once per session. Both sessions decoded the frame-12 acquired reference (SHA-256 `dab415d831ea2027a65f11c8b7cc63180d8e094629fdc3e4dd66d9c8de9f5540`), showed WebGL, and decoded scan and overlay at both frames with zero page errors. Compared all 98 local scan/overlay payloads and the 49-pose sweep file byte for byte.
- **Audit boundary.** The [inventory and review counts](audit.json) describe the baseline assembly. Each authored row was counted once after validating its retained review package and matching its expanded form against the assembled copy. Only the liver received detailed tracing. No new acquisition, learner study, specialist assessment or full campaign audit was performed.

The candidate binary, fresh deliveries, scripts and intermediate captures are local under `.artifacts/us-liver-pretrial/`. The retained decision, metrics and three matched views document why the candidate was held.
