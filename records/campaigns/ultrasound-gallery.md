# Ultrasound Anatomy gallery

Build a learner tour and linked asset review across Abdomen, abdominal aortic aneurysm, thyroid, breast and pregnancy. The [use-case brief](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns audience, outcomes and product decisions. The named screening contexts and asset gaps are recorded there.

| Stage | Evidence and decision |
| --- | --- |
| Fixed gallbladder stop | Local Gallery at `9cf0e1f`. The [lesson package](../../lessons/ultrasound-anatomy/README.md) owns the fixed pose and replay. The schematic probe and synthetic wall triggered the sweep study. |
| Playable design study | Compare [probe control and guided stops](../../experiments/ultrasound-sweep/README.md) on the same anatomy and acquired references. Select the preferred interaction with the owner. |
| Specification and implementation | After design selection, write the implementation spec, delegate most building to Sol, and retain final integration and review with the campaign owner. |
| Expansion | Assess each subsequent tour against its reference images, registered geometry, learner action and asset evidence before claiming it is ready. |

The current frontier is the choice of interaction and a visual judgment on the probe and scan. Probe technique and sonographic fidelity still need independent review. The short-axis comparison has noncommercial terms. A published Gallery selection needs a suitable rights decision for its destination.
