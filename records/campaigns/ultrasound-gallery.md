# Ultrasound Anatomy gallery

Build interactive sweeps across Abdomen, abdominal aortic aneurysm, thyroid, breast and pregnancy. The [tour specification](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns the settled interaction, abdomen, thyroid and breast coverage, acceptance and remaining decisions.

| Stage | Outcome |
| --- | --- |
| Fixed gallbladder stop | Local Gallery at `9cf0e1f`. The [lesson package](../../lessons/ultrasound-anatomy/README.md) owns the original fixed pose and replay. |
| Interaction and torso study | Iterations established one orbitable torso, probe and scan plane, opacity control, an anatomy overlay, a patterned sweep timeline and paired acquired references. The final pivot trial at `d1dfd85` led to organ-centered orbit. |
| Abdomen tour | The [local prototype](../../experiments/ultrasound-sweep/README.md) implements nine named sweeps and four 3D camera presets. Sol builds the main implementation. The campaign owner selects sources, reviews keyframe images, steers fixes and verifies the integrated tour. |
| Normal anatomy review | Each sweep pairs two acquired comparison stops with its modeled anatomy. Four supporting acquired views cover ductal, hepatic venous, pancreatic tail and hepatorenal anatomy. The [reference inventory](../../experiments/ultrasound-sweep/research/README.md) records each view and its use. |
| Thyroid tour | Right and left lobe sweeps use a linear transducer, rectangular field, same-case thyroid, trachea and carotids. Five published images cover both lobe axes and the isthmus. [Thyroid scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#thyroid-coverage) |
| Breast tour | A right breast sweep moves from peripheral tissue layers to a duct beneath the nipple. Its two acquired references preserve the original anatomical labels. [Breast scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#breast-coverage) |
| Next joint decision | Walk the completed abdomen set with the owner, then design the ultrasound asset-management and display experience together. |
| Later topics | Add or adapt assets for scans that reveal an abnormal finding in a separate milestone. Scope AAA and Pregnancy against their own anatomy, reference images and acquisition requirements. Revisit rendering fidelity using the acquired comparison set. |

The source-specific terms apply independently to each acquired reference. Public release and clinical qualification remain open.
