# Two adult reproductive tracts

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Use [female.glb](female.glb) to follow each ovary's relationship to the fimbriae, infundibulum, ampulla, isthmus and uterine horn. Continue from the uterine body through the lower uterine segment, cervix and vagina. Select named structures to inspect the pickup space and the tubal ends. The [breast exterior](../../../models/breasts_hra/exports/source-candidate-02/README.md) is a separate regional study.

Use [male.glb](male.glb) to trace each epididymal tail into its ductus deferens. The ochre seminal vesicle sends a short duct to meet the vas behind the bladder. The paired ejaculatory ducts enter the prostatic urethral region. Isolate the urethra to trace the remaining course to its distal end. The bladder and prostate provide orientation. [Matched views and measurements](../../../reviews/reproductive-tracts/r01/README.md).

## Admission and reference

The [HRA tubal study](../../../models/ovaries/exports/hra-ovary-tubal-r01/README.md) lacks the uterus. The [HRA pelvic study](../../../models/vagina_hra/provenance/context-r02/migration-2026-10-24/README.md) contains uterus, cervix and vagina. Comparing their native coordinates put each isthmus within 0.035 mm of its selected cornual surface. This allows direct composition without invented bridges. The ovary and fimbriae retain their native small gap. Oocyte pickup crosses a peritoneal space. This assembly supplies no simulated ovulation, patent lumen or measured patient-specific pose.

The [testicular study](../../../models/testes/exports/z-native-epididymis-r01/README.md) stops at the epididymides. The earlier review rejected the source ductus display for obscuring the region and unvalidated routing. The [urethral study](../../../models/urethra_male/exports/z-native-context-r01/README.md) supplies a urethral surface, bladder and prostate in compatible native coordinates. The [2D testicular pathway](../../../diagrams/testis_pathway/exports/r02/README.md) and [NCI SEER duct-system description](https://www.training.seer.cancer.gov/anatomy/reproductive/male/duct.html) guide the bilateral schematic additions. The vesicles, ducts and all new attachment locations are inferred gross teaching shapes. The source urethral surface supplies the distal endpoint. Wall thickness, functional patency, ureter crossings, scrotum and erectile tissues are outside scope.

Blender metres, +X toward source labelled left, +Z superior, −Y anterior. glTF uses +X left, +Y superior, +Z anterior. Both compositions apply identity placement to all source world coordinates. Source geometry is detached from parent objects with world transforms baked. Source atlases retain their own scale and laterality limits. Tissues use illustrative matte materials, with teal highlighting the routes. This owner retains both independent assemblies for the body-systems survey. All upstream files retain their individual uses.

## Attribution

[Four exact inputs](inputs.json). Female tissues derive from Kristen Browne and Heidi Schlehlein, HuBMAP Human Reference Atlas ovary v1.3, fallopian tube v1.2 and united-female v1.10. [Ovary and tube credits](../../../sources/datasets/hra/ovary-tubal-context/README.md) and [pelvic attribution](../../../models/vagina_hra/provenance/context-r02/migration-2026-10-24/ATTRIBUTION.md), CC BY 4.0. Male Z-Anatomy derivatives and renders retain CC BY-SA 4.0 and historical BodyParts3D CC BY-SA 2.1 Japan attribution. © DBCLS, Kousaku Okubo, Gauthier Kervyn, Marcin Zielinski, Lluis Vinent and contributors. [Full license and credits](../../../sources/datasets/z-anatomy/testicular-region/ATTRIBUTION.md). Changes include selection, composition, matte recoloring and eight new schematic male surfaces. Reference figures are excluded.

## Replay

[female.blend](female.blend) and [male.blend](male.blend) are separately editable. Blender 5.2.3, factory settings and the pinned local GLBs produced this delivery. From repository root choose fresh output directories.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/reproductive-tracts/r01/build.py -- .artifacts/reproductive-replay
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/reproductive-tracts/r01/check.py -- .artifacts/reproductive-replay .artifacts/reproductive-replay/contacts.json
for sex in female male; do
  blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/reproductive-replay/$sex.glb --views assemblies/reproductive-tracts/r01/$sex-views.json --output .artifacts/reproductive-replay/$sex-views
done
```
