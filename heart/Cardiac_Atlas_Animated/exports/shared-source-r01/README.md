# Cardiac Atlas shared teaching source

Open the [editable Cardiac Atlas](../../Cardiac_Atlas_Animated_Source.blend) to edit the aorta, chamber walls and other structures in one native scene. These two Gallery lessons share the same aorta and full left ventricular wall in the atlas coordinates.

| Learner task | Export | Contents |
| --- | --- | --- |
| Distinguish the pulmonary trunk from the aortic arch | [cardiac-static-ed.glb](cardiac-static-ed.glb) | Complete clinical-color atlas at end diastole. The Gallery can isolate the arch, pulmonary trunk and the two pulmonary arteries. |
| Distinguish ventricular contour change from a rigid shift | [ventricular-wall-motion.glb](ventricular-wall-motion.glb) | Left ventricular wall, fixed aorta, and one 0.8-second authored morph clip. Use the static lesson for external landmarks or the complete original animation for synchronized context. |

The package uses the original procedural Cardiac Atlas geometry and the edition's packed Blender rig. It adds no donor geometry or fused surfaces. The same-source vessels, walls and authored valve geometry retain their placement. Some source vessel and valve junctions overlap or leave visible gaps. The two exercises address external position and a schematic deformation. Neither exercise demonstrates lumen continuity or measured motion.

## Coordinates and source

The native Blender frame uses +X patient left, +Y posterior and +Z superior at 25 mm per Blender unit. The GLBs convert this to +X patient left, +Y superior and +Z anterior, with a common metre conversion at the scene root. The source's end-diastolic frame 1 maps to both the static pose and the animation's 0 seconds. Blue and red are circulation colors for teaching.

The original procedural atlas supplies the geometry and rig. Its [anatomy references](../../../Cardiac_Atlas/docs/README.md#anatomy-references) are creditable references for orientation and educational relationships. They supply no copied geometry to these exports. No separate public license is declared for the authored Cardiac Atlas package. Independent Workshop, scan-derived and atlas alternatives retain their [separate origins](../../../README.md).

## Rebuild

From the repository root, use Blender 5.2.3 and a fresh output directory.

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python heart/Cardiac_Atlas_Animated/recipes/shared-source-r01/build.py \
  -- --out .artifacts/cardiac-replay --full-model
```

The [recipe](../../recipes/shared-source-r01/build.py) exports the static pose before baking the selected motion. The two clinical-color files omit unused UV coordinates. The baked-texture atlases and packed native UVs remain available through their original deliveries. Omit `--full-model` to write only the two teaching GLBs. The full-model flag adds a complete animated GLB for reimport and review.

[Exact assessments and matched views](../../../../reviews/teaching-assessments/2026-11-23-cardiac-shared-source/README.md)
