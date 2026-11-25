# Probe placement on the adult torso

In **Torso pose**, orbit around the transducer and follow the colored sector from its footprint into the chest. The bright marker sits on the image-right side of the phased-array head. A dashed line identifies the aimed central beam. The closer view centers the exact footprint. Hiding the internal landmarks shows the contact against intact skin. [Observed placements](placement.webp)

| Window | Body landmarks |
| --- | --- |
| Apical | Left lower precordium near the apex, inferior to the left pectoral region. The lens and image keep the same instant during orbit. |
| Parasternal | Interspaces beside the left sternal border. The marker and sector rotate between the long and short axes; different levels use subtly different contacts. |
| Subcostal | Upper abdomen caudal to the xiphoid. Both the imaging axis and its contact change when turning to the IVC or aorta. |
| Suprasternal | Notch at the base of the neck. Follow the beam inferiorly behind the manubrium toward the arch. |

The table provides an orientation reference. The native atlas rolls 28° toward the patient's left in the apical and parasternal windows and returns to a supine orientation for subcostal and suprasternal views. Patient side labels move with the body. Arm elevation, head extension, respiratory motion, coupling gel and pressure-induced tissue displacement are outside this rigid pose illustration. The adult TTE guideline describes clinical positioning and index-marker conventions in section I and Table 2. [ASE examination guide](https://www.asecho.org/wp-content/uploads/2019/01/2019_Comprehensive-TTE.pdf)

## Geometry and registration

[The cardiac pose table](../heart-poses.js) provides one origin, beam direction, image-right vector, sector aperture and depth per view. A single [rigid coordinate transform](registration.js) maps the heart, its great vessels, each lens and every plane vertex into the native BodyParts3D frame in millimetres. Axis handedness changes because the two coordinate conventions use different positive directions. Surface contacts were selected on the anterior skin in the named windows and steered through the thoracic cage to the model aim points. The registration is illustrative. The lateral edge of the modeled ventricular wall overlaps the projected rib cage in some orientations.

The [contact check](verify-contact.mjs) intersects actual packed skin triangles and independently intersects ribs, costal cartilage, sternum and clavicles from each lens to its aim point. It verifies the registered fan basis at neutral and rotated planes. It covers central rays and the lens center. Off-axis rib shadow, the entire contact patch, acoustic propagation and patient-specific anatomy remain unvalidated.

## Source and replay

BodyParts3D © The Database Center for Life Science (DBCLS). The adult male [skin envelope](../../../../models/skin/exports/bp3d-envelope-r01/README.md) and [skeletal atlas](../../../../models/skeleton/exports/teaching-economy-r01/README.md) share native coordinates. The packed derivative keeps the upper body's original skin triangles, clusters thoracic bone and cartilage vertices, and uses authored display colors. The strip on the transducer, its cable and the couch are original geometry. [Publisher rights](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Input and packed identities](geometry.json)

From the repository root with the [ultrasound Python environment](../../README.md#replay) and both source GLBs hydrated, regenerate into a fresh directory. The three packed files use the existing gallery mesh format. The normal cardiac delivery reads them with its shared local Three.js dependency.

```sh
python experiments/ultrasound-sweep/cardiac/torso/build_torso.py "$TORSO_OUTPUT"
cmp "$TORSO_OUTPUT/geometry.json" experiments/ultrasound-sweep/cardiac/torso/geometry.json
node experiments/ultrasound-sweep/cardiac/torso/verify-contact.mjs
```
