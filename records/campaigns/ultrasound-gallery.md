# Ultrasound Anatomy gallery

Build interactive ultrasound sweeps and linked asset review across Abdomen, abdominal aortic aneurysm, thyroid, breast and pregnancy. The [use-case brief](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns audience, outcomes and product decisions. The named screening contexts and asset gaps are recorded there.

| Stage | Evidence and decision |
| --- | --- |
| Fixed gallbladder stop | Local Gallery at `9cf0e1f`. The [lesson package](../../lessons/ultrasound-anatomy/README.md) owns the fixed pose and replay. The schematic probe and synthetic wall triggered the sweep study. |
| Playable design study | The [gallbladder prototype](../../experiments/ultrasound-sweep/README.md) combines the probe, fitted patient exterior and internal imaging sector in one orbitable scene. Review the opacity range and the two image comparisons at the long- and short-axis keyframes. |
| Specification and implementation | After design selection, write the implementation spec, delegate most building to Sol, and retain final integration and review with the campaign owner. |
| Expansion | Identify comparable keyframes and their reference images across the scoped tours. Compare the full set before tuning simulated scan appearance. |

The current frontier is review of the redesigned sweep and the set of comparable views. Exercises are deferred. Probe technique and sonographic fidelity still need independent review. The short-axis comparison has noncommercial terms. A published Gallery selection needs a suitable rights decision for its destination.
