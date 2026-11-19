# Follow one circuit through the heart

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../sites/body-systems-survey/README.md#restore-the-media).

Open [the editable scene](cardiovascular-loop.blend) or [the portable GLB](cardiovascular-loop.glb). The front view reads from the patient's right to left. Start at RA and follow the arrowheads. The diagram uses static end-diastolic blood-pool shapes from the Cardiac Atlas as chamber landmarks. Ivory annuli and leaflets mark valves. Teal and ochre three-branch symbols mark the two vascular beds.

1. From the right atrium (RA), cross the tricuspid valve into the right ventricle (RV). Cross the pulmonary valve and follow the blue pulmonary arterial bridge to the lung bed.
2. Follow the rust pulmonary venous return to the left atrium (LA). Cross the mitral valve into the left ventricle (LV).
3. Follow the aortic valve and systemic arterial route to the body bed. The blue systemic venous bridge represents return through the vena cava to RA.

In the object list select a chamber, valve annulus, individual leaflet, bed branch, direction cone or bridge to isolate it. All **Bridge** objects, vascular beds, arrows and annotations are authored for this teaching layout. The blood pools, annuli and leaflets preserve the source shapes under rigid placement. Front-facing labels are intended for the anterior view. The [review](../../reviews/cardiovascular-loop/README.md) includes closer valve views.

## Why this assembly

The [native Cardiac Atlas](../../heart/Cardiac_Atlas/docs/README.md) supplies four closed chamber pools, four native valve sets and proximal vessels. Their original frame remains available for heart orientation. Valve planes overlap in a frontal view of the intact heart, and its vascular routes end before either capillary bed. The Workshop [heart, aorta and pulmonary venous exteriors](../../body/anatomy-workshop-r1/README.md) use a separate case frame. The frontal candidate render showed extensive overlap at the heart, with only a small portion of the sampled vein visible. The [venous context review](../../lessons/pulmonary-vein-context/README.md) documents that only one mask component was retained. Registering the models would require inferred ostia and still leave gaps in the circuit. The Z-native [arterial subset](../../models/aortic_tree_z/exports/r02/README.md) also ends at open rims.

This exploded scene reuses the Atlas chamber and valve surfaces and exposes their connections through authored bridges. It serves the body-systems survey. The assembly owns the recipe, scene and portable export. Its review owns six clean-import screenshots and their bindings. No existing consumer needs to migrate.

## Source, scale and replay

The original procedural [Cardiac Atlas](../../heart/Cardiac_Atlas/docs/README.md) is the source of both ED JSON mesh inputs. [Placement data](placement.json) pins their exact bytes and records each rigid placement in source Blender units. Translate chamber coordinates by the listed vector. For each valve subtract the native pivot, rotate about Y by the listed angle and add the diagram pivot. Multiply by 0.025 for Blender metres. Blender axes are +X patient left, +Y posterior and +Z superior. The GLB is in metres, with +Y superior and +Z anterior. The horizontal spacing, blood-pool ports, axes of the separated valves, vessels and vascular beds are illustrative. Distances between landmarks and the bridges through the valve planes have no physiological interpretation.

The circuit order follows the [US National Heart, Lung, and Blood Institute's blood-flow description](https://www.nhlbi.nih.gov/health/heart/blood-flow). The pulmonary outflow stands for trunk and pulmonary arteries. Each return stands for its vessel group. This is an introduction to gross circulation, with no chamber wall, fused open lumen, vessel calibre, perfusion, gas-exchange, valve motion or disease model. Workshop, TotalSegmentator and Z-Anatomy geometry was screened only. Retain the Atlas provenance on derivatives. The Atlas documentation supplies no standalone redistribution grant for this derivative.

From the repository root, with hydrated sources and Blender 5.2.3:

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python assemblies/cardiovascular-loop/build.py -- .artifacts/cardio-build-new
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python tools/render_teaching.py -- --glb .artifacts/cardio-build-new/cardiovascular-loop.glb --views assemblies/cardiovascular-loop/views.json --output .artifacts/cardio-render-new
python3.12 assemblies/cardiovascular-loop/check.py .artifacts/cardio-build-new .artifacts/cardio-render-new
```

Both build and render require a fresh output directory. The GLB and placements replay byte-identically on the tested Blender build. Native Blender save bytes vary across output directories.
