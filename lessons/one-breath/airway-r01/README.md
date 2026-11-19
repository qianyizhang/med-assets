# From the nasal cavity to an alveolar cluster

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[The route GLB](airway-route.glb) combines inspectable nasal, pharyngeal, laryngeal, tracheal, lobar and terminal sections. [The editable scene](airway-route.blend) retains the curves and individual landmarks. The **Follow the air** stage in [One Breath](../README.md) presents this route over the actual paired breathing lung models. Its upper, branch and terminal views isolate junctions. **Open gas exchange** leads into the existing O₂/CO₂ diagram.

## Geometry and admissions

| Segment | Evidence, placement and limits |
| --- | --- |
| Nasal passage through pharynx | The [NIH nasal airspace](../../../models/nose_sinuses/recipes/nih3d-airspace-r01/README.md) represents a cast with uncertain metric axes, including sinuses. The route needs one exposed passage to the pharynx. A new schematic sagittal lateral wall, three conchal shelves and an exposed centerline show the nasal passage continuing posteriorly and inferiorly through the pharynx. |
| Larynx into trachea | The [BP3D study](../../../models/pharynx_larynx/exports/r03/README.md) supplies the epiglottis, thyroid and cricoid cartilages. The axial center of the inferior cricoid bounding plane is translated to the V7 proximal port. The airway through those landmarks is authored. Their unscaled relative placement is preserved. Disputed left/right muscle labels are outside the selection. |
| Trachea to left upper lobe | Reuse the lesson's exact V7 cutaway, centerline, carina and right/left port locations. A short bridge joins the V7 left opening to the start of the [Workshop](../../../body/anatomy-workshop-r1/README.md) left upper lobar bronchus. Its native authored shape and orientation are retained. The second main branch remains visible for context. |
| Smaller airways to exchange | After the lobar end, a compressed set of small-airway generations reaches the terminal bronchiole, respiratory bronchiole, alveolar duct and enlarged open alveolar cups. The model shows air-side progression. The second and third lesson stages distinguish air movement from gas transfer across the capillary barrier. |

[Inputs](inputs.json) binds the imported GLBs. [Placement](placement.json) records the sole external translation. [The lesson manifest](../assets.json) owns the spatial centerline points in glTF metres, +X patient left, +Y superior, +Z anterior. Blender +X is left, +Y posterior and +Z superior. Source and schematic scales differ, notably at the alveoli. No cross-patient registration, measured lumen, deposition, CFD or tissue-layer reconstruction is asserted.

The intended consumer is the existing One Breath lesson. The lesson uses its separately loaded V7 shell with this extension. Its scene hides the extension's V7 copy, which allows the exported GLB to stand alone without doubling walls in the lesson. Names, region tags and matched local views keep the editable recipe and one portable export usable at both scales. [Source attribution and rights](../licenses/ATTRIBUTION.md). The sequence was screened against [OpenStax 22.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system) and [22.2](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-2-the-lungs).

The [terminal airspace cutaway](../terminal-study-r02/README.md) is a standalone gallery detail. Select its airway regions to follow the open duct into the illustrated recesses.

## Replay

From the repository root with Blender 5.2.3, hydrated inputs and fresh output directories:

```sh
owner=lessons/one-breath/airway-r01
blender -b -t 1 --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/build.py" -- .artifacts/airway-route-replay
shasum -a 256 .artifacts/airway-route-replay/airway-route.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/check.py" -- .artifacts/airway-route-replay/airway-route.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb "$owner/airway-route.glb" --views "$owner/views.json" --output .artifacts/airway-route-views
python3.12 tests/review_records/validate_record.py reviews/one-breath/airway-r01/record.json
```

After [preparing the lesson](../README.md), run `node lessons/one-breath/airway-r01/check-phases.mjs` to compare all five lung lobes at rest and peak inspiration and check exact geometric recovery. [Evidence and gate results](../../../reviews/one-breath/airway-r01/README.md).
