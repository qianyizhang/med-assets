# Pulmonary-vein context — reviewed v2

V2 passed independent static presentation review at
`84ae02a46d3b86d2382893b5fc9e267f862b50bb`. The reviewer verified all 38 evidence
entries and inspected the actual revised teaching pixels, confirming overview
margin, matched cameras, detail locator, side labels and largest-component scope.
The unchanged detail, grayscale and source-binding review remains applicable.
This does not establish anatomy, clinical or browser approval.

The [teaching sheet](../../../lessons/pulmonary-vein-context/pulmonary-vein-context.png)
is the exact reviewed PNG, SHA256
`7e48448afb63ac42df1dc281cf939c3a9783acc75fdca877a9c65e2abcfc4bac`.

Independent v1 review verified all 38 bundle entries and inspected the teaching,
overview/detail comparisons and grayscale. It confirmed the source-bound
left-sided coverage/context and identified one blocking finding: the lower
overview lung touched the frame (0.20 px projected margin).

V2 widens the overview camera from 0.36 to 0.40 m and recentres its height from
0.065 to 0.050 m. Both isolated/context states use that same camera. Context
margins are left 105.88, top 70.12, right 129.60 and bottom **68.93 px**. The detail
rectangle is recomputed from the unchanged detail camera; no geometry moved.
Both detail source PNGs and the standalone detail comparison PNG are byte-identical
to v1. Source inventories and lighting/material settings are unchanged.

- `render.json`: exact input identities, unchanged decoded coordinates/faces,
  source mapping, posterior orientation witness and four matched native renders.
- `build.json`: deterministic embedded-image composition and detail-locator bounds.
- `visual-binding.json`: all eight comparison/teaching panels preserve native
  source pixels outside editorial side labels and the detail locator.
- `checks.json`: scoped eleven-test result, v1 review, v2 reuse and separate gates.

The source raw mask remains unavailable; its recorded four components do not
identify four veins. This change preserves the retained example and introduces
no missing components, repairs, branch names, flow or lumen claim. The source-case
heart is context only and does not modify the active authored-heart work.

V1 remains in Git and private evidence history. Browser runtime and anatomy/clinical
gates remain unverified. Draft delivery reuses the reviewed pixels and scoped
checks. The required offline PR gate passed 200 tests, 26 transport manifests,
25 foundation records, 591 import references and 691 LFS pointer identities.
Its first run exposed a test import-path issue; the test now resolves the
repository root under both entrypoints. No generator or pixel change was needed.
Hosted CI and remote evidence delivery remain separate PR results.
No merge or Site publication is part of this change.
