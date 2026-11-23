# Female HRA pelvis

Use one native atlas group for two close-ups. The urinary selection shows the body and base of the bladder, the outlet and the ureteral entry landmarks. The reproductive selection shows the cervix and vaginal exterior between the bladder and rectum.

The [21-part editorial atlas group](../../models/bladder/exports/hra-female-context-r03/bladder_hra_female_context_r03.glb) owns positions and topology for both selections. It opens as editable meshes in Blender. Both source studies trace to the same [HRA United Female v1.10 export](../../sources/datasets/hra/united-female-v1.10/external-source.json), in native glTF metres with identity node transforms. All seven structures in the reproductive selection have exact position and index streams in both source studies. These surfaces support external relationships. The group establishes neither a patent lumen nor anatomical variation or measured fill state.

| Task | Selection | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Locate both ureteral entry landmarks, base and neck | [Bladder base with ureters](../../models/bladder/exports/pelvic-base-r01/README.md) | 1,271,856 | `07de72fc8f3b152291be30f24e24369a08af1232bb1a18f1cb90cdd2440aa15a` |
| Locate the cervix and vaginal exterior | [Cervicovaginal context](../../models/vagina_hra/exports/teaching-context-r03/README.md) | 1,055,764 | `9147a3872fdceae2d351cd6ca069befbb82be880b770d9ef111b647ee001cd5d` |

The retained [reproductive r02 edition](../../models/vagina_hra/provenance/context-r02/migration-2026-10-24/README.md) supplies its own normals, materials and export layout. Both selections preserve their reviewed appearance and byte identity. R02 also carries four additional bony landmarks and evidence for its wider historical scope. The separate Workshop junction illustration and male Z-Anatomy outlet keep their own frames and uses. [Bladder source terms](../../models/bladder/ATTRIBUTION.md) · [Reproductive source terms](../../models/vagina_hra/provenance/context-r02/migration-2026-10-24/ATTRIBUTION.md)

The assembly owns the [bladder selection and source identity](bladder-selection.json) and the [seven reproductive parts](build.py). The earlier target review keeps the original geometry measurements, clean-import comparisons and assessment bindings. Its bladder replay reads the assembly selection. [Historical evidence](../../reviews/teaching-assessments/target-risk/README.md)

Rebuild both exact exports from hydrated inputs using Python 3.11+ and a fresh destination. The check compares both rebuilt files against their reviewed payloads, moves one dome vertex 0.10 mm in a disposable model and verifies that both selections reach the same new position. It also rejects an incompatible vertex count. The retained files are read-only during either command.

```sh
python3.12 assemblies/hra-female-pelvis/build.py .artifacts/hra-pelvis-replay
python3.12 assemblies/hra-female-pelvis/check.py .artifacts/hra-pelvis-replay/checks.json
```
