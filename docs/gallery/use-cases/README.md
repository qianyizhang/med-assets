# Gallery Use Cases

A learner can answer an anatomy question by following a sequence of authored views. Each collection owns the question, the order of views and the action a learner should be able to complete.

This table links the current collection briefs. Body Systems is established in the Gallery. Ultrasound Anatomy is active in the local candidate, where the first Abdomen stop already links the tour and its asset review. The candidate has a Lessons index and linked Teaching and Development views within each body system. The same paired-page organization is the target for Ultrasound Anatomy.

| Collection | What the learner does |
| --- | --- |
| [Body Systems](body-systems.md) | Orient in one of eleven system assemblies, then inspect a detail or follow a relationship. |
| [Head & Neck](head-and-neck.md) | Locate the major salivary glands, trace the supported parotid duct course or distinguish the oral spaces. |
| [Regional locators](regional-locators.md) | Place a local structure in its region and interpret the corresponding close-up. |
| [Pathway diagrams](pathway-diagrams.md) | Trace a named route through its structures using a bilingual figure. |
| [Dental arch identification](dental-arch-identification.md) | Identify a crown, its FDI number, its arch and the patient's side. |
| [Ultrasound Anatomy](ultrasound-anatomy.md) · Local candidate | Relate a probe position, anatomical section and ultrasound-style view. |

The [route contract](../routes-and-api.md#page-links) lists the individual lesson addresses. The [local teaching checks](../../../reviews/teaching-assessments/use-case-checks.json) record the actions reviewed outside Body Systems.

## Collection pages

Give substantial collections linked **Teaching** and **Development** pages, starting with Body Systems and Ultrasound Anatomy. Carry the selected system, lesson or acquisition and its active stop across the round trip. Reopen that selection on return.

| Page | What it offers |
| --- | --- |
| Teaching | An intentional learner experience with a question, authored sequence and an observable action. Choose the assets, parts, views and captions that support that action. |
| Development | Active questions, the exact asset revisions and parts involved, current status, caveats and links to decisive evidence. Start with one real question or open gap tied to the selected lesson, then add entries when they help someone make a decision. Prune replaced entries and preserve required evidence under the [retention policy](../../WORKFLOW.md#retention). |

Use **Lessons** as a shared index for smaller lessons. A short lesson can present Teaching and Development as sections on one page. [Experiments & Archive](archive.md) indexes retained trials and historical presentations with their original purpose, status and limits.

For example, Teaching can open the Abdomen gallbladder stop at the selected grayscale marker and let the learner reveal the matching section. Development can open on that stop with the pinned s1233 liver and gallbladder masks, axial slice 195, the illustrative near-field caveat and the open question of probe placement against acquired ultrasound. Its evidence links lead to the exact inputs and views in the [lesson package](../../../lessons/ultrasound-anatomy/README.md#pose-and-source).

## Shared lesson requirements

Give a substantial teaching experience its own page or collection. Fold smaller lessons into a relevant stop when they answer the same question. For duplicate presentations and published links, follow the [retention policy](../../WORKFLOW.md#retention).

Move from the overall assembly to an asset or part when those scales answer the lesson question. At each stop, identify the target, its neighbors and deliberate changes in color, visibility or scale. Use continuous zoom where the detail has a known position and scale in the overview. For separately sourced details, show a regional locator and then a labeled view with its own frame and scale. Mark unknown scale explicitly.

Use the shared scene and a scene preset for an interactive 3D stop. Let the lesson control the sequence or interaction and pass the corresponding state into the scene. Static diagrams, sections and video can stand alone. Keep a poster and caption for an unavailable interactive scene. Pin the exact asset revision. When the [Library](../asset-library.md) recommendation changes, offer a [comparison](../compare.md) in the lesson's camera, colors and part selection. Adoption remains the lesson author's decision.

### Practising an anatomical relationship

Open with a question and an unlabelled view. Let the learner point, switch layers and reveal a labelled answer. Keep the point, frame, camera and scale across matched layers, including the learner's rotation and zoom in 3D. Supply a matched still for each layer and keep the point and answer state within the visit. See the [right-arm and pelvic examples](body-systems.md#linked-lessons).

## Develop a use case

1. Put the audience, question, proposed outcome and open decisions in the collection brief. Agree on what a learner should be able to do.
2. Prototype the decisions that would change the journey. Update the brief with the chosen progression and the evidence a learner needs at each stop.
3. Build one representative stop with the intended assets in the ordinary Gallery. Exercise the learner action and the fallback. Record specific page or asset gaps against the exact views that exposed them.
4. Fix the gaps with their owners, then repeat the same learner action. Keep the teaching scope current and replace resolved Development entries with links to the resulting finding when it still informs the collection.

See the [Gallery authoring entry points](../README.md#author-a-gallery-entry) and [repository verification gates](../../WORKFLOW.md#verification).
