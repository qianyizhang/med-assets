# Pancreas r02 is adopted for 3D orientation

The abdominal survey opens the s1233 exterior at frame 12. Rotate it to locate the broad head, hooked uncinate region, body and tail. The default oblique scene partly obscures the head behind vessels; the axial scene and isolated reverse view help distinguish the regions. The standalone sweep uses the same native export. The separate limited-pancreas visit and pancreatic tail chapter keep their worked acquisitions. [Package and replay](../../../../../../models/pancreas_s1233/README.md) · [Lead review and matched images](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-r02/reviews.json)

**Decision.** The user approved an exemption for this exact mesh and exterior-orientation task after reviewing the [contour trial](../contour-trial/README.md). The original full raw-label test still fails. Exact scan-contour tracing, caliper measurement and internal anatomy remain unqualified. An independent post-patch visual audit lowered the builder's proposed form score from 3 to 2 — setting final scores to **3/2/3/4** for fidelity, form, readability and economy — because `r02` only adds two 6 mm local patch pulls on top of `r01` and retains the same corrugated inner-border relief; a second view also helps identify the uncinate turn. The earlier r01 assessment retains its original scope and scores.

| Comparison | Measured result | Interpretation |
| --- | --- | --- |
| Whole 3D exterior against the filled label | Worst bidirectional sampled p95 **0.66 mm**, max **2.44 mm** | Passes the original 1.5 / 3 mm distance limits for whole-organ shape. Three excluded internal mask gaps have 22, 16 and 4 voxels. Their anatomical meaning is unresolved. |
| Tail, neck and uncinate region | Maximum **2.09 / 1.12 / 2.41 mm** respectively | All three protected regions stay within the 3D limit. |
| Three frozen cuts through the filled exterior | Full-cut maxima **1.98 / 2.65 / 1.52 mm** | The two source-anchored corrections restored the targeted grazing intersections. |
| Four interleaved exterior cuts | In-plane maxima **9.64 / 4.45 / 1.74 / 4.02 mm** | At the three failing maxima the nearest 3D surface is **0.87 / 0.91 / 0.77 mm** away. The final miss lies on the main contour. These local section errors still matter for tracing. |
| Original raw half-label | Whole-surface maximum **7.58 mm**; saved-section maximum **10.18 mm** | The original gate exits 1. Filling the exterior does not reproduce the source's internal loops. The overlay and simulated scan continue to use the original source. |
| Integrity and teaching scale | One outward shell, Euler 2, zero degenerate or intersecting faces, volume **+0.22%**, turning silhouette **0.79 px** | The 5,800-triangle mesh uses 104,432 bytes, about 65% less than the previous 16,620-triangle sweep. |

## Replay and checks

Use the [package recipe](../../../../../../models/pancreas_s1233/README.md) with `--revision r02` and the pinned case. Two fresh replays produced SHA-256 `16919fa7975eca4d8e3b2c0de47d30490b823810daa2b8878d6baab432bc6b96`. A default r01 replay reproduced its earlier digest. The refined coordinates are the exact source-anchored trial bytes.

Run the existing [measurement command](../../spleen/measure.py) with the original frozen reference, previous compact sweep, packed r02 mesh, dense replay and `--pancreas-case`. Preserve its nonzero exit and failures. Then run the narrower test in the same Python environment with the study on `PYTHONPATH`:

```sh
python3.12 records/campaigns/ultrasound-refinement/wave-2a/pancreas/orientation-r02/verify_orientation.py \
  "$S1233_CASE" models/pancreas_s1233/exports/r02/pancreas.mesh "$MEASURED/measurements.json"
```

The [orientation checker](verify_orientation.py) reuses the frozen distance, topology, volume, triangle and silhouette limits with the declared exterior reference. It checks each protected region and recomputes the 3D error at the worst point in each direction on the interleaved cuts. The adopted export passes. A disposable copy shifted 12 mm fails the 3D checks. The [measurements](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-r02/measurements.json) retain the full raw failure, orientation results, exact browser responses and scoped chapter digest.

The Gallery retains the earlier r01 card and labels r02 as the adopted exterior. It reports six governed chapters out of 410, seven review cards and zero four-axis qualifications. Build products and browser captures are retained locally under `.artifacts/us-pancreas-r02/`.

Tested locally from `c9e52e38` plus the adoption changes. AssetKit sync, hydrated check-port, native show/impact, the chapter bundle, validation, economy, review check and all 83 AssetKit tests passed. The workbench displayed the current r02 scores and resolved the earlier r01 review as prior. The compact assembly, organ playable and case data/geometry checks passed, including 46 assembly rejection paths. Chrome exercised all four abdominal cases and all 28 standalone sweep routes. Only the pancreatic primary mesh and the named survey chapter changed. All 2,930 compared frame images and pose files matched the preceding delivery. With the study server stopped, Chrome verified the seven Gallery cards, their evidence images and exact downloads. Repository offline and hydrated payload-integrity verification passed.
