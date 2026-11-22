# Bronchial distal sampling trial

The first-fork comparison stays beside this review. The eight supplementary sheets are in the [bronchial trial archive](../../../transport/README.md#restore-an-archived-collection). Restore `bronchial-trial-plates` to inspect the named files in `evidence/`.

**The lighter GLB is the local first-fork teaching default.** It saves **3,254,480 bytes and
135,604 triangles** (30.5% each). At the existing teaching scale, the eye can
still follow the trunk into both main branches. The closest reviewed evidence
of a cost is a 1.41-pixel outline shift at a distal foreground crossing.
[AG-GAL-021](../../../records/work-items/items/AG-GAL-021-simplify-bronchial-distal-sampling.md)

| Export | Bytes | Vertices | Triangles | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| r13 control | 10,655,808 | 221,948 | 443,892 | `c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587` |
| `bronchial_distal_trial.glb` | 7,401,328 | 154,146 | 308,288 | `f8d78751f47cf14311138a3c7e2e35d6e28415c9f6e1d2a0e4f6ca2bf1a07fc9` |

## What changes at teaching zoom

The overview locator (`locator.webp`) marks the first fork and the
accepted left lobar fairing. The six paired neutral renders use the same
1000 × 850 viewport, orthographic scale, material, lighting and exposure within
each pair. The three-light setup uses the original framing and neutral material
values. Its transparent background permits an alpha-based measurement.

| Matched pair | Foreground overlap | Worst outline shift | Inspection |
| --- | ---: | ---: | --- |
| Whole exterior (`whole.webp`) | 99.692% | 1 px | The trunk and both main branches lead to the same visible distal routes and tips. |
| Reverse whole (`reverse-whole.webp`) | 99.701% | 1 px | The reverse direction exposes the overlapping routes and shows the same branch attachments. |
| [Neutral first fork](evidence/close.webp) | 100% | 0 px | The Y contour, reduced dimple and trunk split read alike. |
| Opposite first fork (`opposite-close.webp`) | 100% | 0 px | The reverse collar reads alike. |
| Rotated underside (`rotated-close.webp`) | 100% | 0 px | Both views retain the angular, asymmetric underside. |
| Left lobar fairing (`left-lobar-close.webp`) | 99.923% | 1.41 px | The softened lobar blend reads alike. The narrow foreground branch has a slightly flatter contour and a muted highlight at the crossing. |

Overlap is foreground intersection divided by union at 50% alpha. The shift
is the largest bidirectional nearest-foreground distance in native pixels.
The 4x outline crop (`worst-silhouette.webp`) shows the shift at
pixel (873, 506), on the foreground branch crossing at the right side of the
left lobar view. The 4x shading crop (`worst-shading.webp`) shows the
largest mean absolute luma difference in a fully opaque 9 × 9 pixel patch
near (818, 640) along the same foreground branch. It measures 4.26 of 255 code
values and includes render sampling variation. The main lobar junction lies
left of the crossing in the full view. The whole-view outline shift stays
within one native pixel on both sides.

## Geometry and replay

- The decoded scene retains one mesh, one primitive, the same material and
  authored metadata. Both clean imports retain the same identity transform
  and bounds, with one consistently oriented closed component, Euler
  characteristic 2 and zero degenerate faces at the checked area tolerance.
  Signed enclosed volume changes by −0.176%.
- Exact position matching and oriented triangle comparison verify every
  incident triangle at the 16 established 6 mm terminal neighborhoods, both
  12 mm lobar regions, and the central ±28 mm slab. All surviving encoded
  normals match r13. The protected center includes 142,757 incident triangles,
  and the accepted left blend includes 22,797.
- Nearest-triangle checks sample every vertex and face center in both directions.
  The maximum is **0.15249 mm** (r13 to candidate), on the authored distal
  left-lower group near (109.03, 3.15, 6.15) mm in Blender coordinates.
  The reverse maximum is **0.14672 mm**. These are sampled surface distances.
  [Geometry receipt](geometry.json)
- The input identities agree with the [r07 → r09 → r13 source chain](../README.md#source-chain-and-technical-limits).
  The [candidate recipe](../../../models/bronchial_tree/recipes/distal-simplification-trial/README.md)
  replayed byte for byte from exact r13. Blender 5.2.3 (`fab76e95306d`) clean-imported and
  rendered both files with 48 CPU Cycles samples. [Render bindings](views.json)
  [Pixel measurements and sheet hashes](pixels.json)
- A second capture produced byte-identical geometry and the same decoded RGBA
  pixels in all 12 renders. The PNG files carry run-specific metadata. The input
  and comparison commands rejected r09 substitution, an existing destination
  and a candidate with a corrupted normal while preserving the successful
  output. The pixel comparison refused a render paired with the wrong GLB
  digest. [Build receipt](build.json)
- The isolated offline gate on `29c02157b071dce7bf3fd1600af505eb3045d561` plus
  the trial passed 441 tests, 26 transport manifests, 25 foundation records,
  430 import references and 1,010 LFS pointer identities. Each of the nine
  local review sheets matched its recorded digest.

The candidate has been adopted as the exact [local r14 export](../../../models/bronchial_tree/exports/distal-sampling-r14/README.md).
Use the recipe to recover it from r13. The
[r13 attribution](../../../models/bronchial_tree/exports/authored-central-fairing-r13/ATTRIBUTION.md)
and the authored schematic's existing limits apply to the derivative. The
comparison covers saved geometry and the stated teaching task. Viewer
performance, anatomy and clinical use require separate evidence. The Gallery
retains the exact r13 export and its 11/16 assessment alongside r14.
