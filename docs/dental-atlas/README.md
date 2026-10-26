# Dental teaching assets — research and component specification

**Status: research only; 2026-10-26. No new meshes, completed dental atlas, clinical simulator or anatomy approval.**

## Goal and deliverable

Build realistic, reusable dental assets for downstream illustrations and future procedural demonstrations. Cover **32 permanent + 20 primary teeth**, each individually named and selectable, with independently addressable tissue/components where evidence supports them. Add necessary condition, instrument and material assets. This PR specifies the inventory and evidence gates first; it does not manufacture unsupported anatomy.

`inventory.json` is the single machine-readable inventory. Its 52 tooth records inherit one compact component template rather than duplicating 52 files. `validate_inventory.py` checks naming, counts, hierarchy, references and explicit missing-geometry state. Primary teeth are not scaled adult teeth. Adult and primary are separate scenes/cohorts, not a mixed-dentition mouth with52 erupted teeth.

## Single-file scene contract

```text
DentalAtlas
 ├─ permanent
 │   ├─ maxillary / tooth_11 … tooth_28
 │   └─ mandibular / tooth_31 … tooth_48
 ├─ primary
 │   ├─ maxillary / tooth_51 … tooth_65
 │   └─ mandibular / tooth_71 … tooth_85
 └─ demonstration_assets / conditions / instruments / materials
```

- Future GLB: one file, named nodes/meshes, independent selection/hide/explode; no fused mouth. Keep source `.blend` separately for editing. Current deliverable is JSON/docs, **not** GLB.
- FDI quadrant and side always mean **patient** side. Each tooth label carries dentition, arch, side and type. No primary premolars or third molars. Anatomical absent/missing/unerupted differs from unavailable source coverage.
- Per-tooth components: exterior proxy; enamel; dentin; cementum; pulp tissue; pulp cavity, chamber and observed canal branches; PDL. Crown/root regions, CEJ, apical foramina and surface landmarks are annotations, not duplicate tissue volumes. A cavity mask is not verified soft pulp tissue.
- Pulp cavity is a parent space/render proxy; chamber and canals partition or annotate that space. Do not add parent and child volumes together, render duplicate overlapping solids, or relabel the space as verified pulp tissue.
- Gingiva and alveolar support are shared arch nodes, with tooth/socket region annotations. Do not duplicate interdental papillae or bone under each tooth.
- Subdivide roots/canals only when the specimen supports it. Store observed names/counts, not assumed class-wide values. Primary assets also need eruption, root formation and physiological resorption stages.
- Root/bone/gingiva support must be inspectable together; an isolated root is not proof of an exposed-root defect. Keep intact and cutaway states distinct. Section caps are rendering aids, not anatomical surfaces.

## Evidence and source feasibility

| Candidate | Useful for | Limit / next gate |
|---|---|---|
| [ToothFairy3](https://ditto.ing.unimore.it/toothfairy3/) | Permanent tooth and pulp-cavity label extraction; jaws/support context | Account required. Confirm actual download license/version before reuse; NC-SA terms reported by indexed challenge page are not a verified downloaded license. No separate enamel/dentin/cementum/PDL labels verified. Check `dataset.json` rather than guessing77 foreground labels. Official orientation is RPI; preserve affine and verify patient laterality. |
| [ToothFairy2](https://toothfairy2.grand-challenge.org/dataset/) | Adult exterior/support alternative | Official benchmark metadata says CC-BY-SA4.0; challenge description also says research-purpose use. Reconcile actual access agreement before redistribution; do not inherit its license onto ToothFairy3. No verified pulp-layer labels. |
| [Pulpy3D](https://ditto.ing.unimore.it/pulpy3d/) | Mandibular pulp/canal candidate annotations | Account-gated, not a full upper/lower atlas. Current portal advertises423 scans; paper describes original443-scan basis. Actual archive count and derivative-license clearance unverified. |
| [LMU SWIRendo](https://data.ub.uni-muenchen.de/477/) | Candidate microCT layer reference |9 prepared teeth; public metadata states CC BY-SA4.0, archive not inspected. After7mm access preparation; not a complete healthy adult/primary atlas. Verify preparation state and actual license before deriving meshes. Never splice unregistered internals into another tooth. |
| Existing `models/teeth_gums/exports/r02/` | Exterior reference in BP3D native atlas frame | Existing review scope:28 teeth +2 gingiva surfaces, static exterior only. Not32 permanent/20 primary; no internal tissues. Preserve existing study unchanged. Source attribution must be checked before reuse. |
| [CENIEH measurements](https://doi.org/10.5281/zenodo.20487337) | Primary crown dimensional reference |712 measurements; CC BY4.0 metadata. Not meshes or internal anatomy. |
| [Habi microCT cohort](https://github.com/habi/zmk-tooth-cohort) | Mandibular canine research lead |2 example datasets linked; other data on request; dataset-specific license unverified. Not redistribution-cleared. |
| Primary dentition | FDI51–55,61–65,71–75,81–85 can be specified now | No complete redistributable layered20-tooth source verified; do not promise extraction coverage. |

Public metadata only: no archives downloaded, accounts created or terms accepted. ToothFairy label availability does not guarantee all32 teeth in any single case. Keep asset licenses distinct from code licenses; educational intent alone does not clear NC restrictions.

Existing repo source map: `sources/datasets/bp3d-4.0-head-studies/external-source-map.json`; attribution: `models/teeth_gums/exports/r02/ATTRIBUTION.md`; bounded reviews: `reviews/teeth_gums/2026-10-24-r02-bounded-migration/`. These are dependencies to inspect, not new license approvals. Existing display snapshot binds r02 to SHA-256 `82bfaeead46bb51b1fa5bdfdb06c918dfd01aa23b28acae733ab75ec2cd6897f`; reconfirm canonical bytes before derivative work.

## Reusable demonstration inventory

Priorities are production ordering, not clinical urgency. All are **planned**, not acquired or approved. Tools are generic; device-specific dimensions/connectors need manufacturer evidence and redistribution clearance.

| Illustration family | Anatomy / condition states | Reusable assets | Priority |
|---|---|---|---|
| Tooth structure / primary-versus-permanent | Distinct tooth morphology, tissues, cutaways; stage-labelled primary roots | Labels, landmarks, section planes |P1|
| Restorative | Intact, localized caries, preparation and restored variants | Isolation kit, handpiece/bur, excavator, matrix/wedge, restorative material, curing tip |P1|
| Endodontic | Pulp-space anatomy and independently selectable referenced states | Dam, hand/rotary files, stops, syringe/tip, paper/gutta-percha points, sealer, temporary restoration, crown/post |P1|
| Periodontal | Deposits, gingival changes, pocket and bone-loss examples | Probe, scaler, curette, ultrasonic tip |P2|
| Extraction / impaction | Position/context, root and socket variants | Adult/paediatric forceps, elevators, surgical/retraction/suture assets |P2|
| Implant restoration | Missing tooth/ridge and assembly variants | Implant body, abutment, fixation screw, crown, driver/drill |P3|

Crack/fracture, pulpal/apical disease and impaction need dedicated pathology references before geometry authoring. The catalog does not endorse diagnosis from a rendered appearance. No operation sequence, dose, speed, torque, force or treatment settings are specified.

## Realism and acceptance gates

1. **Source gate:** accession/version, actual license terms, attribution, file hashes, label map, source permissions and de-identification/public-redistribution suitability. Do not publish raw patient scans or identifying metadata.
2. **Geometry gate:** non-generic class-specific crowns, cusp/ridge/fossa/incisal detail where resolved; root divergence/furcation and tissue boundaries preserved from evidence. No procedural cones, repeated crowns or scaled adult substitutes for primary anatomy.
3. **Coordinate gate:** keep each specimen/frame separate; record units, NIfTI affine, any handedness conversion, export transform and registration evidence. Check patient right/left against known landmarks. Never merge BP3D, authored mouth and CBCT frames by appearance alone.
4. **Extraction gate:** inspect actual labels/voxel spacing; surface extraction then conservative cleanup. Log smoothing/decimation and source-to-mesh deviation relative to resolution; no smoothing invented canals. Mesh closure/connectedness checks must accommodate genuinely open boundaries.
5. **Presentation gate:** intact, isolated, cutaway and exploded views; tooth/tissue selection; all52 names unique; missing parts visible as coverage warnings, not silently hidden. Adult/primary switching cannot accidentally show both as one mouth. Materials distinguish tissue without hiding source resolution limits.
6. **Instrument gate:** measured scale, handle/grip pivot, working tip/edge, axis and compatible attachment frames; separately selectable replaceable parts. Contact markers aid animation but are not validated collision/contact mechanics.
7. **LOD gate:** retain source-resolution master; separately verified teaching/display derivatives. Report triangle counts and measured simplification error; no universal triangle target. Do not remove canal branches, thin tissue boundaries or diagnostic landmarks merely to meet a budget.
8. **Review gate:** technical checks, rendered multi-view inspection and dentist/anatomist review are separate statuses. Inspect representative anterior/premolar/molar upper/lower classes and every exception, then all delivered teeth. No claim of dentist-teaching suitability until scoped professional review.

## Next executable work

- Review this spec and its gaps; confirm source download rights/access before acquisition.
- Inspect actual dataset labels and coverage; choose a documented representative adult specimen, not an invented complete patient.
- Acquire a licensed primary source or explicitly commission/reference-author primary anatomy; this remains a separate blocker.
- Pilot one adult anterior and one molar with supported layers, plus one primary tooth only when evidence exists. Validate frames, tissue semantics and review workflow before scaling to52.
- Add one coherent restorative/endodontic asset family after dimensions/reference clearance. Keep variants modular; do not create a new framework or dozens of boilerplate folders.

Nomenclature: [ADA tooth designation/ISO mappings](https://www.ada.org/-/media/project/ada-organization/ada/ada-org/files/publications/cdt/universal_tooth_designation_system_valueset_2.pdf). Basic tissue distinctions: [ADA tooth anatomy](https://www.mouthhealthy.org/all-topics-a-z/tooth/). Context only, not geometry licenses: [NIDCR fillings](https://www.nidcr.nih.gov/health-info/dental-fillings), [NIDCR gum disease](https://www.nidcr.nih.gov/health-info/gum-disease), [AAE root canal overview](https://www.aae.org/patients/root-canal-treatment/what-is-a-root-canal/root-canal-explained/), [FDA implants](https://www.fda.gov/medical-devices/dental-devices/dental-implants-what-you-should-know), [NHS training equipment guide](https://heeoe.hee.nhs.uk/sites/default/files/educational_supervisor_information_guide_24-25_v1.pdf). No source illustrations copied.
