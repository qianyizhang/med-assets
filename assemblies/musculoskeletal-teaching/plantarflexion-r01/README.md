# Right calf, Achilles tendon and heel in plantarflexion

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Animated GLB](calf-plantarflexion.glb) · [Editable Blender rig](calf-plantarflexion.blend) · [Two poses, sampled deformations and attachment evidence](../../../reviews/muscle/plantarflexion-r01/README.md).

Use the side view to trace the medial and lateral gastrocnemius heads and soleus through the Achilles to the posterior calcaneus. In Blender select a named mesh and enter Local View to isolate it. Change the timeline from **Neutral** (frame 0) to **Plantarflexion 15 degrees** (frame 24). The shank stays fixed as the heel rises relative to the forefoot direction. Select the three distal meshes in the review's insertion view to inspect the scalloped tendon margin through both poses. The complete [whole-body atlas](../../../models/muscle/exports/z-anatomy-r02/README.md) supplies static orientation.

## Admission, coordinates and anatomy

The [2026-10-23 study](../2026-10-23/README.md) already has eight same-frame right-sided surfaces, a visible distal tendon margin and a talus to orient the ankle. The entire body atlas omits a coordinated Achilles/heel rig. Reusing the regional surfaces retains the static supplement and adds an independently inspectable regional pose to the survey. Exact input `e38e33c1d0ceb791e4a2ad676dedd7923f53b5ad8d7dc8b195202565609354ea`. The neutral pose preserves source coordinates. Measurements use Blender metres, +Z superior, −Y anterior and +X toward source left. Portable glTF uses +Y superior and +Z anterior.

[AAOS](https://www.orthoinfo.org/bodypart/foot-ankle/achilles-tendinitis/) and the [regional reference screening](../../../reviews/draft_muscle/2026-10-23-achilles-context/REFERENCE-CHECK.md) identify the calf–Achilles–posterior calcaneus chain. The two gastrocnemius surfaces and soleus approach the proximal tendon sheet. The distal tendon and calcaneus retain their inherited margins. Per-part attachment witnesses measure proximity on these surfaces. They do not establish fibre continuity or the precise enthesis footprint. The femur and proximal gastrocnemius origins are outside the scene.

The shank and hindfoot bones form the editable skeleton. The illustrative hinge passes through (−0.080, +0.051, +0.065) m along Blender X, positioned within the talar region after comparing tibia and fibula intersections. Tibia/fibula receive only shank weight and calcaneus/talus only hindfoot weight. A shared smooth height-dependent skinning weight bends soft tissue between z = 0.065 and 0.280 m. The low insertion moves with the calcaneus. The rig does not model subtalar motion, contraction physiology, load, sliding contact or volume preservation. Whole-body attachment validation and expanded rig coverage remain broader work.

## Rights and replay

Z-Anatomy CC BY-SA 4.0. BodyParts3D © The Database Center for Life Science, historical CC BY-SA 2.1 Japan. Kousaku Okubo, Gauthier Kervyn, Marcin Zielinski and contributors. [Attribution and change history](../../../reviews/draft_muscle/2026-10-23-achilles-context/ATTRIBUTION.md) and [full upstream license](../../../reviews/draft_muscle/2026-10-23-achilles-context/SOURCE-LICENSE.txt). This rig, adapted geometry and renders retain CC BY-SA 4.0. Changes include matte recoloring, two-bone regional skinning and one authored animation. No external illustrations included.

From the repository root with Blender 5.2.3, use fresh destinations.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/musculoskeletal-teaching/plantarflexion-r01/build.py -- .artifacts/calf-replay
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/musculoskeletal-teaching/plantarflexion-r01/check.py -- .artifacts/calf-replay/calf-plantarflexion.glb .artifacts/calf-replay/checked.json
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/calf-replay/calf-plantarflexion.glb --views assemblies/musculoskeletal-teaching/plantarflexion-r01/views.json --output .artifacts/calf-views
```
