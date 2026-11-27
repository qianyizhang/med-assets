# Asset Landscape & Batch-Porting Triage

This inventory groups candidate 3D packages and their known readers. The [migration specification](MIGRATION_SPEC.md) owns package acceptance, wave assignments, and cleanup criteria. Wave 1 starts after the [HRA liver acceptance test](MIGRATION_SPEC.md#hra-liver-acceptance-test) and the s1233 sweep prerequisites pass on the merged base.

**Pre-migration inventory** · Local branch `asset-governance-v1`, 2026-11-28. Package counts describe directories. LFS totals use declared bytes from `git lfs ls-files --json`, in decimal MB. The [AssetKit design](../src/assetkit/DESIGN.md#decisions) defines the reusable 3D scope.

---

## Executive Summary

| Bucket | Packages | LFS Files | LFS Size | AssetKit Scope | Primary Triage Focus |
| --- | ---: | ---: | ---: | --- | --- |
| `models/` | 63 | 144 | 470.4 MB | **In scope (3D)** | 23 packages ≥ 5 MB hold about 85% of model LFS bytes; s1233 has an owner record |
| `heart/` | 5 | 44 | 192.6 MB | **4 in scope** · 1 outside | `84 MB` in 2 `.blend` files; 1 pilot (`Cardiac_Atlas_Animated`) live |
| `body/` | 3 | 89 | 160.5 MB | **2 in scope** · 1 outside | `82 MB` in 4 `.blend` files; `2d-v4` stays outside 3D scope |
| `assemblies/` | 16 | 10 | 7.6 MB | **In scope (3D)** | Includes shared replay recipes for liver/spleen and bladder/pancreas |
| `diagrams/` | 4 | 8 | 1.8 MB | **Outside (2D)** | Stay with illustration packages |
| `experiments/` | 4 | 562 | 71.9 MB | **Consumer / Exp** | `ultrasound-sweep` (`554` files / `42.5 MB` frames+media) + dental films |
| `lessons/` | 13 | 155 | 7.8 MB | **Consumer** | `body-systems` (`132` WebP display plates) + 12 lessons |
| `sites/` | 2 | 6 | 0.1 MB | **Consumer (Site)** | `anatomy-gallery` + `body-systems-survey` |
| `reviews/` & `sources/` | — | 686 | 244.1 MB | **Evidence / Raw** | `reviews/` alone is `240.5 MB` (`682` files); cold-archive candidate |
| **Total** | **110 pkgs** | **1,704** | **1,157.0 MB** | **85 candidate 3D package directories** | All indexed LFS files hydrated locally at this snapshot; savings require separate measurement |

At the start of the migration, two of the 85 candidate 3D directories had owner records (`models/liver_s1233` and `heart/Cardiac_Atlas_Animated`). The other 83 included the HRA liver gate, multi-asset directories, and recipe-only packages. The wave plan records exactly which exports to port or defer. The standalone Governance toolkit was retired locally in `1b135799`. The [migration acceptance record](../records/campaigns/assetkit-migration.md) tracks completed ports and their reader checks.

---

## 1. Demand Landscape — Priority Consumer Surfaces

| Surface / Consumer | Kind | 3D Assets Consumed (Slugs) | Own LFS (`files · MB`) | Pinning State | Batch-Porting Role |
| --- | --- | --- | --- | --- | --- |
| **`sites/anatomy-gallery`** | Site (Key #1) | The candidate Library selects and lists specific 3D editions. The Gallery also displays separately owned 2D materials. | `6 · 0.1 MB` | Library package declarations, edition routes, teaching register and delivery receipts | Verify each assigned native asset against the actual candidate family, route and pinned bytes. |
| **`lessons/body-systems`** | Lesson · 11 reviewed stops | 70 plate placements trace to 21 survey mesh inputs (seven tracked, twelve archived, two local Workshop outputs). Two detailed pelvic stops also offer live 3D layers. | `132 · 1.5 MB` (display WebPs) | [Display index](../lessons/body-systems/display/index.json), [reviewed stops](../lessons/body-systems/reviewed-stops.json) and survey render receipts | Second major consumer to wire via owning-config 3D references after pilot |
| **`experiments/ultrasound-sweep` + `lessons/ultrasound-anatomy`** | 16 sweeps and 32 exam cases | s1233 liver mesh, BodyParts3D exterior-fit pair, and HRA mammary source. The workbench inspects 10 donor GLBs independently of acquisition. | `556 · 42.6 MB` (frames, reference media and other retained inputs) | The track owns its liver pin. The [exterior recipe](../experiments/ultrasound-sweep/exterior-atlas.json) owns its source pair. | Index exact donor editions and selectors. Track the s0189 exterior, endocrine locator, fetal study and earlier cardiac volumes with their actual owners. |
| **Other 11 `lessons/*`** | Standalone lessons | `one-breath` (`7` local GLBs + airway models), `dental-layer-controls` / `dental-animation` / `arch-identification` (`swirendo_fdi31`, `teeth_gums`, `dental_specimens`), `right-arm-parts` (`joints`, `peripheral_nerves`), `ovary-tubal-context`, `pulmonary-vein-context`, `brain-source-cut`, `kidney-location`, `aortic-arch-locators`, `salivary-practice` | `21 · 6.1 MB` | Mixed `lesson.json` / path refs | Keep existing references until the lesson is edited |
| **Dental `experiments/*`** | Films & trials (`dental-video-treatments`, `dental`, `dental-image26`) | `models/dental_specimens` (`uff_tomo1b`) | `8 · 29.9 MB` (`mp4`/`wav`/`png`) | Dedicated UFF/film replay gates | Keep media outside AssetKit; cold-archive heavy intermediates |

### Ultrasound Anatomy WIP Demand (New Assets & Refinements for AssetKit)

These requests come from the [Ultrasound Anatomy brief](gallery/use-cases/ultrasound-anatomy.md). Track each missing asset as a gap. New geometry and shared probe extraction belong to separate authoring PRs with their own review and replay checks.

| Domain | New / Refined 3D Assets Needed | Notes |
| --- | --- | --- |
| **Shared Instruments (Props)** | Curved, linear, phased-array, and endocavitary ultrasound probes | Extract from `ultrasound-sweep` shared geometry builder into reusable 3D registry with canonical tool frames |
| **Abdomen & Vascular** | `s1233` hepatic veins + IVC junction, extrahepatic bile duct, portal/splenic veins, AAA mural thrombus boundary | `liver_s1233` pilot sets the `s1233` voxel-frame pattern; add separate exports only where reuse or pathology warrants |
| **Neck (Thyroid & Carotid)** | Bilateral thyroid nodules, cervical lymph nodes, carotid plaque/stenosis geometry | Extends `s1127` CT masks + Z-Anatomy carotid survey |
| **Breast & Axilla** | Focal breast lesion / ductal variants, retroareolar & axillary lymph-node context | Currently relies on `models/breasts_hra` (`71 MB` — needs major trim/split) |
| **Obstetric & Cardiac Echo** | Early / 11–14w / mid-trimester / 3rd-trimester fetal anatomy; beating cardiac echo valves & stenosis views | `models/fetus` currently has `0` GLBs; echo builds on `heart/Cardiac_Atlas_Animated` |

---

## 2. Supply landscape by package family

**Consumers legend:** `G` = Gallery · `BS` = Body Systems · `US` = Ultrasound Anatomy · `L:<name>` = standalone lesson.

**Triage legend:** `port` means a metadata-only package change. `trim/split`, `cold-archive`, and `merge?` flag opportunities for later evaluation under the spec’s cleanup and retention gates. Explicit dependencies below include rebuild and Gallery delivery readers. A blank reader column means coverage is unknown.

### 2A. Imported & Multi-Part Atlases (`body/`, `heart/` — 8 pkgs · 353.1 MB)

| Slug | Scope | Payloads (GLB / `.blend` / Other) | LFS (`files · MB`) | Used By | Gov / Review | Triage |
| --- | --- | --- | ---: | --- | --- | --- |
| `body/anatomy-workshop-r1` | `3D-Atlas` | `18` GLB (`46M`), `2` `.blend` (`32M`), `34` PNG | `54 · 81.5 MB` | `G`, `BS`, `US`, `L:one-breath`, `L:pulm-vein` | assessed, recipe | **cold-archive** `.blend`; **port** 18 delivery GLBs |
| `heart/Cardiac_Atlas_Animated` | `3D-Atlas` | `6` GLB (`34M`), `1` `.blend` (`42M`) | `7 · 76.3 MB` | `G` (+ `2` adopted tasks) | **asset.record**, assessed | **pilot (done)**; **cold-archive** `.blend` & full anims |
| `body/breathing` | `3D-Atlas` | `11` GLB (`23.5M`), `2` `.blend` (`50.3M`), `2` WebP | `15 · 74.4 MB` | `G`, `BS` | assessed, recipe | **cold-archive** `50M` `.blend`; **port** 11 GLBs |
| `heart/Cardiac_Atlas` | `3D-Atlas` | `4` GLB (`21.5M`), `1` `.blend` (`42M`), `10` STL | `17 · 72.2 MB` | `G`, `BS` | assessed, recipe | **merge?** with `Cardiac_Atlas_Animated`; **cold-archive** `.blend`/STL |
| `heart/synthetic-imaging` | `Ref/Vol` | `3` `.raw`, `3` `.nrrd`, `3` `.gz`, `1` `.npz`, `7` PNG | `17 · 23.7 MB` | `G`, `US` | — | **outside-3d** (volume/imaging source; cold-archive?) |
| `heart/exterior-presentation-r01` | `3D-Model` | `2` GLB (`17.2M`) | `2 · 17.1 MB` | `G` | recipe | **retain** both r01 exports for the [Gallery library](../sites/anatomy-gallery/app/src/content/gallery/library-packages.json) and [delivery index](../sites/anatomy-gallery/app/src/content/assets/delivery-index.json) |
| `body/2d-v4` | `2D-Outside` | `149` SVG, `20` contact-sheet PNG (`4.5M`) | `20 · 4.5 MB` | `G`, `BS`, `US` | recipe | **outside-3d** (trim contact-sheet PNGs?) |
| `heart/exterior-presentation-r02` | `3D-Model` | `1` GLB (`3.4M`) | `1 · 3.4 MB` | `G` | assessed | **port** (or fold as revision of `heart` exterior) |

### 2B. Heavyweight 3D Models (`models/*` ≥ 5 MB — 23 pkgs · about 401 MB, 85% of model LFS bytes)

| Slug | Payloads | LFS (`files · MB`) | Used By | Gov / Review | Triage |
| --- | --- | ---: | --- | --- | --- |
| `models/breasts_hra` | `2` GLB | `2 · 70.1 MB` | `G`, `US` | assessed, recipe | **trim/split** (top single-package bloat; needed by US) |
| `models/muscle` | `2` GLB | `2 · 53.1 MB` | `G`, `BS` | assessed, recipe | **trim/split** |
| `models/bronchial_tree` | `6` GLB | `6 · 48.4 MB` | `G` | assessed, recipe | **trim/split** + **cold-archive** superseded revs |
| `models/skeleton` | `2` GLB | `2 · 23.8 MB` | `G`, `BS`, `US` | assessed, recipe | **trim/split** (shared across all 3 key surfaces) |
| `models/lung_pair` | `2` GLB | `2 · 24.0 MB` | `G` | assessed, recipe | **trim/split** · **merge?** with `lung_left`/`lung_right` |
| `models/dental_specimens` | `1` GLB (`uff_tomo1b`) | `1 · 20.4 MB` | `G`, `Exp:dental` | assessed, recipe | **trim/split** (keep high-res source cold; lean runtime GLB) |
| `models/blood_cell_study` | `2` GLB (`6.2M`), `1` `.blend` (`8.6M`) | `3 · 14.7 MB` | `G` | assessed, recipe | **cold-archive** `.blend`; **port** GLB |
| `models/bone_marrow` | `2` GLB | `2 · 13.0 MB` | `G` | assessed, recipe | **trim/split** |
| `models/large-intestine` | `2` GLB | `2 · 12.7 MB` | `G`, `BS` | assessed, recipe | **trim/split** |
| `models/lymph_node` | `3` GLB | `3 · 12.7 MB` | `G`, `US` | assessed, recipe | **trim/split** (US axilla consumer) |
| `models/eye_anterior_segment` | `2` GLB | `2 · 12.6 MB` | `G` | assessed, recipe | **trim/split** · **merge?** with `eye_exterior` |
| `models/brain` | `3` GLB | `3 · 11.0 MB` | `G`, `BS`, `L:brain-source-cut` | assessed, recipe | **trim/split** |
| `models/dental-root-support` | `2` GLB (`6.4M`), `4` PNG (`3.2M`) | `6 · 9.5 MB` | `G` | assessed | **trim/split** (convert/drop PNGs) |
| `models/placenta` | `2` GLB | `2 · 9.0 MB` | `G`, `US` | assessed, recipe | **trim/split** (US pregnancy consumer) |
| `models/pharynx_larynx` | `2` GLB | `2 · 8.9 MB` | `G`, `L:one-breath` | assessed, recipe | **trim/split** |
| `models/skin` | `4` GLB, `1` `.blend` | `3 · 8.5 MB` | `G`, `BS`, `US` | assessed, recipe | **trim/split** (shared across all 3 key surfaces) |
| `models/nose_sinuses` | `2` GLB | `2 · 8.4 MB` | `G`, `L:one-breath` | assessed, recipe | **trim/split** |
| `models/tongue_authored_study` | `2` GLB | `2 · 8.2 MB` | `G` | assessed, recipe | **trim/split** |
| `models/prostate` | `2` GLB | `2 · 7.1 MB` | `G` | assessed, recipe | **trim/split** |
| `models/trachea` | `5` GLB | `5 · 6.8 MB` | `G`, `L:one-breath` | assessed, recipe | **cold-archive** older revs; **port** active |
| `models/stomach` | `2` GLB | `2 · 6.4 MB` | `G` | assessed, recipe | **trim/split** |
| `models/spinal_cord` | `3` GLB | `3 · 6.2 MB` | `G` | assessed, recipe | **trim/split** |
| `models/bladder` | `3` GLB | `3 · 5.2 MB` | `G`, `US` | assessed, recipe | **trim/split** (US urinary consumer) |

Package totals include all indexed LFS files, including earlier editions and editable sources. Compare the exact exports loaded by each consumer when evaluating a split.

### 2C. Mid & Lightweight 3D Models (`models/*` < 5 MB — 40 pkgs · about 70 MB)

| Slug | Payloads | LFS (`files · MB`) | Used By | Gov / Review | Triage |
| --- | --- | ---: | --- | --- | --- |
| `models/lung_left` | `2` GLB | `2 · 4.6 MB` | `G`, `L:one-breath` | assessed, recipe | **port** · **merge?** with `lung_right`/`lung_pair` |
| `models/small-intestine` | `2` GLB | `2 · 4.5 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/kidney_left` | `3` GLB | `3 · 4.5 MB` | `G`, `L:kidney-location` | assessed, recipe | **port** · **merge?** with `kidney_right` |
| `models/kidney_right` | `3` GLB | `3 · 4.5 MB` | `G` | assessed, recipe | **port** · **merge?** with `kidney_left` |
| `models/pancreas` | `3` GLB | `3 · 3.9 MB` | `G`, `US` | assessed, recipe | **port** (US abdomen) |
| `models/vagina_hra` | `2` GLB | `2 · 3.8 MB` | `G`, `BS`, `US` | assessed, recipe | **port** (all 3 key surfaces) |
| `models/heart` | `2` GLB | `2 · 3.7 MB` | `G` | assessed, recipe | **port** (check overlap with `heart/*`) |
| `models/diaphragm` | `3` GLB | `3 · 3.6 MB` | `G`, `BS`, `US` | assessed, recipe | **port** (all 3 key surfaces) |
| `models/liver` | `3` GLB | `3 · 3.2 MB` | `G` | assessed, recipe | **Wave 0 dispatch test** · [HRA acceptance](MIGRATION_SPEC.md#hra-liver-acceptance-test); [shared source replay](../assemblies/liver-spleen/recipes/README.md) |
| `models/ears_z` | `2` GLB | `2 · 2.8 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/joints` | `6` GLB | `6 · 2.7 MB` | `G`, `L:right-arm-parts` | assessed, recipe | **port** (multi-asset folder: 4 joints) |
| `models/lung_right` | `1` GLB | `1 · 2.7 MB` | `G`, `L:one-breath` | assessed, recipe | **port** · **merge?** with `lung_left` |
| `models/liver_s1233` | `1` `.mesh` | `1 · 2.2 MB` | `US` (pinned abdomen sweep) | **asset.record**, recipe | **pilot (active)** |
| `models/spleen` | `2` GLB | `2 · 2.1 MB` | `G` | assessed, recipe | **port** |
| `models/gallbladder` | `1` GLB | `1 · 2.1 MB` | `G` | assessed, recipe | **port** |
| `models/swirendo_fdi31` | `1` GLB | `1 · 2.1 MB` | `G`, `L:dental-*` | assessed | **port** |
| `models/vertebrae_L3` | `1` GLB | `1 · 2.0 MB` | `G` | assessed, recipe | **port** |
| `models/peripheral_nerves` | `4` GLB | `4 · 1.8 MB` | `G`, `L:right-arm-parts` | assessed, recipe | **port** (multi-asset folder: 3 nerves) |
| `models/pulmonary_vein` | `1` GLB | `1 · 1.7 MB` | `G`, `L:pulm-vein` | assessed, recipe | **port** |
| `models/salivary_glands` | `4` GLB | `4 · 1.7 MB` | `G` | assessed, recipe | **port** · **merge?** with `parotid_glands` |
| `models/aortic_tree_z` | `2` GLB | `2 · 1.6 MB` | `G`, `BS`, `L:aortic-arch` | assessed, recipe | **port** (compare vs. `models/aorta`) |
| `models/ovaries` | `2` GLB | `2 · 1.4 MB` | `G`, `BS`, `L:ovary-tubal` | assessed, recipe | **port** |
| `models/lymph-collecting-routes` | `2` GLB (`0.04M`), `6` PNG (`1.2M`) | `8 · 1.2 MB` | `G`, `BS` | assessed | **port** (trim PNGs) |
| `models/aorta` | `1` GLB | `1 · 1.2 MB` | `G` | assessed, recipe | **port** |
| `models/teeth_gums` | `1` GLB | `1 · 0.8 MB` | `G`, `L:arch-id`, `L:dental-layer` | assessed, recipe | **port** |
| `models/eye_exterior` | `1` GLB | `1 · 0.7 MB` | `G` | assessed, recipe | **port** · **merge?** with `eye_anterior_segment` |
| `models/adipose-context` | `1` GLB (`0.05M`), `2` PNG (`0.6M`) | `3 · 0.6 MB` | `G`, `BS` | assessed | **port** |
| `models/thyroid_ct_s0189` | `3` GLB | `3 · 0.5 MB` | `G`, `US` | assessed, recipe | **port** (US thyroid) |
| `models/adrenals` | `2` GLB | `2 · 0.3 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/uterus` | `1` GLB | `1 · 0.3 MB` | `G` | assessed, recipe | **port** |
| `models/testes` | `1` GLB | `1 · 0.2 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/esophagus_wall` | `1` GLB | `1 · 0.2 MB` | `G` | assessed, recipe | **port** |
| `models/urethra_male` | `1` GLB | `1 · 0.2 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/parotid_glands` | `2` GLB | `2 · 0.1 MB` | `G` | assessed | **port** · **merge?** with `salivary_glands` |
| `models/hypothalamus` | `1` GLB | `1 · 0.1 MB` | `G` | assessed, recipe | **port** |
| `models/parathyroids` | `2` GLB | `2 · 0.1 MB` | `G`, `BS` | assessed, recipe | **port** |
| `models/penis` | `1` GLB | `1 · 0.1 MB` | `G` | assessed, recipe | **port** |
| `models/thymus` | `1` GLB | `1 · 40 KB` | `G`, `BS` | assessed, recipe | **port** |
| `models/pituitary` | `1` GLB | `1 · 22 KB` | `G` | assessed, recipe | **port** |
| `models/fetus` | No tracked GLB | `0 · 0.0 MB` | Historical study | [Owner](../models/fetus/exports/head-face-junction-r01/README.md) | Keep its existing source and review limits. The pregnancy sweeps use their own gestational recipe. New reusable fetal geometry requires separate authoring. |

### 2D. 3D Assemblies (`assemblies/*` — 16 pkgs · 7.6 MB)

| Slug | Payloads (GLB / `.blend`) | LFS (`files · MB`) | Used By | Gov / Review | Triage |
| --- | --- | ---: | --- | --- | --- |
| `assemblies/marrow-comparison` | `3` GLB (incl. `5.3M` trabecular ref) | `3 · 5.4 MB` | `G` | assessed, recipe | **trim/split** (`5.3M` ref GLB) + **port** |
| `assemblies/endocrine-locator` | `4` GLB, `1` `.blend` | `3 · 0.8 MB` | `G`, `US` | assessed | **port** |
| `assemblies/skeletal-teaching` | `3` GLB, `1` `.blend` | `2 · 0.8 MB` | `G`, `BS` | assessed, recipe | **port** |
| `assemblies/musculoskeletal-teaching` | `2` GLB, `1` `.blend` | `1 · 0.5 MB` | `G`, `BS` | assessed, recipe | **port** |
| `assemblies/hypothalamus-pituitary` | `1` GLB | `1 · 0.1 MB` | `G`, `BS` | assessed, recipe | **port** |
| `assemblies/{cardiovascular-loop,digestive-route,hra-female-pelvis,lymphatic-return,nervous-senses,reproductive-tracts,urinary-junctions}` | `0–2` GLB/blend each (non-LFS / recipe-backed) | `0 · 0.0 MB` | `G` (+ `BS` system stops) | mixed (`hra-female-pelvis` assessed) | **port** (7 lightweight Body Systems compositions) |
| `assemblies/workshop-s1233` | recipe only | `0 · 0.0 MB` | `US` | recipe | **retain** case/grid and composition recipes for ultrasound and two Body Systems survey outputs; track their replay separately from runtime |
| `assemblies/kidney-pair` | recipe only | `0 · 0.0 MB` | `L:kidney-location` | recipe | **port** |
| `assemblies/bladder-pancreas` | recipe only | `0 · 0.0 MB` | [Bladder](../models/bladder/README.md), [pancreas](../models/pancreas/README.md) | shared replay | **retain** until both readers have a verified replacement |
| `assemblies/liver-spleen` | recipe only | `0 · 0.0 MB` | [Liver](../models/liver/README.md), [spleen](../models/spleen/README.md), [bladder/pancreas recipe](../assemblies/bladder-pancreas/recipes/recipe/dependency-map.json) | shared replay | **retain**; required by the HRA port |

### 2E. Outside 3D AssetKit (`diagrams/*` — 4 pkgs · 1.8 MB)

| Slug | Payloads | LFS (`files · MB`) | Used By | Triage |
| --- | --- | ---: | --- | --- |
| `diagrams/{testis_pathway,oral_spaces,biliary_pathway,urinary_outflow}` | `4–8` SVG + `2–4` PNG each + `render.py` | `8 · 1.8 MB` | `G`, `BS` | **outside-3d** (leave with illustration packages) |

---

## 3. Wave assignments

| Wave | Inventory focus |
| --- | --- |
| 0 | Existing s1233 liver sweep integration and the HRA liver's selected teaching edition. The HRA port is the required batch acceptance test. |
| 1 | Existing Ultrasound Anatomy exports from Workshop s1233, endocrine locator, and the named organ packages. Record missing or recipe-only inputs as gaps. |
| 2 | Body Systems assemblies, breathing, cardiac assets, and their named lesson and Gallery readers. |
| 3 | Remaining maintained Gallery 3D exports, including independent assets under joints and peripheral nerves. Record deferred standalone lesson references. |

Use the [wave exit criteria](MIGRATION_SPEC.md#package-and-wave-acceptance) to assign exact assets and reader pins. Use the [cleanup backlog](MIGRATION_SPEC.md#post-port-cleanup) to evaluate heavy exports, archives, and retention after the applicable wave.
