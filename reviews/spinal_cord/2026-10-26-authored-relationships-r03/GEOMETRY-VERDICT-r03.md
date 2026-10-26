# Independent r03 geometry review

2026-10-26. **Pass for the tested authored-model geometry gates only.**

Exact candidate SHA256: `5d9f0f88ff8498f611aea583e080558691d592a3ce50c89ecb847cf18b4d1471`.

- Fresh GLB import:104 meshes. Exact-coordinate welding for analysis only gives1component/Euler2 and positive signed volume for every mesh,0non-two-face edges,0zero-area triangles.
-5151 unrelated root/mixed-nerve/filum pairs screened;0BVH triangle-overlap candidates. Samelevel, same-side dorsal/ventral/mixed-nerve convergence is the only nerve-group exclusion. Upper and descending groups are distinct; filum tested against every nerve group.
-68/68 dorsal/ventral root objects show actual triangle contacts with cord surface.
-28/28 recorded descending root start points are inside fresh cord geometry under3non-axis ray parity checks. Nearest actual exported root vertex is within0.480001mm, consistent with the authored0.48mm strand radius. This supports attachment rather than a floating start.
- Actually viewed matched before/after lower views plus candidate lower-oblique, whole and side. Conus/filum/descending-root distinction is visibly clearer; the separate reference/pixel reviewer owns the teaching-scope verdict.

Limitations: finite-precision BVH screening, not formal exhaustive intra-object self-intersection proof. Separate objects intentionally overlap at cord attachments and own-group nerve convergence. No anatomy, clinical, runtime or31-pair reconstruction certification. No candidate bytes were edited. Full local receipts and reproducible checker scripts are retained alongside the concise `r03-SUMMARY.json`.
