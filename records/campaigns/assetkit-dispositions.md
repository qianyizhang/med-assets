# AssetKit migration dispositions

The [landscape](../../docs/ASSET_LANDSCAPE.md) has 87 directory entries across the atlas, model and assembly sections. Its 85 candidate directories exclude [the 2D body collection](../../body/2d-v4/) and [the earlier synthetic imaging volumes](../../heart/synthetic-imaging/). The reconciliation at `f691f6f1` compared tracked 3D paths within all 85 directories and elsewhere in the repository with native records and existing readers. In the 205-path Gallery intake, all 81 maintained selections had exact native owner records after adding the [terminal-airspace cutaway](../../lessons/one-breath/terminal-study-r02/asset.record.json). Directory counts describe scope. The [migration acceptance rules](../../docs/MIGRATION_SPEC.md#package-and-wave-acceptance) require the exact export and the owning reader before closing a wave.

## Frozen Gallery and legacy delivery

| Exact file or group | Disposition and evidence |
| --- | --- |
| `heart/Cardiac_Atlas/exports/STL_RAS_mm/{bloodpool_LA,bloodpool_LV,bloodpool_RA,bloodpool_RV,interatrial_septum,interventricular_septum,wall_LA,wall_LV,wall_RA,wall_RV}.stl` | Retain ten native RAS-millimetre end-diastolic surfaces as exact artifacts with their existing static Library downloads. The atlas record pins all ten identities and the import convention. The selected metre-valued scene has its own native export. [Owner record](../../heart/Cardiac_Atlas/asset.record.json) · [STL export contract](../../heart/Cardiac_Atlas/exports/EXPORT_CONTRACT.json) |
| `reviews/swirendo_fdi31/2026-10-27-interface-locked/media/A_1_31_T2_SEG_na__layered.glb` | Retain the 26,524,356-byte research candidate at `library/swirendo_fdi31/interface-locked-20261027`. The FDI31 owner pins SHA-256 `c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014` as frozen review evidence. Balanced remains the distinct maintained choice. [Owner record](../../models/swirendo_fdi31/asset.record.json) · [Bounded review and exact media](../../reviews/swirendo_fdi31/2026-10-27-interface-locked/README.md) |
| `dental-review/cotton-tweezers-r04/cotton-tweezers.glb` and `dental-review/mouth-mirror-r01/mouth-mirror.glb` | Keep their deployed legacy Dental Review delivery paths and current Gallery list entries. The owning index supplies identity and remote delivery. A native port needs a recoverable package-owned payload with frame and rights evidence. [Legacy Dental delivery](../../sites/anatomy-gallery/app/src/content/assets/legacy-dental-assets.json) |
| `body/3d/assets/motion/heart_animated_clinical.glb` and `swirendo-pilot/A_1_31_T2_SEG_na__layered.glb` | Retain the historical route and documented identity. These older listed files have no locally available payload at their original paths. The fitted cardiac archive and historical prepared-incisor r03 need owner-approved recovery before path-backed registration. [Historical Library and dental entries](../../sites/anatomy-gallery/app/src/content/gallery/static-reviews.json) · [Dental pilot ingestion](../../docs/dental-atlas/pilot-ingestion.md) |

## Archived and recipe-owned 3D

The dated Body Systems survey owns these replay files. The ordinary Body Systems plate reader keeps its reviewed WebPs and separate 3D lesson links. The twelve archive members below and the two optional Workshop outputs matched the independent survey identities on the local Mac. All fourteen are outside the Git index. [Survey replay and restore](../../sites/body-systems-survey/README.md#restore-the-media) · [Exact archive identities](../../sites/body-systems-survey/backup-sha256.txt)

| Owner and file | Disposition |
| --- | --- |
| `assemblies/cardiovascular-loop/cardiovascular-loop.glb` | Archive-only circulation and valve plates. [Replay and review](../../assemblies/cardiovascular-loop/) |
| `assemblies/digestive-route/r01/digestive-route.glb` | Archive-only digestive route and related plates. [Recipe owner](../../assemblies/digestive-route/r01/) |
| `assemblies/endocrine-locator/r01/endocrine-locator.glb` | Archive-only whole-body locator. Regional r03–r05 have separate native records and Gallery uses. The r02 neck, thyroid and case adrenal GLBs are source-recipe results. The r02 adrenal case reference is pinned as evidence for the regional replay. [r01](../../assemblies/endocrine-locator/r01/README.md) · [r02](../../assemblies/endocrine-locator/r02/README.md) · [Regional record](../../assemblies/endocrine-locator/asset.record.json) |
| `assemblies/lymphatic-return/r01/lymphatic-return.glb` | Archive-only lymphatic return plates. [Recipe owner](../../assemblies/lymphatic-return/r01/) |
| `assemblies/musculoskeletal-teaching/plantarflexion-r01/calf-plantarflexion.glb` | Archive-only pose study. The static Achilles context is a separate, named Library export. [Pose replay](../../assemblies/musculoskeletal-teaching/plantarflexion-r01/README.md) |
| `assemblies/nervous-senses/nervous-senses.glb` | Archive-only nervous and special-sense plates. [Recipe owner](../../assemblies/nervous-senses/) |
| `assemblies/reproductive-tracts/r01/{female,male}.glb` | Two archive-only reproductive models. Neither changes the native cervicovaginal Gallery layer exercise. [Recipe owner](../../assemblies/reproductive-tracts/r01/) |
| `assemblies/skeletal-teaching/knee-motion-r01/knee-motion.glb` | Archive-only two-pose knee study. The L3–L4 and costal studies retain their independent static Library records. [Knee replay](../../assemblies/skeletal-teaching/knee-motion-r01/README.md) |
| `assemblies/urinary-junctions/r01/urinary-junctions.glb` | Archive-only urinary junction plates. The ordinary viewer loads the independent native HRA bladder-base export. [Recipe owner](../../assemblies/urinary-junctions/r01/) |
| `lessons/one-breath/airway-r01/airway-route.glb` | Archive-only full airway replay and comparison input. The tracked terminal cutaway now has native owner `anatomy:authored:terminal-airspaces@terminal-study-r02:cutaway`, with four verified selectors and the existing `terminal-airspace-study` Gallery selection. [Airway replay](../../lessons/one-breath/airway-r01/README.md) · [Cutaway owner](../../lessons/one-breath/terminal-study-r02/asset.record.json) |
| `models/skin/teaching-block-r01/skin-block.glb` | Archive-only integumentary plate and nail comparison replay input. The tracked nail and adult body envelope each have their own owner record. [Skin block](../../models/skin/teaching-block-r01/README.md) · [Nail record](../../models/skin/nail-study-r02/asset.record.json) |
| `.artifacts/body-systems-survey-2026-11-19/workshop-s1233-r01/{cardiovascular,digestive}.glb` | Two optional local compositions generated by the Workshop recipe. Keep case inputs, registrations and render receipts with the survey. [Workshop owner](../../assemblies/workshop-s1233/README.md) |

The other recipe-only directory candidates retain their existing output owners.

| Package | Disposition |
| --- | --- |
| [`assemblies/hra-female-pelvis`](../../assemblies/hra-female-pelvis/README.md) | Owns the two selection recipes. The 21-part atlas input and two delivered meshes live in the bladder and vagina owners. |
| [`assemblies/kidney-pair`](../../assemblies/kidney-pair/recipes/README.md) | Owns left and right source replay. The delivered references have separate renal package identities. |
| [`assemblies/bladder-pancreas`](../../assemblies/bladder-pancreas/recipes/recipe/README.md) and [`assemblies/liver-spleen`](../../assemblies/liver-spleen/recipes/README.md) | Retain both shared source replay lines and pinned authoring dependencies. Their organ records own delivered bytes. |
| [`models/fetus`](../../models/fetus/exports/head-face-junction-r01/README.md) | Retain the bounded head–face recipe and historical private review. The November 6 disposition keeps original and candidate media private. The procedural pregnancy sweeps have separate acquisition geometry. |
| [`src/assetkit/pilot`](../../src/assetkit/pilot/README.md) | Retain the metadata-only fixture and its isolated `assets.json` and `consumer.json` examples. Production liver identity and playback belong to the tracked s1233 package and sweep. |

## Older tracked Library outputs

These exact paths retain listed historical revisions and their legacy file delivery. A dependency pin preserves replay where the native owner consumes the file. The dated scope and current selection stay with the [Gallery Library](../../sites/anatomy-gallery/app/src/content/gallery/library-packages.json) and [maintained selections](../../docs/gallery/maintained-selections.json). A sibling export cannot substitute for any route below.

| Path | Retained role |
| --- | --- |
| `models/adrenals/exports/source-candidate-01/adrenals_source_frame.glb` | `library/adrenals/source-candidate-01`. [Pinned source](../../models/adrenals/asset.record.json). |
| `models/aortic_tree_z/exports/r02/aortic_tree_z_source_frame.glb` | `library/aortic_tree_z/r02`. [Pinned source](../../models/aortic_tree_z/asset.record.json). |
| `models/bladder/exports/metadata-cleanup-r01/bladder.glb` | `library/bladder/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |
| `models/blood_cell_study/exports/authored-r05/blood-cell-authored-study-r05.glb` | `library/blood_cell_study/authored-r05`. [Pinned source](../../models/blood_cell_study/asset.record.json). |
| `models/bone_marrow/exports/authored-source-cutaway-r05/marrow_cutaway.glb` | `library/bone_marrow/authored-source-cutaway-r05`. [Pinned source](../../models/bone_marrow/asset.record.json). |
| `models/brain/exports/bodyparts3d-4.0-atlas-r2/brain-source-frame.glb` | `library/brain/bodyparts3d-4.0-atlas-r2`. [Pinned source](../../models/brain/asset.record.json). |
| `models/brain/exports/metadata-cleanup-r01/brain.glb` | `library/brain/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |
| `models/breasts_hra/exports/source-candidate-02/breasts_hra_native_frame.glb` | `library/breasts_hra/source-candidate-02`. [Pinned source](../../models/breasts_hra/asset.record.json). |
| `models/bronchial_tree/exports/authored-central-fairing-r13/bronchial_central_fairing.glb` | `library/bronchial_tree/authored-central-fairing-r13`. Earlier airway geometry and review lineage. |
| `models/bronchial_tree/exports/authored-junction-repair-r07/bronchial_authored_junction_repair.glb` | `library/bronchial_tree/authored-junction-repair-r07`. Earlier airway geometry and review lineage. |
| `models/bronchial_tree/exports/authored-lobar-fairing-r09/bronchial_lobar_fairing.glb` | `library/bronchial_tree/authored-lobar-fairing-r09`. Earlier airway geometry and review lineage. |
| `models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb` | `library/bronchial_tree/distal-sampling-r14`. [Pinned source](../../models/bronchial_tree/asset.record.json). |
| `models/bronchial_tree/exports/metadata-cleanup-r01/bronchial_tree.glb` | `library/bronchial_tree/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |
| `models/diaphragm/exports/z-native-static-r01/diaphragm_z_context_static.glb` | `library/diaphragm/z-native-static-r01`. Separate source-context export. |
| `models/diaphragm/exports/z-native-static-r01/diaphragm_z_native_static.glb` | `library/diaphragm/z-native-static-r01`. [Pinned source](../../models/diaphragm/asset.record.json). |
| `models/ears_z/exports/r04/ears_z.glb` | `library/ears_z/r04`. [Pinned source](../../models/ears_z/asset.record.json). |
| `models/heart/exports/metadata-cleanup-r01/heart.glb` | `library/heart/metadata-cleanup-r01`. [Pinned source](../../models/heart/asset.record.json). |
| `models/joints/exports/z-elbow-r01/elbow_z_native.glb` | `library/joints/z-elbow-r01`. Earlier native regional study. |
| `models/joints/exports/z-shoulder-r01/shoulder_z_native.glb` | `library/joints/z-shoulder-r01`. Earlier native regional study. |
| `models/kidney_left/exports/hra-female-v1.3-r02/kidney_left.glb` | `library/kidney_left/hra-female-v1.3-r02`. [Pinned source](../../models/kidney_left/asset.record.json). |
| `models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb` | `library/kidney_left/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |
| `models/kidney_right/exports/hra-female-v1.3-r02/kidney_right.glb` | `library/kidney_right/hra-female-v1.3-r02`. [Pinned source](../../models/kidney_right/asset.record.json). |
| `models/kidney_right/exports/metadata-cleanup-r01/kidney_right.glb` | `library/kidney_right/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |
| `models/large-intestine/exports/source-candidate-v4/large-intestine.glb` | `library/large-intestine/source-candidate-v4`. [Pinned source](../../models/large-intestine/asset.record.json). |
| `models/liver/exports/hra-female-v1.10-r02/liver.glb` | `library/liver/hra-female-v1.10-r02`. [Pinned source](../../models/liver/asset.record.json). |
| `models/liver/exports/metadata-cleanup-r01/liver.glb` | `library/liver/metadata-cleanup-r01`. Historical metadata-cleanup candidate with unresolved lineage. [HRA gate and scope](../../docs/MIGRATION_SPEC.md#local-execution). |
| `models/lung_left/exports/metadata-cleanup-r01/lung_left.glb` | `library/lung_left/metadata-cleanup-r01`. [Pinned source](../../models/lung_left/asset.record.json). |
| `models/lung_pair/exports/hra-female-normals-r02/lung_female_hra_normals_r02.glb` | `library/lung_pair/hra-female-normals-r02`. [Pinned source](../../models/lung_pair/asset.record.json). |
| `models/lymph-collecting-routes/source-context-r01/selected-source-routes.glb` | `library/lymph-collecting-routes/source-context-r01`. [Pinned source](../../models/lymph-collecting-routes/asset.record.json). |
| `models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb` | `library/lymph_node/hra-v1.2`. [Pinned source](../../models/lymph_node/asset.record.json). |
| `models/pancreas/exports/metadata-cleanup-r01/pancreas.glb` | `library/pancreas/metadata-cleanup-r01`. Retain the October 23 metadata-cleanup candidate and its frozen review. |

The [delivery index](../../sites/anatomy-gallery/app/src/content/assets/delivery-index.json) records the file bindings. Runtime checks, recovery approval, new geometry and distribution decisions belong to the named owners.

## Evidence corrections found during reconciliation

- The original landscape implied that the private fetal study supplied Gallery and ultrasound. Its owner retains the bounded private review, and the ultrasound steps build independent gestational geometry. [Landscape](../../docs/ASSET_LANDSCAPE.md) · [Fetal study scope](../../models/fetus/exports/head-face-junction-r01/README.md) · [Sweep recipes](../../experiments/ultrasound-sweep/README.md#replay)
- Consolidating recipe paths changed the dated Achilles replay receipt and broke its exact evidence pin. The native port restored the original receipt bytes. The assembly guide records the current command. The receipt preserves the historical location. Verification passed the dated evidence ledger. The Blender recipe itself was not rebuilt for this migration. [Current replay guide](../../assemblies/musculoskeletal-teaching/2026-10-23/README.md) · [Historical receipt](../../reviews/draft_muscle/2026-10-23-achilles-context/independent-export-replay.json)
