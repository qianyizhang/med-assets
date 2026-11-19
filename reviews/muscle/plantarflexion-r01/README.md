# Calf–Achilles–heel · regional motion review

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Assembly and exact source](../../../assemblies/musculoskeletal-teaching/plantarflexion-r01/README.md). Two Blender 5.2.3 builds yielded GLB SHA-256 `cfb5242ba5daf9fe3ec176912e0c33e3d5efcf4aa23a1cfc306db35237c8a118`. Editable BLEND SHA-256 `06149c74f9a50d7c5cd9505324b17f61b16069854b3ccd32fb62214b0605b43a`.

| Pose and selection | Side | Isometric |
|---|---|---|
| Neutral · whole leg segment | [Neutral lateral](neutral-ortho.png) | [Neutral oblique](neutral-iso.png) |
| 15° plantarflexion · whole leg segment | [Flexed lateral](plantarflexion-ortho.png) | [Flexed oblique](plantarflexion-iso.png) |
| Neutral · tendon and hindfoot | [Neutral insertion](neutral-insertion-ortho.png) | [Distal margin](neutral-insertion-iso.png) |
| 15° plantarflexion · tendon and hindfoot | [Flexed insertion](flexed-insertion-ortho.png) | [Distal margin](flexed-insertion-iso.png) |

**Technical.** [Five-pose measurements](verified.json) compare frames 0, 6, 12, 18 and 24 after clean GLB import. The neutral surface vertex sets match the static source bidirectionally within 0.01 mm. The final calcaneus follows the prescribed 15° transform within 0.01 mm and tibia/fibula stay fixed. Four fixed source landmark pairs track both gastrocnemius heads, soleus and the distal tendon insertion throughout motion. The distal pair remained 0.085 mm apart. The largest proximal separation was 0.285 mm at the lateral head. Final soft-tissue edge lengths ranged from 0.873 to 1.112 times neutral. Calf muscle vertices moved by up to 15.13 mm. Measured lengths are skinning diagnostics, with no physiological strain interpretation.

An initial pivot introduced 21 tibia–talus intersecting triangle pairs at 15°. Repositioning the hinge within the talar region reduced that count to zero at all five sampled frames. The inherited fibula–talus overlap decreased from 31 intersecting triangle pairs to 19, 4, 0 and 0. This count is a surface diagnostic. The source retains neutral interpenetration and lacks a validated articular-contact model.

**Visual.** The lateral pair shows a changed posterior tendon angle and hindfoot rotation. Distal isolation keeps the insertion visible in both poses. The oblique view exposes the broad tendon surface. The inherited thin profile and scalloped distal seam remain visible. [Camera, scale, visibility and screenshot hashes](renders.json). The source's earlier static images remain in its own review. These pairs use the rig's source-matched neutral pose as the comparison.

**Anatomy.** Reference-screened for the gross pathway from both gastrocnemius heads and soleus to the calcaneal tendon and posterior heel. Quantified proximity preserves a source relationship. Histological insertion, joint kinematics, loading, clinical validity and whole-body attachment/rig coverage remain open.

**Runtime.** Blender imported and evaluated the exported animation, skin and bone weights. Live browser animation and performance were not tested.
