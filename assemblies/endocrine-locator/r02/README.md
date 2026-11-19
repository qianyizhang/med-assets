# Regional endocrine teaching groups

Use the posterior atlas neck to find four parathyroid landmarks. Use the
s1233 models to examine the thyroid and central airway, or the two adrenals
with kidney and pancreas context in their shared scan frame. The
[head-to-pelvis locator](../r01/README.md) still provides the hormone route,
the enlarged islet and the two gonad examples.

| Portable file | Editable group and use |
| --- | --- |
| `atlas-neck-posterior.glb` | Select the four ochre parathyroids by side and level against the rose thyroid. Uses the original r01 atlas placement. |
| `s1233-thyroid.glb` | Select the thyroid label and airway separately. The label qualifies as a regional source reference with two substantial components and three retained single voxels. |
| `s1233-adrenals.glb` | Select either adrenal, either kidney or the pancreas. The kidneys and pancreas provide muted context. The visible separations preserve the source labels. |

Each has a same-named editable BLEND. Select by object name or
`extras.anatomy_id` on import. The atlas and scan files have independent
frames. There is no atlas-to-scan registration. In the same-case files,
`(-R, 155 - A, S - 430) / 1000` converts NIfTI RAS millimetres to Blender
metres, with +X left, +Y posterior and +Z superior. glTF uses +X left, +Y
superior and +Z anterior. The atlas posterior view represents one four-gland
example. Its visible midline projection retains the
[source review qualification](../../../models/parathyroids/exports/z-localization-r01/README.md).

For the gallery close-up, the [smoothed adrenal group](../adrenal-study-r03/README.md) preserves this scan frame and records per-organ deviations from the r02 surfaces.

## Source and replay

The atlas subset preserves the original world placement and the
[Z-Anatomy and BodyParts3D notices](../../../models/parathyroids/exports/z-localization-r01/ATTRIBUTION.md)
under CC BY-SA 4.0. Changes are named selection groups and display materials.
The separate scan derivatives retain the
[s1233 Workshop source terms](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md).
Credit Jakob Wasserthal, TotalSegmentator contributors and University Hospital
Basel. The surfaces follow binary label contours with limited smoothing and
retain the source components. [Exact inputs](inputs.json) ·
[Part and render review](../../../reviews/endocrine-locator/r02/README.md).

Restore the r01 locator GLB with the
[teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).
Set `S1233_MASK_DIR` to the retained s1233 NIfTI segmentations. Use the
[Workshop Python stack](../../workshop-s1233/README.md#source-and-build) and
Blender 5.2.3. On macOS get command-specific approval before the first
headless Blender invocation. Run from the repository root with fresh paths.

```sh
prepared=.artifacts/endocrine-mask-replay
out=.artifacts/endocrine-replay
python3.12 assemblies/endocrine-locator/r02/prepare.py \
  --masks "$S1233_MASK_DIR" --output "$prepared"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/r02/assemble.py -- \
  --prepared "$prepared" --output "$out"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/endocrine-locator/r02/render.py -- \
  --models "$out" --output "$out/renders"
```

`mask-audit.json` records byte pins, affine, boundary margins, mask
components, label distances and smoothing displacements. `geometry.json`
binds the model outputs to the audited inputs. Use the rear orthographic
atlas comparison and the independently framed scan views.
