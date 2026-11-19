# Body-systems gallery · next-round build specification

Draft · 19 November 2026 · Baseline `ba0bf3d6be59adfa7065cb5cefea8f442476121b`

Refine all eleven systems so a learner can orient themselves in the overview,
find the important structures, and follow one route or compare one movement.
Use source assets as fidelity references. Build clean teaching geometry where
the source is rough, crowded or incomplete. Keep a labeled teaching route
available wherever a connection is inferred. Sequence the work below so the
digestive and cardiovascular builds establish the visual standard before it
is applied across the gallery.

## Verified baseline

| Coverage | Current systems and remaining gap |
| --- | --- |
| Five native or shared-frame overviews | Skeletal, muscular, respiratory, urinary and reproductive. Their missing work is regional legibility, motion presentation or clearer joins. The two reproductive plates have separate regional frames. |
| Two partial assemblies | Digestive and cardiovascular. Same-case s1233 overviews improve spatial fidelity. Complete route demonstrations currently live in separate schematics. |
| Three illustrative placements | Nervous, endocrine and lymphatic. Each has regional teaching detail. The overview placement, scale or joins need better context. |
| One body locator | Integumentary. The envelope and the two local sections need an explicit locator-to-detail relationship. |

- **Local gallery** · The report validator bound 69 view pairs to their exact
  GLBs and images across 21 render scenes. Disposable Chrome passed 11 system
  sections, 12 assembly plates, 58 detail plates, 232 unique image decodes
  and 24 WebGL launches. The run covered keyboard orbit, missing-model fallback
  and retry, and 1024 px reflow. The gallery viewer uses static model launches.
  One Breath has separate breathing and airway evidence.
- **s1233 checks** · All 13 source-mask identities, dimensions and affines
  matched the manifest. Recounting the colon at 6-connectivity yielded
  122,899, 38,714 and 35 voxels. The two largest components were 24.602 mm
  apart by nearest occupied voxel centres. The four consecutive digestive
  label pairs have minimum boundary distances of 0, 0, 1.5 and 1.5 mm.
  Heart/major-vessel masks overlap at the boundary. These measurements
  establish proximity and component coverage. Lumen and chamber connections
  require local landmarks or imaging evidence.
- **Source leads** · The wider retained s1233 label set has thyroid, bilateral
  adrenal and left atrial appendage landmarks for feasibility checks. Its
  brain mask is empty and its spinal cord mask reaches the superior grid
  face. Use it as a candidate regional reference and screen for truncation.
- **Visual baseline** · Voxel stair-steps are prominent in the two same-case
  overviews. The liver occludes much of the stomach. The long nervous view
  makes the root junction small. The endocrine frontal view partly hides the
  adrenals behind the pancreas. The lymphatic view combines the enlarged node
  with organs and a long duct at a different teaching scale.

Repository offline verification passed 434 tests at the baseline revision.
The audit used local inputs, rendered evidence and Chrome. Specialist review,
source CT interpretation, full payload verification and hosted verification
remain outside this audit.

[Current gallery and replay](README.md) · [Previous teaching brief](study-brief.md) ·
[s1233 source and build](../../assemblies/workshop-s1233/README.md) ·
[Gallery glossary](../../GLOSSARY.md)

## What the learner sees

1. **System assembly** opens with a calm, readable view of the main structures.
   Use matte materials, a restrained palette, a stable anatomical orientation
   and subdued context. Keep related structures visually consistent across
   systems. Use labels, arrowheads and line or surface treatment to carry
   distinctions in grayscale.
2. **Teaching route** is a separate selectable layer in the assembly where
   spatial context helps. Show ordered direction cues and named junctions.
   Keep inferred segments visually distinct and label them at the point of
   use. Where a full route would obscure the anatomy or cross incompatible
   frames, use a linked teaching detail with an explicit transition from the
   overview.
3. **Asset detail** isolates a crowded junction, alternate pose or magnified
   section. Give each an overview locator and label enlarged or separate
   scales. Use a cutaway or selective transparency when it makes the target
   easier to locate. In a matched comparison, hold camera, scale and anatomy
   alignment fixed. Present separately framed reference assets side by side.

Start with the existing geometry, camera and selection controls. Smooth,
retopologize or author a derivative only to solve a visible problem or make
a learner action possible. Keep the original available as a fidelity
reference. Before editing, identify the landmarks, section relationships and
components the derivative must preserve. Use close reference comparisons for
these features. Track cleanup, deliberate shape simplification and authored
connections separately in the owner record.

## Build sequence and acceptance

### 1. Digestive and cardiovascular

| System | Build or refine | Done when |
| --- | --- | --- |
| Digestive | Make a clean esophagus-to-colon overview from the s1233 references. Preserve the gastric and bowel landmarks and the recorded colon discontinuity in the source reference. Give the stomach, duodenum and ileocecal region focused reveals. Bring in the existing mouth-to-outlet route and an accessory secretion detail. Use source slices or a corroborating trace for any claimed local join. Where these fall short, use a named illustrative bridge or detail. [Existing route](../../reviews/digestive-route/r01/README.md) | A learner can trace mouth to outlet and locate bile and pancreatic entry. With context turned down, the learner can identify the gastric inlet and outlet, the intended ileocecal transition and the colon gap. Source, cleaned geometry and inferred connections are distinguishable in the actual view. The 24.602 mm measurement remains attached to its source mask. |
| Cardiovascular | Refine the s1233 heart and great-vessel overview for silhouette and visibility. Use the [Cardiac Atlas cutaway and proximal vessels](../../heart/Cardiac_Atlas/docs/README.md) as references for a clean heart-centered detail. Check local landmarks for pulmonary arterial outflow, venous entry and the valve planes before aligning models. Use two heart-side reveals and the existing circuit as the basis for directional teaching. Keep distal beds visibly schematic. [Existing loop](../../reviews/cardiovascular-loop/README.md) | A learner can trace a full circuit and distinguish pulmonary arterial outflow from pulmonary venous return. Right and left valve transitions are readable in their respective views. Each demonstrated vessel-to-chamber join has a named landmark or an inferred label. The four s1233 venous mask components retain their source identity until individual names are evidenced. |

Review these two systems together for the default material, section, route
and legend treatment. Use actual, matched clean-import views for the review.

### 2. Nervous, endocrine and lymphatic

| System | Build or refine | Done when |
| --- | --- | --- |
| Nervous | Add restrained body context to the brain–cord–right sciatic teaching route. Use source regional landmarks for head, lower spine and pelvis. Isolate one root, ganglion and plexus transition to resolve the overlap. Keep the five sensory insets at their own scales and provide regional entry points. [Existing senses and placements](../../reviews/nervous-senses/README.md) | A learner can locate the right sciatic pathway in the body and follow the selected afferent to the brainstem. The root and ganglion read without overlaid neighboring roots. The five insets still expose their respective receptors and first pathway steps. The upper s1233 cord truncation and empty brain mask constrain any same-case claim. |
| Endocrine | Qualify the s1233 thyroid, adrenals and pancreas as candidate neck and abdominal references. Refine head-to-pelvis context using documented regional landmarks. Provide a posterior view for parathyroids and adrenals. Keep alternate gonads and islet at separate scales and the TRH/TSH arrows selectable. [Existing locator](../../reviews/endocrine-locator/r01/README.md) | A learner can locate each gland in the intended set and trace the two signal steps. Neck and abdominal labels work with the context remaining visible. Laterality, regional reference frames and authored placements are explicit. |
| Lymphatic | Add subtle torso landmarks to orient the duct and left venous angle. Use the existing duct and node as references, and a local vein study to qualify the terminal join. Separate the enlarged node transit and spleen/thymus locator views from the main route where they compete with it. [Existing return study](../../reviews/lymphatic-return/r01/README.md) | A learner can follow tissue → node → collecting duct → venous angle and distinguish spleen/thymus landmarks from that route. The venous angle reads in an isolated view. Node enlargement and the authored terminal join are visible qualifications. |

### 3. Native and regional assemblies, and the integumentary locator

| System | Build or refine | Done when |
| --- | --- | --- |
| Skeletal | Connect the whole-body skeleton to a same-scale, fixed-camera right-knee comparison at source pose and +20°. Improve compartment visibility with a complementary view. Reuse checked landmarks and qualitative load arrows. [Current knee evidence](../../reviews/joints/knee-motion-r01/README.md) | A learner can find the knee, distinguish both poses and identify medial and lateral landmarks and load directions. A clean import repeats the pose and clearance checks. |
| Muscular | Bring the calf–Achilles–heel chain into a focused neutral/15° comparison. Screen the inherited fibula–talus intersection and the scalloped insertion seam before local cleanup. Preserve the sampled attachment relationship. [Current plantarflexion evidence](../../reviews/muscle/plantarflexion-r01/README.md) | The gastrocnemius/soleus–Achilles–heel chain and pose change remain visible in both views. A replay checks all five poses, reports intersection and attachment distances, and records remaining source limitations. |
| Respiratory | Make the thoracic overview a clear entry into the existing sagittal airway, branching and enlarged terminal views. Show lobes and airway hierarchy legibly at rest and inspiration. Keep the One Breath exchange handoff. [Current airway evidence](../../reviews/one-breath/airway-r01/README.md) | A learner can trace nose to a named lobar branch and on to the terminal detail, then open exchange. Both phases preserve the intended route stages and visible junctions. Mark the compressed distal airway and enlarged terminal detail. |
| Urinary | Refine seams at the renal-pelvis/ureter and ureter/trigone transitions locally. Give each side and the bladder outlet accessible isolated views. Keep the filtration inset at its own scale. [Current junction evidence](../../reviews/urinary-junctions/r01/README.md) | A learner can trace both kidneys to the shared outlet and see every required join in a focused view. Bilateral clean-import checks establish the intended geometric contacts. Continue to label the authored ureter and filtration detail. |
| Reproductive | Refine the paired pelvis presentations independently. Show the open fimbria–ovary pickup and tubal entry in the female view. In the male view reveal the epididymis-to-outlet route and both vesicle contributions behind bladder/prostate. Keep the breast study linked. [Current tract evidence](../../reviews/reproductive-tracts/r01/README.md) | A learner can distinguish pickup from a fused tube and trace each tract through the relevant junctions. Clean import preserves laterality, separate frames, both open pickup gaps and male duct provenance. |
| Integumentary | Add illustrative skin and nail locator callouts to the envelope. Improve the section faces and isolation of the coil-to-pore path and nail matrix. Use the existing sections as reference for essential contacts. [Current section evidence](../../reviews/skin/teaching-block-r01/README.md) | A learner can get from the locator to each section and identify skin layers, follicle, sweat outlet, nail plate, bed and matrix. Cut faces and alternate angles expose each relationship. The locator and enlarged section scales are labeled. |

## Evidence and delivery

- **Admit each derivative** with the baseline and a matched candidate. Name
  the audience, learner action, source owner and the visible improvement.
  Reuse an existing export when camera, layering or isolation closes the gap.
- **Package geometry changes** as editable source, portable GLB, pinned
  inputs and replay under the owning asset or assembly. Record axes, units,
  laterality, transforms, per-structure derivation and attribution. Record
  local tolerances before cleanup, tied to the source resolution and the
  feature's purpose. Report displacements at selected landmarks and summarize
  surface deviations where they matter. Check component preservation,
  clipping, unintended intersections and new connections. Keep source
  coverage and teaching continuity explicit in the gallery and review.
- **Review the delivered view** using matched-scale isometric and straight
  orthographic renders from a clean GLB reimport, plus a close view for each
  critical junction. At laptop scale, inspect default and isolated views for
  label collisions, silhouettes, route crossings and grayscale readability.
  Each view should have one main anatomical question that a reviewer can
  answer from the delivered plate.
- **Exercise the local gallery** through its normal entry points. Verify 11
  sections, assembly-to-detail navigation, keyboard access, route visibility,
  context reset, static fallback and failed model load/retry. If adding pose
  or phase controls, verify the exported state at each stop. The current
  viewer loads static scenes and needs bounded pose behavior or explicit static
  pose views for those comparisons.
- **Run the owning replay and relevant negative case** from fresh outputs.
  Verify exact candidate and render identities, run the repository offline
  gate, and apply payload integrity for the broad hydrated delivery. Record
  technical, visual, anatomy and runtime results independently. Use a clean
  checkout or fresh output to exercise recovery, including a deliberately
  incomplete optional s1233 bundle.

**Repository follow-ups.** The gallery README now identifies both the s1233
and fallback digestive and cardiovascular views. The owner README and report
copy give the measured colon gap. `prepare.py` emits the component count in
`mask-audit.json`. Add the individual sizes and measured separation to that
receipt and use its values for the gallery copy.
`gallery_plan.py` activates optional s1233 scenes when it finds
`assemblies.json`. `report.py` then requires all expected render receipts.
An interrupted restore can therefore block the entire report. Validate
bundle readiness before enabling those scenes and report actionable recovery
information for incomplete or invalid additions.

Local builds and review complete this round. Any hosted integration should
use the owning gallery source and a separate publication decision.
[Repository workflow and verification gates](../../docs/WORKFLOW.md)
