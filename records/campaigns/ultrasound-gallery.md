# Ultrasound Anatomy gallery

Build interactive sweeps across Abdomen, abdominal aortic aneurysm, thyroid, breast and pregnancy, with a separate cardiac cycle study. The [tour specification](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns the settled interaction, abdomen, thyroid, breast and pregnancy coverage, acceptance and remaining decisions.

| Stage | Outcome |
| --- | --- |
| Fixed gallbladder stop | Local Gallery at `9cf0e1f`. The [lesson package](../../lessons/ultrasound-anatomy/README.md) owns the original fixed pose and replay. |
| Interaction and torso study | Iterations established one orbitable torso, probe and scan plane, opacity control, an anatomy overlay, a patterned sweep timeline and paired acquired references. The final pivot trial at `d1dfd85` led to organ-centered orbit. |
| Abdomen tour | The [local prototype](../../experiments/ultrasound-sweep/README.md) implements nine named sweeps and four 3D camera presets. Sol builds the main implementation. The campaign owner selects sources, reviews keyframe images, steers fixes and verifies the integrated tour. |
| Normal anatomy review | Each sweep pairs two acquired comparison stops with its modeled anatomy. Four supporting acquired views cover ductal, hepatic venous, pancreatic tail and hepatorenal anatomy. The [reference inventory](../../experiments/ultrasound-sweep/research/README.md) records each view and its use. |
| Thyroid tour | Right and left lobe sweeps use a linear transducer, rectangular field, same-case thyroid, trachea and carotids. Five published images cover both lobe axes and the isthmus. [Thyroid scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#thyroid-coverage) |
| Breast tour | Three normal-anatomy routes cover a four-pass right breast survey, independently steerable nipple and duct views, and rotation through a right axillary node. A surface-sampled contact model drives the tissue deformation in the 3D view and scan sections. Six acquired images supply structural comparisons. [Breast scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#breast-coverage) |
| Pregnancy tour | Eleven local sweeps span the early embryo, 11–14-week profile and placenta, mid-trimester organ survey, and third-trimester presentation, growth planes and cord sampling. Named stops pair synchronized models with licensed acquisitions. [Pregnancy scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#pregnancy-coverage) |
| Normal aortic screening | The proximal, mid and distal transverse windows share a moving probe, a case-derived aorta and vena cava, and an optional anterior–posterior mask span. [Aortic survey scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#normal-aortic-screening-survey) |
| Cardiac echo | The first normal adult apical four-chamber beat links probe rotation, chamber motion and a phase-matched acquired cine. [Replay and evidence](../../experiments/ultrasound-sweep/cardiac/README.md) |
| Next joint decision | Walk the completed abdomen set with the owner, then design the ultrasound asset-management and display experience together. |
| Later topics | Add or adapt assets for scans that reveal an abnormal finding in a separate milestone. An aneurysm-positive example still requires its own reviewed anatomy and acquired references. Revisit rendering fidelity using the acquired comparison set. |

The source-specific terms apply independently to each acquired reference. Public release and clinical qualification remain open.
