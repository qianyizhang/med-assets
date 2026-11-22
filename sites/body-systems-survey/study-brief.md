# Body-systems study brief

Close the gaps in the baseline 11-system survey. Seven systems need a core
model or assembly. Four already support a scoped demo and have refinements
listed below. Baseline `2cb53c05577b4cbc2355c4bff293666127d21382`. The survey's
source disclosures identify the exact GLBs and prior evidence for each row.
Follow the [repository workflow](../../docs/WORKFLOW.md) and the owning export
and review records.

## Complete the missing setups first

| Work package | Build or refine | Done when |
| --- | --- | --- |
| **Integumentary** | Keep the existing body envelope as a locator. Use the [2D skin-detail plate](../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/skin-detail.svg) to scope an editable skin block with epidermis, dermis, subcutaneous context, a hair follicle and a coiled sweat gland with a surface opening. Include a separate nail-unit insert showing plate, bed and matrix. The [skin concept](../../.artifacts/body-systems-survey-2026-11-19/media/concept-skin.png) sets the visual direction. | Layers and appendages can be isolated. The cut face shows the follicle in the dermis, the sweat duct reaching the surface, and the nail structures in the inset. |
| **Cardiovascular** | Reuse the [Cardiac Atlas](../../heart/Cardiac_Atlas/docs/README.md) and screen the Workshop vessels. Assemble the four chambers and valves, pulmonary outflow and return, and systemic arterial and venous return. Use explicitly schematic lung and body vascular beds where fine branches add no teaching value. | A learner can trace a single directional loop through both sides of the heart and both beds. All required transitions have named, visually matched endpoints, with authored bridges identified. |
| **Digestive** | Reuse the [Workshop abdominal assets](../../body/anatomy-workshop-r1/README.md) and the BP3D bowel studies. Build a registered or explicitly authored path from mouth through pharynx, esophagus, stomach, small and large intestine to the terminal outlet. Include salivary, biliary and pancreatic entry points. Use the [biliary diagram](../../diagrams/biliary_pathway/exports/r01/README.md) as a reference for the local teaching setup. | The entire food route is traceable with entrances and exits visible in isolation. A separate accessory view shows where saliva, bile and pancreatic secretions enter. |
| **Nervous and special senses** | Stage the brain, [cord and representative roots](../../reviews/spinal_cord/2026-10-29-authored-roots-r04/README.md), and one peripheral pathway into a traceable route. Extend the [auricle](../../models/ears_z/exports/r04/README.md) with canal, tympanum, middle-ear ossicles, cochlea and vestibular structures. Add or qualify one receptor-to-pathway inset for each of vision, hearing, balance, smell and taste. | One brain–cord–peripheral route can be followed in context. Each sensory inset shows the receptor/organ and the start of its route. The ear distinguishes the auditory and vestibular structures. |
| **Endocrine** | Build a head-to-pelvis locator from the [hypothalamus–pituitary assembly](../../assemblies/hypothalamus-pituitary/teaching-stalk-r01/README.md) and qualified thyroid/parathyroid, adrenal, pancreas and gonad models. Add an islet inset and one hypothalamus → pituitary → target-gland example with a schematic signal overlay. | All major landmarks in the set are individually locatable. The teaching example separates gland geometry from the signal path and shows the chosen target and direction. |
| **Lymphatic and immune** | Reuse the [collecting-route scaffold](../../models/lymph-collecting-routes/source-context-r01/README.md) and node, spleen and thymus studies where useful. Build one regional route from tissue through a node and collecting vessel to a venous junction. Give spleen and thymus separate locator context. See the [junction concept](../../.artifacts/body-systems-survey-2026-11-19/media/concept-lymph.png) for visual direction. | One route has identifiable entry and exit points through the node and a documented duct-to-vein join. Spleen and thymus are locatable apart from the demonstrated route. |
| **Reproductive** | Build separate female and male adult assemblies. Reuse the [ovary/tubal study](../../models/ovaries/exports/hra-ovary-tubal-r01/README.md), female pelvic context, [testis/epididymis](../../models/testes/exports/z-native-epididymis-r01/README.md) and male outlet study. Female scope covers ovaries, fimbriae, tubes, uterus, cervix and vagina. Male scope covers testes, epididymides, ductus deferens, seminal vesicles, ejaculatory ducts, prostate and urethral outlet. Keep the breast study as a linked regional view. | The female assembly shows the fimbrial pickup relationship and the route from tube to uterus. The male assembly traces the path from epididymis to urethral outlet and shows seminal-vesicle contributions. Source limits and inferred anatomy are recorded for each assembly. |

## Refine the four working demos

| Work package | Done when |
| --- | --- |
| **Skeletal** | Extend the [knee study](../../reviews/joints/knee-inspection-r01/README.md) with one joint-motion example, two labelled poses and qualitative load directions. Check landmarks and articulation in both poses. Keep the whole skeleton as orientation and document source mesh categories separately from anatomical counts. |
| **Muscular** | Refine the [calf–Achilles–heel scene](../../assemblies/musculoskeletal-teaching/2026-10-23/README.md) with reference-checked regional insertions and a simple plantarflexion rig. Show the muscle–tendon–bone chain in two poses and check deformations. Record whole-body attachment validation and rig coverage as broader follow-up scope. |
| **Respiratory** | Extend [One Breath](../../lessons/one-breath/README.md) with one continuous route from nasal cavity through pharynx, larynx, trachea and a lobar branch to an illustrative terminal/alveolar inset. Show the branch joins in context and link the existing 2D exchange view. Check the route and breathing scene at two phases. |
| **Urinary** | Refine the Workshop's bilateral gross route with visible kidney-to-ureter, ureter-to-bladder and bladder-to-outlet transitions. Add a renal filtration inset and a clearly schematic flow overlay. Check each side independently and let users isolate each junction. |

## Shared acceptance

- Compare existing candidates before adding an asset. Use an editable source,
  portable GLB, replay instructions, exact input/output identities and attribution
  in the existing asset or assembly owner.
- Record units, axes, left/right orientation, and any registration transform
  or authored placement. Inspect expected joins, occlusion and collisions.
  Use a named, reference-backed schematic when anatomy must be authored.
- Make each essential part inspectable on its own and supply a combined view
  of the teaching route. Render from the clean GLB at matched scale within
  each isometric and straight orthographic pair. Use the survey's matte
  palette and a complementary view for hidden junctions. ImageGen provides
  visual direction. It does not establish anatomy or supply 3D geometry.
- Record technical, visual, anatomy and runtime checks independently. Replay
  affected recipes and run `python3.12 tools/verify.py offline`. Run
  `payload-integrity` for broad hydrated changes per the workflow. Carry
  forward exact blockers and unverified gates.

## Completion ledger · 19 November 2026

All eleven rows have local teaching assets and exact screenshot evidence. The repository gates and local revision are in the [verification summary](README.md). Specialist approval and gallery consolidation remain separate decisions.

| System | Editable source, portable GLB and replay | Matched pairs and independent checks |
|---|---|---|
| Skeletal | [Assembly](../../assemblies/skeletal-teaching/knee-motion-r01/README.md) | [Evidence](../../reviews/joints/knee-motion-r01/README.md) |
| Muscular | [Assembly](../../assemblies/musculoskeletal-teaching/plantarflexion-r01/README.md) | [Evidence](../../reviews/muscle/plantarflexion-r01/README.md) |
| Respiratory | [Assembly](../../lessons/one-breath/airway-r01/README.md) | [Evidence](../../reviews/one-breath/airway-r01/README.md) |
| Urinary | [Assembly](../../assemblies/urinary-junctions/r01/README.md) | [Evidence](../../reviews/urinary-junctions/r01/README.md) |
| Cardiovascular | [Assembly](../../assemblies/cardiovascular-loop/README.md) | [Evidence](../../reviews/cardiovascular-loop/README.md) |
| Digestive | [Assembly](../../assemblies/digestive-route/r01/README.md) | [Evidence](../../reviews/digestive-route/r01/README.md) |
| Nervous | [Assembly](../../assemblies/nervous-senses/README.md) | [Evidence](../../reviews/nervous-senses/README.md) |
| Endocrine | [Assembly](../../assemblies/endocrine-locator/r01/README.md) | [Evidence](../../reviews/endocrine-locator/r01/README.md) |
| Lymphatic and immune | [Assembly](../../assemblies/lymphatic-return/r01/README.md) | [Evidence](../../reviews/lymphatic-return/r01/README.md) |
| Reproductive | [Assembly](../../assemblies/reproductive-tracts/r01/README.md) | [Evidence](../../reviews/reproductive-tracts/r01/README.md) |
| Integumentary | [Assembly](../../models/skin/teaching-block-r01/README.md) | [Evidence](../../reviews/skin/teaching-block-r01/README.md) |

## ImageGen concept prompts

Built-in ImageGen. The concepts explore teaching geometry and matte-clay visual style. The report links each concept to a gap and labels it illustrative.

### Layered skin

> Use case: scientific-educational. Original design concept for a future editable 3D teaching asset, not a diagnostic illustration. Single landscape image split neatly into two equal panels on a seamless very pale warm gray background. Show the exact same stylized skin barrier block at matching apparent scale in each panel: left is an isometric orthographic museum-model view, right is a true flat front orthographic view of its cut face. Coherent matte clay anatomy maquette, gentle studio shading, restrained parchment, terracotta, and soft pale gold. Clearly distinguish thin upper epidermis, thicker dermis, and pale lobulated subcutaneous tissue, with one hair follicle and one coiled sweat gland reaching the surface. Use simple broad shapes, generous clear margins, no realistic injury, no lettering, no arrows, no title, no watermark, no split line. Visual target for hand-built geometry.

### Lymphatic return junction

Initial generation

> Use case: scientific-educational. Original appearance proposal for an editable gross-anatomy teaching asset that will show one lymphatic collecting route ending at a venous junction. Paired-view landscape concept board on a seamless pale warm-gray background. In left half render a well-framed isolated orthographic three-quarter clay model, in right half the exact same small model as a front orthographic plate. Show a narrow muted sage collecting tube rising from bottom with two small sage node-shaped beads on the lower path and ending where two thicker slate-blue venous branches meet in a Y. Use broad readable curves, softly matte clay, restrained depth, simple seamless joints, tasteful high legibility. Generous margin, no people or body silhouettes, no words, no labels, and no arrows. Treat this as a visual prototype for selecting camera and palette, a simplified partial segment.

Edit of the initial image

> Edit this scientific-educational clay concept for the topology of the vessels, preserving the two matched panels, camera style, muted sage and slate-blue materials, and pale warm gray background. In each panel, the blue vein must have THREE unmistakable arms, all BLUE: an upper vertical branch, a lateral branch entering from the right, and a downward outgoing main vein that continues intact below their junction and has a visible cut end. The very thin green lymphatic tube with two small nodal bulges approaches from the lower LEFT and joins the SIDE of the blue vein at the angle near the upper/lateral confluence. The green never replaces the blue outgoing main vein. Exactly three blue terminal openings, one green incoming tube. Display the same topology in both halves. Keep it an abstract visual blockout, no labels, no text, no arrows.
