# Vaginal and cervical teaching context r03

Use [this seven-part HRA selection](vagina_teaching_context.glb) to locate the vaginal exterior below the cervix and between anterior bladder and posterior rectum. The [matched plate](../../../../reviews/teaching-assessments/target-form/plates/vagina_hra-comparison.webp) pairs the original overview with the same seven visible meshes in the candidate at matched cameras. Open the [full r02](../context-r02/vagina_hra_same_atlas_context_r02.glb) for the additional bony and uterine context.

| Export | SHA-256 | Bytes | Triangles |
| --- | --- | ---: | ---: |
| r03 | `9147a3872fdceae2d351cd6ca069befbb82be880b770d9ef111b647ee001cd5d` | 1,055,764 | 57,166 |
| r02 | `c649de4db766ba00020315029c922de1d018061c1a34bd95c850a05255ab3037` | 2,718,584 | 138,419 |

The seven selected meshes retain the exact native frame, position, index, normal and material data. They are the vaginal exterior, cervix, cervicovaginal junction, rectum, bladder dome, bladder base and bladder-neck smooth muscle. Sixteen meshes representing other pelvic structures are omitted. Both the side and opposite focused views match the r02 selection pixel for pixel. These surfaces provide exterior context. The source establishes neither a validated lumen nor detailed mucosal boundaries.

Retain the [HRA source attribution and terms](../../provenance/context-r02/migration-2026-10-24/ATTRIBUTION.md), including the attribution for the source parts and the r02 assembly. This edition adds only a teaching selection and container bookkeeping changes.

The [shared female HRA pelvis recipe](../../../../assemblies/hra-female-pelvis/README.md) rebuilds these seven structures with positions and topology from the same editable group as the bladder-base export. The hydrated exact r02 still supplies the reviewed display normals and materials. The [original command](../../recipes/teaching-context-r03/build.py) uses that shared recipe and keeps its single-file output. Use a fresh path from the repository root.

```sh
python3.12 models/vagina_hra/recipes/teaching-context-r03/build.py .artifacts/vagina-teaching-context-r03.glb
```

[Clean-import and view bindings](../../../../reviews/teaching-assessments/target-form/README.md)
