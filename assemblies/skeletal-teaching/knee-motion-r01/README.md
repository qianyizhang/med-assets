# Right knee · tibiofemoral flexion

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Open the two-pose GLB](knee-motion.glb) or [edit the Blender source](knee-motion.blend). Look at the right knee from its lateral side. The left panel retains the source pose. The right panel keeps the femur fixed and rotates the tibia and fibula 20° further into flexion. The tibial shaft moves posteriorly and the fibular head stays lateral. Select the pose's named hinge in Blender to inspect the change. The two labeled endpoints are the measured scope.

The rust arrow points distally along the thigh and the blue-green arrow points proximally along the lower leg. These offset arrows illustrate opposing compressive load directions on the femur and tibia. The arrow lengths carry no force or stress magnitude. Open the [matched views and measurements](../../../reviews/joints/knee-motion-r01/README.md).

## Source and placement

The [22-mesh right knee](../../../models/joints/exports/z-knee-r01/README.md) and its [inspection gallery](../../../gallery/knee-inspection/r01/README.md) preserve a static study of bone and soft tissue. Selective reuse preserves both the gallery's exact mesh bindings and the existing inspection recipe. This assembly reuses the distal femur, proximal tibia and proximal fibula. The shaft cuts at native Blender Z=0.550 and 0.318 m expose the joint region at a common scale. The assembly owns one portable export, one editable scene and its geometry check. Its review retains three matched pairs for the body-systems survey.

Source GLB SHA-256 `6dcc793e4132e62e4962e504bef0d595bb2e7d3a31881137244f31eadbb53aad`. Source units are metres. Native Blender +X points to patient left, +Y posterior, +Z superior. The export maps (x,y,z) to glTF (x,z,-y). The source panel retains the atlas placement. The flexed panel is translated by (0,−0.175,0) m for display. Its tibia and fibula turn together +20° about the native X axis through (−0.077,0.030,0.452) m before that translation. This authored axis passes through the distal femoral region. A fixed-axis schematic omits condylar rolling/gliding and coupled axial rotation. The pose angle is relative to the source. Cartilage, menisci, capsule, ligaments, patella and extensor mechanism remain outside this bone-surface example. Refer to [OpenStax's knee joint description](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-6-anatomy-of-selected-synovial-joints).

Use the separate [whole skeleton](../../../models/skeleton/exports/source-candidate-03/README.md) for orientation. Its 271 representation meshes comprise 206 bone-category meshes, 37 cartilage/disc meshes and 28 dental-context meshes. Those counts describe atlas organization. The native Z-Anatomy knee and BodyParts3D skeleton have separate frames.

## Attribution and replay

Z-Anatomy, *Models of Human Anatomy*, with upstream BodyParts3D / The Database Center for Life Science attribution. The adapted geometry and rendered images retain CC BY-SA 4.0. See the [source attribution and license links](../../../models/joints/exports/z-knee-r01/ATTRIBUTION.md). Changes comprise bone selection, planar shaft sections, matte colors, labels, arrows and rigid pose placement.

From the repository root with Blender 5.2.3 and the hydrated source GLB:

```sh
blender -b -t 1 --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/skeletal-teaching/knee-motion-r01/build.py -- .artifacts/knee-motion-new
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/skeletal-teaching/knee-motion-r01/check.py -- .artifacts/knee-motion-new/knee-motion.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/knee-motion-new/knee-motion.glb --views assemblies/skeletal-teaching/knee-motion-r01/views.json --output .artifacts/knee-motion-images-new
```
