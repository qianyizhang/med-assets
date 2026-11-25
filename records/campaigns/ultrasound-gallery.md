# Ultrasound Anatomy gallery

Build interactive sweeps across the abdomen, abdominal aorta, thyroid, common carotids, breast and pregnancy, alongside adult cardiac echo. The [tour specification](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns the shared controls, study coverage, acceptance and remaining decisions.

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
| Common carotid anatomy | The combined bilateral duplex exam adds branch and flow stations, manual calipers, gated velocity measurements and tracked lumen and grayscale reconstruction. The original CT orientation sweeps retain their separate acquired comparisons. [Carotid scope](../../docs/gallery/use-cases/ultrasound-anatomy.md#common-carotid-coverage) |
| Cardiac echo | The adult study links 17 probe positions to one beating heart, a registered torso, measurement and Doppler exercises, nine acquired cines and the BSE reference panels. [Replay and evidence](../../experiments/ultrasound-sweep/cardiac/README.md) |
| Next joint decision | Walk the completed abdomen set with the owner, then design the ultrasound asset-management and display experience together. |
| Next batch | Complete the [scan scenarios](../../docs/gallery/use-cases/ultrasound-anatomy.md#next-batch). Use the acquired comparison set when reviewing rendering fidelity. |

The source-specific terms apply independently to each acquired reference. Public release and clinical qualification remain open.
