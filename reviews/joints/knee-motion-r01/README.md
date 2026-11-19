# Right knee motion review

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Editable study, source identities, placements and attribution](../../../assemblies/skeletal-teaching/knee-motion-r01/README.md). The final GLB SHA-256 is `3702f9ed5aaa3a4b41945a548eb95843ea24b9d7a4941a160128a3ea9b1a76ea`. The delivered BLEND SHA-256 is `3e19dc928aec196fed47c877c27339958fb2184d92b4691cbddb1dd82e17c0fc`.

| View | Straight orthographic | Isometric |
|---|---|---|
| Comparison at one scale, source at left and +20° flexion at right | [Lateral](poses-ortho.png) | [Oblique](poses-iso.png) |
| Source pose landmarks | [Anterior](source-ortho.png) | [Oblique](source-iso.png) |
| Flexed pose landmarks | [Anterior](flexion-ortho.png) | [Oblique](flexion-iso.png) |

**Technical passed.** Two fresh builds reproduced the GLB bytes. The native Blender container varies between saves. Clean reimport matched all retained interior source vertices (excluding the two shaft-cut planes) against expected placement for femur, tibia and fibula. Maximum nearest-vertex error was 0.000068 mm. Cone tips point along their prescribed qualitative vectors in both poses. Removing the flexion rotation from a scratch GLB made the independent checker reject the tibial landmark placement.

| Clean-import measure | Source | +20° flexion |
|---|---:|---:|
| Femur/tibia intersecting triangle pairs | 0 | 0 |
| Nearest sampled lateral plateau to femur | 4.81 mm | 4.58 mm |
| Nearest sampled medial plateau to femur | 0.32 mm | 1.14 mm |
| Fibula to femur minimum sampled separation | 20.45 mm | 17.76 mm |

The checker samples proximal tibial source vertices above Z=0.416 m, splitting medial/lateral at X=−0.077 m. Values below 6 mm keep both sides within approximately 1.2 mm of the source's largest compartment gap. These are mesh distances only. The 6 mm screen is specific to this teaching asset. In a preliminary axis screen, a more anterior pivot at Y=0.025 m caused 22 overlapping triangle pairs in flexion. Moving it 5 mm posteriorly eliminated overlap while retaining both plateau regions under the distal condyles.

**Visual passed with limitations.** Inspected all six clean-import images. Both pose labels and arrowheads read in the matched lateral comparison. The tibia and fibula move together. The anterior views expose both condyles and the tibial plateau, including the lateral fibular head. In oblique views the nearer bone conceals portions of the joint cleft and the labels are foreshortened. [Render identities, visible objects, matched camera scales and image hashes](renders.json).

**Anatomy reference-screened.** The bone landmarks and posterior direction of flexion agree with the cited gross-anatomy references. Qualitative arrows describe loading direction. Surface clearance does not establish cartilage contact, force transmission, measured motion or specialist approval.

**Runtime unverified.** Blender imported and rendered the portable export. Interactive browser performance was outside the check.
