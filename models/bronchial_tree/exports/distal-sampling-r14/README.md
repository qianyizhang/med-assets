# Bronchial tree distal sampling r14

The loopback Anatomy Gallery uses [bronchial_distal_sampling.glb](bronchial_distal_sampling.glb) to teach tracing the first fork from the trunk into both main branches. This is the exact [AG-GAL-021 trial export](../../../../reviews/bronchial_tree/2026-11-21-distal-simplification-trial/README.md), adopted as-is under a durable filename and Library revision.

| Export | Bytes | Triangles | SHA-256 |
| --- | ---: | ---: | --- |
| Distal sampling r14 | 7,401,328 | 308,288 | `f8d78751f47cf14311138a3c7e2e35d6e28415c9f6e1d2a0e4f6ca2bf1a07fc9` |
| [Original r13](../authored-central-fairing-r13/README.md) | 10,655,808 | 443,892 | `c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587` |

The derivative reduces bytes and triangles by 30.5%. The central Y, both lobar neighborhoods and all 16 terminal neighborhoods retain their exact incident triangles and encoded normals. At 1000 × 850, the three central comparison masks match and the largest outline shift is 1.41 pixels on a distal crossing. The maximum sampled bidirectional surface difference is 0.15249 mm. The tree remains an authored schematic with closed terminal caps, an angular asymmetric underside and a right collar and pocket. The review covers first-fork teaching at the measured views. The whole model remains **Needs revision** and has no anatomical, lumen or clinical validation.

## Recover the exact export

Run from the repository root. If this path contains a pointer and the local object is present, hydrate it with:

```sh
git lfs checkout models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb
```

If the local object is absent, use the [distal simplification recipe](../../recipes/distal-simplification-trial/README.md#replay) with the exact hydrated r13 control and a fresh output directory. Verify that the recipe's `bronchial_distal_trial.glb` matches the r14 size and SHA-256 above. Copy those verified bytes to the r14 export path when it is absent or holds its original pointer. The preview serves the restored bytes at the existing asset URL. **Retry 3D** opens them from the first-fork stop. The [review ledger](../../../../reviews/bronchial_tree/README.md#source-chain-and-technical-limits) retains the r07 → r09 → r13 replay chain.

## Attribution and delivery

The [r13 source attribution](../authored-central-fairing-r13/ATTRIBUTION.md) applies. The original schematic used display lung bounds derived from TotalSegmentator case s1233. Retain attribution to Jakob Wasserthal, the TotalSegmentator contributors and University Hospital Basel under CC BY 4.0. The derivative reduces lateral surface sampling. Its authored routes and terminal closures carry forward from r13. No separate public license is declared for the authored geometry.

The exact r14 Library route is `/#/library/bronchial_tree/distal-sampling-r14`. The original saved r13 comparison and export remain available and the 11/16 assessment stays on r13. See [AG-GAL-023](../../../../records/work-items/items/AG-GAL-023-adopt-bronchial-distal-sampling.md) for local verification and the remaining release decisions.
