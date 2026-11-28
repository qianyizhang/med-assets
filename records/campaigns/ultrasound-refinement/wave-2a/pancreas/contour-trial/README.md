# Pancreas contour trial

**Keep the existing survey chapter.** A local correction on the held r01 mesh recovered both targeted intersections of the pancreatic exterior with the scan plane. It left a 10.18 mm maximum discrepancy on the raw saved section. The discrepancy lies around enclosed gaps in the source segmentation. The CT label does not establish their anatomical meaning.

![Adjacent native CT slices and parallel oblique cuts at the two exterior misses](../../../../../../experiments/ultrasound-sweep/development/asset-reviews/pancreas-wave-2a/adjacent-contours.webp)

At the saved frame, the filled-label exterior cut picks up a 0.17 mm perimeter loop. At the same marker the r01 contour is 6.81 mm away in that plane, while the closest point on its 3D surface is 1.10 mm away. A parallel plane 1 mm deeper already cuts a detached loop on r01. The neighboring axial slices show a short projecting margin. This evidence supports comparing the exterior locally. It gives no basis for constructing a separate internal anatomical structure.

## What changed across the trials

All three disposable trials started with the same dense r01 replay. Each used two 6 mm-radius patches, a maximum permitted vertex displacement of 1.5 mm, and the same Blender reduction to 5,800 triangles. Both sites were chosen from the earlier frozen errors, so the three protected sections alone cannot demonstrate general improvement.

| Trial | Change | Worst full **exterior** section error at −1.5 / 0 / +1.5 mm |
| --- | --- | --- |
| Held r01 | Original replay | 3.15 / 6.81 / 1.52 mm |
| Half projection | Move nearby mesh vertices halfway toward the nearest filled-label surface | 3.34 / 6.81 / 1.52 mm |
| Full projection | Use the full local projection, with the same falloff | 1.98 / 6.81 / 1.52 mm |
| Source-anchored | Move a patch toward each frozen source marker from its closest dense-mesh point. The two center displacements are 0.44 and 1.04 mm. | **1.98 / 2.65 / 1.52 mm** |

Moving from mesh to source rounded past the second marker. Moving from source to mesh placed a small part of the surface across the plane. At the two original markers, the anchored trial reduced in-plane distances from 3.15 to 0.12 mm and from 6.81 to 0.32 mm. The maximum over each *entire* section is larger, as shown in the table.

Four additional filled-exterior cuts at −2.25, −0.75, +0.75 and +2.25 mm tested positions between and outside the protected planes. The largest distances were **9.64, 4.45, 1.74 and 4.02 mm** after the anchored edit. Only the +0.75 mm cut crossed below 3 mm. The raw-label whole-surface and saved-plane maxima remained **7.58 and 10.18 mm**. The frozen checker rejected all three trials. An exterior-only task would need its own predeclared reference and section criteria.

The anchored mesh replayed byte-for-byte twice. Reimport found one outward shell, Euler 2, zero degenerate faces and zero intersecting nonincident pairs. Volume changed +0.22% from the raw reference and the maximum turning-silhouette departure was 0.79 px across 24 directions. The matched overview and reverse clay views showed little visible change to the broad head and uncinate contour at teaching scale. The held r01 review retains its scores. [Measured results and identities](results.json) · [Original worker and lead decisions](../README.md)

The trial started at `4fd3b35c`. The anchored replay reproduced the mesh and the comparison WebP byte for byte. The replay rejected a modified dense r01 input, and the figure checker rejected a different mesh. The native review exposes the new witness and the held export still has zero consumers. AssetKit validation, the review register, 83 AssetKit tests, repository offline checks and hydrated payload integrity passed. Chrome opened the updated offline Gallery, decoded all five pancreas witnesses and verified the exact r01 download.

## Replay

Use the [pancreas package environment and r01 replay](../../../../../../models/pancreas_s1233/README.md), the pinned public s1233 case and the [Wave 2A freeze and verifier](../../spleen/measure.py). From the repository root set `S1233_CASE`, `R01_REPLAY` (containing the original dense and packed meshes), `FROZEN`, `BASELINE` (a compact study with the previous sweep), `BLENDER`, and a fresh `TRIAL` directory. Use the study directory on `PYTHONPATH`.

```sh
packet=records/campaigns/ultrasound-refinement/wave-2a/pancreas/contour-trial
python3.12 "$packet/trial.py" "$S1233_CASE" "$R01_REPLAY" "$TRIAL"
for variant in half full anchor; do
  d="$TRIAL/$variant"
  "$BLENDER" --background --factory-startup --disable-autoexec --python-exit-code 1 \
    --python models/pancreas_s1233/retopology.py -- "$d/smooth.npz" "$d/pancreas.mesh" || exit 1
  python3.12 "$packet/../../spleen/measure.py" evaluate "$FROZEN" "$BASELINE" \
    "$d/pancreas.mesh" "$d/smooth.npz" "$d/evidence" --pancreas-case "$S1233_CASE"
  # Each candidate is expected to exit 1 on the raw gate and write its measured failures.
done
python3.12 "$packet/inspect_cuts.py" "$S1233_CASE" "$TRIAL/anchor/pancreas.mesh" "$TRIAL/inspection"
```

The figure uses native axial slices through each marker and oblique cuts at ±0.75 mm around the failing plane. Oblique views interpolate the original CT for display. Gold contours use the filled mask's half-label surface. Perimeters and point distances use physical RAS millimetres. Sub-voxel measurements describe the mesh and interpolation precision on a 1.5 mm source grid. The recipe, compact results and figure are retained. Dense trial surfaces and full numerical reports stay in ignored scratch.
