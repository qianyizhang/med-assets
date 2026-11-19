# Body-systems gallery · next-round build specification

Draft · 19 November 2026 · Baseline `ba0bf3d6be59adfa7065cb5cefea8f442476121b`

Refine all eleven systems for two uses. A learner can orient, follow a route or
compare a movement in the gallery. An author can take a named regional group
into a lesson, a close-up or a future animation. Use source assets as fidelity
references. Build clean teaching geometry where the source is rough, crowded
or incomplete. Keep a labeled teaching route wherever a connection is inferred.
Start with digestive and cardiovascular to establish the visual and reuse
standard for the rest of the gallery.

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
- **Reuse baseline** · The existing exports already contain several useful
  selections. The circulation GLB has named annuli and leaflets. The urinary
  GLB has individual calyces, pyramids and filtration structures. The skin GLB
  has separately named layers, appendages and nail structures. The local viewer
  combines these into broader rule-based visibility groups and substitutes
  matte materials. The calf GLB carries a skin and clip. One Breath's lung
  GLBs and the separate Cardiac Atlas heartbeat edition carry animation clips.
  The gallery's current static launches do not play them.
  [Viewer source](viewer/viewer.mjs) · [Calf rig](../../assemblies/musculoskeletal-teaching/plantarflexion-r01/README.md) ·
  [One Breath](../../lessons/one-breath/README.md) ·
  [Animated heart](../../heart/Cardiac_Atlas_Animated/README.md)

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
   A local exploded view is appropriate where separation reveals an interface,
   such as a valve leaflet at its annulus or the nail plate over its bed and
   matrix. Pair it with the assembled view, make the displacement reversible
   or clearly illustrated, and keep the assembled placement in the export.

Start with the existing geometry, camera and selection controls. Smooth,
retopologize or author a derivative only to solve a visible problem or make
a learner action possible. Keep the original available as a fidelity
reference. Before editing, identify the landmarks, section relationships and
components the derivative must preserve. Use close reference comparisons for
these features. Track cleanup, deliberate shape simplification and authored
connections separately in the owner record.

## What the author can reuse

- **Parts and labels** · Start with the proposed lesson, cutaway, replacement
  or motion. Make a part independently selectable when that use needs to name,
  hide, move, shade or extract it. Use an existing named mesh or group where
  possible. Keep the overview at organ or regional level and expose finer
  selections in context. Give qualifying parts a persistent identity and a
  readable label with laterality or segment when relevant. Reuse the owner's
  `anatomy_id`, `view_role` and derivation conventions where present. Keep labels
  and arrows separate from the reusable anatomy. A labeled region of a
  continuous wall can use a surface selection or a section. Create detachable
  geometry only when the intended use calls for it. Verify a representative
  selection in a clean scene with its local transform, materials and source
  credit intact. Keep one assembly export with named parts unless a known
  consumer needs a separate file.
- **Interiors** · Build an interior when it explains a route, layer, opening,
  moving interface or attachment. Preserve the exterior and provide a focused
  section with the corresponding wall, cut face and interior structures
  distinguishable. Retain relevant openings, rims and partner surfaces. Teach
  a named example where the source does not support a full internal model.
  Mark authored interiors and keep them selectable apart from source-derived
  anatomy. Inspect the clean export both assembled and isolated, including the
  geometry exposed when a wall is hidden.
- **Geometry economy** · Favor the lighter candidate when matched overview
  and teaching close-up show equivalent shape, shading and readability. Keep
  smooth curved silhouettes and enough geometry for apertures, wall rims,
  contact surfaces and deformation. Remove redundant surfaces and fine detail
  that add no insight across the intended views, selections and poses. Use
  simple geometry and smooth shading where they preserve shape. Inspect cut
  edges, normals, seams and silhouettes. Compare exported triangles,
  primitives and file size for the same scope. Apply extra care at part
  boundaries, and preserve compatible topology, UVs, skin weights and morph
  targets where the asset already depends on them.
- **Motion** · Preserve and reuse the calf skin and clip, One Breath morphs,
  and the authored heartbeat edition in their own scopes. The knee is the first
  candidate for a small reusable rigid pivot if it can reuse the current two
  checked poses. Record parent, pivot, axis and rest transform for moving parts.
  Add an armature for driven or skinned motion and use shape keys or transforms
  where they fit the movement. Any new rig or clip must survive clean reimport
  and preserve the checked landmark relationship in representative poses. If
  weights, new motion evidence or playback work would dominate a package, keep
  its separable parts and motion landmarks and defer the rig. Defer a whole-body
  rig sweep and new soft-tissue motion such as peristalsis to a separate round.
- **Materials** · Use named, editable materials for surfaces whose appearance
  helps explain the anatomy. Consider a mucosal surface and neutral section face
  for the digestive cutaway, valve tissue distinct from muscle and flow cues in
  the heart, and epidermis, dermis and nail plate in the skin section. Start
  with a small reusable set of base color and roughness assignments. Add maps
  or relief only if a named close-up benefits. Keep a categorical teaching
  palette available and distinguish surface appearance from schematic signals.
  Verify dedicated materials on the reimported GLB. If a gallery view is meant
  to show them, exercise a material-preserving view alongside the current
  categorical override. [Workshop materials](../../body/anatomy-workshop-r1/README.md#uvs-and-textures) ·
  [Look development evidence](../../docs/material-lookdev-research.md)

## Build sequence and acceptance

### 1. Digestive and cardiovascular

| System | Build or refine | Done when |
| --- | --- | --- |
| Digestive | Make a clean esophagus-to-colon overview from s1233. Reveal gastric inlet, outlet and the intended ileocecal transition. Make a reusable stomach–duodenum section with wall, mucosal surface and pyloric opening, and let the learner isolate the bile and pancreatic ducts where they enter the duodenum. Reuse the mouth-to-outlet schematic. Require local evidence for source-backed joins and label illustrative bridges. [Existing route](../../reviews/digestive-route/r01/README.md) | A learner can trace mouth to outlet and find both duct entries. An author can extract the stomach–duodenum section with its labeled interfaces and materials. The cleaned overview distinguishes inferred links, and the source reference retains the recorded 24.602 mm colon gap. |
| Cardiovascular | Refine the s1233 heart and great vessels. Reuse the [Cardiac Atlas cutaway and proximal vessels](../../heart/Cardiac_Atlas/docs/README.md) for a focused interior with chamber walls, septum, chamber spaces, annuli and leaflets distinguishable. Reuse the existing circuit with schematic distal beds. Trial a local exploded annulus/leaflet view where it clarifies seating or attachment. Check landmarks for pulmonary arterial outflow, venous entry and valve planes before alignment. [Existing loop](../../reviews/cardiovascular-loop/README.md) | The full circuit, arterial outflow, venous return and both sides' valve transitions are readable. A valve set can be reused in its assembled pose and isolated with its supporting anatomy where relevant. Each demonstrated vessel-to-chamber join has a landmark or an inferred label. The four s1233 venous components keep their source identities until individual names are evidenced. |

Use the stomach–duodenum section and one valve set as the first reuse trials.
Review material, section, route and legend treatment in matched clean-import
views. Check that the same parts can be used outside their gallery scene.

### 2. Nervous, endocrine and lymphatic

| System | Build or refine | Done when |
| --- | --- | --- |
| Nervous | Add restrained body context using regional head, lower spine and pelvis landmarks. Keep the dorsal and ventral roots, ganglion and plexus transition independently selectable. Treat the five sensory insets as separate teaching groups at their own scales. In the ear detail, let the auditory and vestibular structures be isolated. [Existing senses and placements](../../reviews/nervous-senses/README.md) | A learner can follow the selected right sciatic afferent to the brainstem and inspect the root/ganglion without overlaid neighbors. Each sensory group exposes its receptor and first pathway step. The upper s1233 cord truncation and empty brain mask constrain any same-case claim. |
| Endocrine | Qualify the s1233 thyroid, adrenals and pancreas as candidate neck and abdominal references. Refine head-to-pelvis context. Let a posterior thyroid/parathyroid group and an adrenal pair be reused independently of the locator. Keep alternate gonads and islet at separate scales and the TRH/TSH signals separate from the gland geometry. [Existing locator](../../reviews/endocrine-locator/r01/README.md) | A learner can locate each gland and trace the two signal steps. Neck and abdominal labels work with context visible. Laterality, frames and authored placements are explicit. |
| Lymphatic and immune | Add torso landmarks to orient the duct and left venous angle. Qualify the terminal join against a local vein study. Make an enlarged node detail with capsule, afferent and efferent vessels, and illustrative internal passage independently selectable. Keep spleen and thymus available as a separate locator view. [Existing return study](../../reviews/lymphatic-return/r01/README.md) | A learner can follow tissue → node → collecting duct → venous angle. The terminal join reads in isolation and the node can be reused for an entry-to-exit section. Node enlargement and the authored terminal join are visibly qualified. |

### 3. Native and regional assemblies, and the integumentary locator

| System | Build or refine | Done when |
| --- | --- | --- |
| Skeletal | Link whole-body context to a fixed-camera right knee at source pose and +20°. Retain separate femur, tibia and fibula and preserve the tibia–fibula motion grouping. Give the compartment landmarks a complementary view. Keep load arrows optional. [Current knee evidence](../../reviews/joints/knee-motion-r01/README.md) | A learner can identify poses, medial/lateral landmarks and load directions. A clean import repeats the pose and clearance checks. The regional group can be posed without the full skeleton. |
| Muscular | Isolate the two gastrocnemius heads, soleus, Achilles tendon and hindfoot in a neutral/15° comparison. Preserve the existing skin, clip and sampled attachments. Screen the inherited fibula–talus intersection and insertion seam before cleanup. [Current plantarflexion evidence](../../reviews/muscle/plantarflexion-r01/README.md) | The chain reads in both poses with muscle, tendon and bone distinguishable. Replay checks all five poses and reports intersections, attachment distances and remaining source limits. |
| Respiratory | Keep each lobe, the airway tree and diaphragm selectable in context. Provide a reusable tracheal cutaway, with wall and cartilage distinguishable, and an independently framed terminal detail. Keep the existing lung morphs and One Breath exchange handoff. [Current airway evidence](../../reviews/one-breath/airway-r01/README.md) | A learner can trace nose to a named lobar branch and terminal detail, then open exchange. Rest and inspiration preserve the intended route stages and junctions. Compressed distal airways and enlarged terminal geometry are labeled. |
| Urinary | Refine renal-pelvis/ureter and ureter/trigone seams locally. Keep the collecting system, kidney section and ureter selectable by side. Let an author extract the collecting-system section or the enlarged filtration group without the full tract. [Current junction evidence](../../reviews/urinary-junctions/r01/README.md) | A learner can trace both kidneys to the shared outlet and see each join in isolation. Bilateral clean-import checks establish geometric contacts. Authored ureters and enlarged filtration remain labeled. |
| Reproductive | Refine the pelvis presentations independently. Keep the ovary/fimbria, tube and uterine entry as a reusable female detail. Keep the vas and vesicle confluence separately visible behind bladder/prostate. Expose the verified extent of the urethral route in section where the exterior hides it. Keep the breast study linked. [Current tract evidence](../../reviews/reproductive-tracts/r01/README.md) | A learner can distinguish open pickup from a fused tube and trace each route. Clean import preserves laterality, both open pickup gaps, distinct regional frames and the authored male duct provenance. |
| Integumentary | Add illustrative skin and nail callouts to the envelope. Keep epidermis, dermis, follicle and the coil-to-pore path selectable within the skin block. Keep nail plate, bed and matrix reusable as their own lesson group. Test a local lift-away of the plate where it clarifies the bed and matrix. [Current section evidence](../../reviews/skin/teaching-block-r01/README.md) | A learner can identify each layer and appendage in section and relate the isolated or displaced part to its assembled location. Locator, illustrative materials and enlarged scales are clear. |

## Evidence and delivery

- **Admit each derivative** with the baseline and a matched candidate. Name
  the learner action or downstream use, source owner and visible improvement.
  Reuse an existing export when camera, layering or isolation closes the gap.
  For each refined system, demonstrate one use of a named part group outside
  its default assembly, such as a lesson insert, section or posed detail.
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
  critical junction. Compare candidate and reference at the same camera,
  lighting and scale. Include assembled and separated states for any exploded
  detail. At laptop scale, inspect labels, silhouettes, route crossings and
  grayscale readability. Assess simplification and material changes at the
  intended close-up scale. Each view should have one anatomical question that
  a reviewer can answer from the delivered plate.
- **Exercise the local gallery** through its normal entry points. Verify 11
  sections, assembly-to-detail navigation, keyboard access, route visibility,
  context reset, static fallback and failed model load/retry. Check finer
  selections and any material-preserving view in the actual consumer. If
  adding pose or phase controls, verify the exported state at each stop. Use
  explicit static pose views when the consumer has no playback control.
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
