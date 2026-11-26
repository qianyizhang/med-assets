# Maintained teaching asset scorecard

The total counts distinct register IDs under the existing `families` key across collections. Coverage and target counts apply to selected export–task pairs. See the [counting rules](../../../docs/gallery/asset-library.md#review-coverage) for the scope of both counts.

Use the [rubric](../../../docs/guides/asset-quality.md) for the anchors and the [exemption recheck](../teaching-exemption-recheck.md) for the current before/after decisions and owned follow-ups.

Run `python3.12 records/campaigns/teaching-asset-review/coverage.py --audit --baseline a6f4b3c` for every identity, historical alternate, evidence gap and register change.

| Collection | Register IDs | At target | Exemption | Open | Full | Partial | Unrated | Export–task pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Body & support | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 3 |
| Cardiovascular | 6 | 7 | 0 | 0 | 7 | 0 | 0 | 7 |
| Digestive | 7 | 7 | 0 | 0 | 7 | 0 | 0 | 7 |
| Endocrine | 7 | 6 | 1 | 0 | 7 | 0 | 0 | 7 |
| Lymphatic & tissue | 5 | 4 | 1 | 0 | 5 | 0 | 0 | 5 |
| Musculoskeletal | 12 | 12 | 0 | 0 | 12 | 0 | 0 | 12 |
| Nervous & senses | 8 | 8 | 0 | 0 | 8 | 0 | 0 | 8 |
| Oral & dental | 7 | 6 | 2 | 0 | 8 | 0 | 0 | 8 |
| Reproductive | 8 | 7 | 1 | 0 | 8 | 0 | 0 | 8 |
| Respiratory | 10 | 10 | 1 | 0 | 11 | 0 | 0 | 11 |
| Skin | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 |
| Urinary | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 4 |
| **Total** | 77 | 75 | 6 | 0 | 81 | 0 | 0 | 81 |

| Collection | Selected export | Fidelity | Form | Readability | Economy | Target | Review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Body & support | [3D Anatomy Workshop](../../../body/anatomy-workshop-r1/Anatomy_Workshop_compact.blend) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-paired/decisions.json) |
| Body & support | [Adipose pads](../../../models/adipose-context/r01/selected-source-pads.glb) | 4 | 3 | 4 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Body & support | [Body envelope](../../../models/skin/exports/teaching-economy-r01/skin_source_frame.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Cardiovascular | [Aorta · s1233](../../../models/aorta/exports/metadata-cleanup-r01/aorta.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Cardiovascular | [Aortic tree · Z](../../../models/aortic_tree_z/exports/teaching-economy-r01/aortic_tree_z_source_frame.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Cardiovascular | [Cardiac Atlas · cardiac-static-ed](../../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/cardiac-static-ed.glb) | 4 | 3 | 4 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-cardiac-shared-source/campaign-assessments.json) |
| Cardiovascular | [Cardiac Atlas · ventricular-wall-motion](../../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/ventricular-wall-motion.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-cardiac-shared-source/campaign-assessments.json) |
| Cardiovascular | [Heart · body shell](../../../models/heart/exports/texture-pack-r02/heart.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-paired/decisions.json) |
| Cardiovascular | [Pulmonary-vein component](../../../models/pulmonary_vein/exports/metadata-cleanup-r01/pulmonary_vein.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Cardiovascular | [Static cardiac exterior](../../../heart/exterior-presentation-r02/exports/static-opaque-exterior-repacked.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Digestive | [Esophageal wall](../../../models/esophagus_wall/exports/authored-cutaway-r01/esophagus-wall-cutaway-r01.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Digestive | [Gallbladder](../../../models/gallbladder/exports/metadata-cleanup-r01/gallbladder.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-risk/decisions.json) |
| Digestive | [Large bowel](../../../models/large-intestine/exports/teaching-economy-r01/large-intestine.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Digestive | [Liver](../../../models/liver/exports/teaching-economy-r02/liver.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Digestive | [Pancreas](../../../models/pancreas/exports/gross-locator-r05/gross-locator.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-regional/decisions.json) |
| Digestive | [Small bowel](../../../models/small-intestine/exports/teaching-economy-r01/small-intestine.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Digestive | [Stomach · s1233](../../../models/stomach/exports/teaching-economy-r02/stomach.glb) | 3 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Endocrine | [Adrenal pair](../../../models/adrenals/exports/atlas-locator-r02/atlas-profiles.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-regional/decisions.json) |
| Endocrine | [Adrenal regional study · s1233](../../../assemblies/endocrine-locator/adrenal-study-r05/s1233-adrenals-regional.glb) | 4 | 4 | 4 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Endocrine | [Hypothalamus](../../../models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Endocrine | [Hypothalamus–pituitary join](../../../assemblies/hypothalamus-pituitary/teaching-stalk-r01/hypothalamus-pituitary-teaching.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Endocrine | [Parathyroid localization](../../../models/parathyroids/exports/z-localization-r01/parathyroids_thyroid_context.glb) | 4 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Endocrine | [Pituitary](../../../models/pituitary/exports/source-candidate-01/pituitary_source_frame.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/campaign-assessments.json) |
| Endocrine | [Thyroid · s0189](../../../models/thyroid_ct_s0189/exports/illustrative-exterior-r02/thyroid-illustrative-exterior.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/refinement-form/campaign-assessments.json) |
| Lymphatic & tissue | [Blood-cell forms](../../../models/blood_cell_study/exports/teaching-economy-r01/blood-cell-authored-study-r05.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Lymphatic & tissue | [Lymph collecting routes](../../../models/lymph-collecting-routes/source-trace-r02/route-diagram.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-regional/decisions.json) |
| Lymphatic & tissue | [Single lymph node](../../../models/lymph_node/exports/tissue-color-pack-r02/lymph-node.glb) | 4 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-paired/decisions.json) |
| Lymphatic & tissue | [Spleen](../../../models/spleen/exports/hra-female-v1.10-r03/spleen.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Lymphatic & tissue | [Thymus](../../../models/thymus/exports/source-candidate-01/thymus_source_frame.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Bone / trabecula comparison](../../../assemblies/marrow-comparison/2026-10-23/illustrative-container-r03.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Bone-marrow cutaway](../../../models/bone_marrow/exports/teaching-economy-r01/marrow_cutaway.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Musculoskeletal | [Calf–Achilles–heel](../../../assemblies/musculoskeletal-teaching/2026-10-23/achilles-right-context.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Elbow](../../../models/joints/exports/z-elbow-r02/elbow_z_native.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/campaign-assessments.json) |
| Musculoskeletal | [Knee](../../../models/joints/exports/z-knee-r01/knee_z_native.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [L3 vertebra](../../../models/vertebrae_L3/exports/metadata-cleanup-r01/vertebrae_L3.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [L3–L4 disc](../../../assemblies/skeletal-teaching/2026-10-23/L3-L4-disc.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Muscle atlas](../../../models/muscle/exports/teaching-economy-r02/muscle_z_native_frame.glb) | 3 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Musculoskeletal | [Right rotator cuff](../../../models/joints/exports/z-rotator-cuff-r01/right-rotator-cuff.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Second costal cartilage](../../../assemblies/skeletal-teaching/2026-10-23/second-costal.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Musculoskeletal | [Shoulder](../../../models/joints/exports/z-shoulder-r02/shoulder_z_native.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/campaign-assessments.json) |
| Musculoskeletal | [Skeletal atlas](../../../models/skeleton/exports/teaching-economy-r01/skeleton_source_frame.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Nervous & senses | [Auricles / pinnae](../../../models/ears_z/exports/teaching-economy-r01/ears_z.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Nervous & senses | [Brain](../../../models/brain/exports/teaching-economy-r02/brain-source-frame.glb) | 3 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Nervous & senses | [Eye · anterior segment](../../../models/eye_anterior_segment/exports/eye-order-r01/eye-order-study.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-risk/decisions.json) |
| Nervous & senses | [Eye · exterior courses](../../../models/eye_exterior/exports/z-native-courses-r01/eye-exterior-courses.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Nervous & senses | [Median nerve at wrist](../../../models/peripheral_nerves/exports/median-wrist-r01/right-median-wrist.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Nervous & senses | [Sciatic nerve at hip](../../../models/peripheral_nerves/exports/sciatic-hip-r01/right-sciatic-hip.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-lymphatic-musculoskeletal-nervous/campaign-assessments.json) |
| Nervous & senses | [Spinal cord & roots](../../../models/spinal_cord/exports/teaching-economy-r02/candidate.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Nervous & senses | [Ulnar nerve at elbow](../../../models/peripheral_nerves/exports/ulnar-elbow-r02/right-ulnar-elbow.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/campaign-assessments.json) |
| Oral & dental | [Adult teeth & gingiva](../../../models/teeth_gums/exports/r02/teeth_gums.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/campaign-assessments.json) |
| Oral & dental | [FDI31 · prepared specimen](../../../models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb) | 3 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Oral & dental | [Major salivary glands · glands-and-parotid-ducts](../../../models/salivary_glands/exports/z-native-shared-r01/glands-and-parotid-ducts.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-salivary-shared-source/campaign-assessments.json) |
| Oral & dental | [Major salivary glands · same-source-context](../../../models/salivary_glands/exports/z-native-shared-r01/same-source-context.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-salivary-shared-source/campaign-assessments.json) |
| Oral & dental | [Molar root & support](../../../models/dental-root-support/v3/molar-support-v3.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/campaign-assessments.json) |
| Oral & dental | [Parotid pair](../../../models/parotid_glands/exports/source-shared-r01/parotid-pair.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-salivary-shared-source/campaign-assessments.json) |
| Oral & dental | [Tongue · hybrid](../../../models/tongue_authored_study/exports/teaching-economy-r01/tongue-authored-hra-hybrid-p11.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Oral & dental | [UFF molar specimen](../../../models/dental_specimens/uff_tomo1b/exports/r01/uff-tomo1b-display.glb) | 3 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Reproductive | [Breast pair](../../../models/breasts_hra/exports/teaching-economy-r01/breasts_hra_native_frame.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Reproductive | [Full-term placenta](../../../models/placenta/exports/teaching-economy-r01/placenta_full_term.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Reproductive | [Ovary + tubal ends](../../../models/ovaries/exports/teaching-ovoid-r02/ovary-tubal-teaching.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Reproductive | [Penile components](../../../models/penis/exports/z-native-components-r04/penile_internal_components.glb) | 3 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-source/decisions.json) |
| Reproductive | [Prostate](../../../models/prostate/exports/teaching-economy-r01/VH_M_Prostate.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Reproductive | [Testis–epididymis](../../../models/testes/exports/z-native-epididymis-r01/testicular-region.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/campaign-assessments.json) |
| Reproductive | [Uterus exterior](../../../models/uterus/exports/hra-v1.1-r02/uterus_exterior.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/campaign-assessments.json) |
| Reproductive | [HRA female pelvis · Vaginal / cervical context](../../../models/vagina_hra/exports/teaching-context-r03/vagina_teaching_context.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-form/decisions.json) |
| Respiratory | [Breathing collection](../../../body/breathing/exports/dome-motion-r01/Breathing_Dome.blend) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-risk/decisions.json) |
| Respiratory | [Bronchial tree · first fork](../../../models/bronchial_tree/exports/first-fork-fairing-r15/bronchial-first-fork.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-form/decisions.json) |
| Respiratory | [Diaphragm](../../../models/diaphragm/exports/normal-pack-r02/diaphragm.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-paired/decisions.json) |
| Respiratory | [Left lung · s1233](../../../models/lung_left/exports/teaching-economy-r01/lung_left.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Respiratory | [Lung pair · HRA](../../../models/lung_pair/exports/teaching-economy-r01/lung_female_hra_normals_r02.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Respiratory | [Nasal / sinus airspace](../../../models/nose_sinuses/exports/index-pack-r02/nasal_airspace.glb) | 4 | 2 | 3 | 3 | Exemption | [Evidence](../../../reviews/teaching-assessments/reopen-paired/decisions.json) |
| Respiratory | [Pharynx / larynx](../../../models/pharynx_larynx/exports/teaching-economy-r01/pharynx_larynx.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Respiratory | [Right lung · s1233](../../../models/lung_right/exports/metadata-cleanup-r01/lung_right.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-respiratory/campaign-assessments.json) |
| Respiratory | [Terminal airspace study](../../../lessons/one-breath/terminal-study-r02/terminal-airspaces.glb) | 4 | 3 | 4 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-respiratory/campaign-assessments.json) |
| Respiratory | [Trachea / Y-airway · trachea-open](../../../models/trachea/exports/teaching-economy-r02/trachea-open.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/reopen-economy/decisions.json) |
| Respiratory | [Trachea / Y-airway · trachea-cutaway](../../../models/trachea/exports/open-airway-r06/trachea-cutaway.glb) | 4 | 3 | 4 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-23-trachea-cutaway/campaign-assessments.json) |
| Skin | [Nail unit surface](../../../models/skin/nail-study-r02/nail.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/2026-11-22-dental-reproductive-skin-urinary/campaign-assessments.json) |
| Urinary | [HRA female pelvis · Bladder](../../../models/bladder/exports/pelvic-base-r01/bladder-pelvic-base.glb) | 4 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/target-risk/decisions.json) |
| Urinary | [Left kidney](../../../models/kidney_left/exports/teaching-economy-r01/kidney_left.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
| Urinary | [Male urethral context](../../../models/urethra_male/exports/z-native-context-r01/urethral-context.glb) | 3 | 3 | 3 | 3 | At target | [Evidence](../../../reviews/teaching-assessments/refinement-risk/accepted.json) |
| Urinary | [Right kidney](../../../models/kidney_right/exports/teaching-economy-r01/kidney_right.glb) | 4 | 3 | 3 | 4 | At target | [Evidence](../../../reviews/teaching-assessments/target-economy/decisions.json) |
