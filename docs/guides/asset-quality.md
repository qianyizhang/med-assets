# Review a teaching asset

Start with one sentence a learner could test. For example, “From behind, identify each adrenal and its relation to the kidney on the same side.” Name the exact export, target parts, protected landmarks and closest intended view. Specify whether the model shows traced labels, an interpreted teaching exterior or a schematic. A single object can serve different tasks with different scores.

For work starting with CT labels or an extracted mesh, follow the [scan-derived surface refinement guide](scan-surface-refinement.md) from source inspection through the lighter-mesh trial.

## Reading a library rating

Show **fidelity to evidence**, **form and surface**, and **mesh economy** for the selected revision. Bind the profile to the exact export, reference, reviewed view, reviewer, date and rubric revision. Use **Unrated** for a missing assessment or axis. A numeric zero is an assessed result with the meaning defined below. A new revision starts unrated until evidence covers it.

A named teaching assessment adds **teaching readability**. Show a total only when all four axes are rated for that task. For example, **16/16 · regional localization · s1233 r05** links to the [adrenal review](../../reviews/endocrine-locator/adrenal-study-r05/README.md). The Asset Library links to this rubric from both scored and unrated profiles.

An agent assessment can appear as soon as its evidence is available. Identify it as agent-reviewed and show the evaluator, review date and supporting views alongside the score. Record a human reviewer’s judgment separately, including disagreements about a visible feature. Keep both judgments attributable to their authors.

## Score four axes

Use 0–4 on each axis. **0** means a required feature is absent or contradicted. **1** means a defect dominates the teaching view. **2** means the task is possible with a specific distracting defect or incomplete check. Apply the anchors below for **3** and **4**. Mark an axis **unrated** if the necessary evidence is unavailable and omit the total. Give one observation or measurement per score.

| Axis | 3 · Ready for the stated task | 4 · Additional evidence |
| --- | --- | --- |
| Fidelity to evidence | Named parts, sides, placement and protected relationships survive clean import. Source geometry, editorial changes and magnification are identified. | Measure the change against the declared reference, including the most vulnerable small feature. For a schematic, independently test the claimed contacts, spatial order or open route in the export. |
| Form and surface | The target has a recognizable silhouette in two views **and** an intelligible exterior at the intended close-up. Inspect a neutral render with a broad highlight. Account for each conspicuous pit, ridge or opening that someone could learn as anatomy. | The surface also reads under a different light direction or reverse view. A close comparison to a suitable anatomical reference supports the major folds, openings and finish. |
| Teaching readability | A reviewer can perform the named action in the view pair and isolate the targets. Context supplies orientation. Mark editorial joins, lifted parts and independent scales where they appear. | The default view answers the question, a second angle confirms depth or continuity, and the task still works in grayscale. Record what was found or traced. |
| Mesh economy | Per-part triangles, material primitives and connected pieces have a visible, selectable or motion-related purpose. Inspect thin rims and curved silhouettes. Compare bytes at the same export scope. | A lighter trial of the same shape or a measurement of its tessellation error shows the benefit and cost at the intended zoom. Record the worst affected feature as well as the total saving. |

Aim for **at least 3 on every axis**. Use a total out of 16 only to compare revisions on the same task. A wrong side, lost landmark, falsely connected route, corrupt export or untraceable source blocks acceptance. Report specialist review, runtime and distribution separately.

## From a score to an improvement

Name the observation that affected the learner's task. If a relationship is hard to see, inspect it in another view before deciding whether to change the geometry. For a suspected mesh cost, compare a lighter export at the intended zoom and inspect the most vulnerable landmark. For a missing reference or view, record which check would resolve the uncertainty.

State what the proposed change should improve, what it must preserve and how the reviewer will tell. Check the candidate against the same task and baseline. Record a keep, revise or reject decision with the matched evidence. A keep decision can close the review when the current asset already serves its task.

### Resolve a below-target score

Work first on a plausible false inference, then on a learner action that fails at teaching size. Review form and mesh cost in terms of the same action. Give each asset one primary work item and record secondary defects there.

Use the previously delivered experience as the control. Identify the exact file, named task, first view and any selection a learner already had. A control and candidate with a changed camera, hidden structure, illustrative color or additional source must disclose that difference. The reviewer should be able to repeat the selection or inspect the matched views and point to the landmark. A newly surfaced existing witness can improve teaching readability. It supplies no evidence that the source geometry changed.

Record what happened to every previously low axis. Raise a score when the same task meets its anchor in the delivered experience. A source limitation stays attached to the original file. Evaluate a lighter candidate under its own identity, including its closest useful view, worst affected feature and any data lost from the export. The original retains its measured cost.

## Review a teaching set

Choose a learner task and protected landmark for each asset. In the overview, use the same projection, orientation conventions, lighting and framing across comparable assets. Preserve physical scale when comparing size. Label independently enlarged details, intentional cuts and schematic joins in the views where they appear. Keep target, context and cut surfaces distinguishable under grayscale. Pick a second angle that answers a real depth, attachment or continuity question.

Inspect the intended lesson alongside the isolated model. A recognizable organ can still disappear behind context, lose its connecting landmark at lesson scale or use a color that changes meaning between stops. Record where this happens and test the smallest correction in that view. When a collection requires a different camera or palette, state what the learner gains and preserve the other orientation cues.

Calibrate reviewers on a previously assessed export and a borderline example. Compare observations axis by axis at the declared viewing size. Record the lead reviewer's agreement or correction alongside the original judgment. Where two defensible treatments lead to different learner outcomes, prepare matched variants and state the choice for the maintainer.

For lessons built from one editable model, mark the shared structures and verify their registration and units. Rebuild after a disposable edit to a shared landmark and check that each export reflects that edit while retaining its own selection or motion. Review each delivered file at its lesson camera and phase. The [register](../gallery/maintained-models.md) groups ownership, while the [scorecard](../../records/campaigns/teaching-asset-review/current-coverage.md) keeps the individual assessments.

## When an organ looks like clay

1. **Isolate the part.** Inspect the actual GLB in its gallery pose and in a close-up. Rotate it and compare a neutral material with the intended palette under the same light. Check the full-resolution poster at 1:1. A jagged edge that disappears on a higher-resolution render points to raster sampling. A depression that moves with the model calls for mesh inspection.
2. **Name the feature.** A boundary loop is an open edge. A closed surface can still have a tunnel through it. A blind depression, a gap between two organs and a dark highlight need different treatment. Count components and open edges. For each closed, orientable shell, genus helps detect tunnels. Inspect their location before editing.
3. **Decide what the source supports.** Record a documented opening or landmark, a feature visible in the acquisition with uncertain meaning, or an editorial reconstruction. Protect real concavities and thin limbs. Preserving every segmentation tunnel can mislead learners. Filling one for an illustrative exterior requires naming the part, keeping the traced reference accessible, and measuring what changed. An unexplained conspicuous tunnel or lumpy target at teaching zoom caps **form and surface at 2**.
4. **Tune shape before finish.** Reduce small undulations that compete with the organ's major planes. A broad highlight should travel across the body and turn at meaningful folds. Use restrained highlight strength and enough value separation to read the edge against context. Add local relief or gloss only with a reason visible in the reference. A static render can suggest soft tissue. A claim about compliance or motion needs separate mechanical or deformation evidence.

For a traced or smoothed surface, record voxel spacing, component and topology changes, typical and worst local deviations in physical units, and the reference those distances use. Protect the smallest target separately. A volume match can coexist with a misplaced limb. A closed manifold can retain a false tunnel. Show the inspected region alongside the numbers. [Matched-view evidence contract](../WORKFLOW.md#evidence-for-comparison)

## When an asset looks like a toy

Check the outline before the palette. Repeated spheres, constant-width tubes and identical rounded ends can hide the taper, branching order or attachment that distinguishes one part from another. Name the distinguishing feature and find it in two views. Keep a deliberate simplification when it helps the learner trace the structure. In the teaching palette, give the target the clearest value contrast, let the context recede, and distinguish an intentional cut face from an intact exterior. Check that those distinctions survive grayscale.

## Soft mesh budgets

Start with one selectable part per teaching role. A homogeneous surface often needs one material primitive. A wall and cut face may justify two. Preserve multiple disconnected pieces when the source and lesson call for them.

A few hundred triangles can describe a short tube or simple sheet. A few thousand can describe a curved organ or cut rim. Above roughly 10,000 triangles on one static context organ, try a lighter copy. Long edges are appropriate on a plane. Sample a turning silhouette densely enough that the chord departs from the intended curve by about one display pixel or less at the declared zoom. Complex branches, preserved acquisition detail and deformation can justify other budgets.

## Review note to copy

> **Task and reference** · Who uses which selection, at what view and scale? Which source supports the relationship?
>
> **Protected features and interpretation** · Name the landmarks, purposeful openings, uncertain features and editorial changes.
>
> **Evidence** · Link the exact export, matched whole views, target close-up and measurements.
>
> **Decision** · Fidelity __ / Form __ / Readability __ / Economy __. Give the reason for each and the next unresolved limit.

## Resolve the teaching target

Keep the four scores on the exact file and learner task. Inspect the visible finish at the closest intended teaching view. If a contour is visibly distracting, score the observed finish and record any uncertainty about its cause. A registered section or source-author explanation can support a claim about specimen morphology. Preserve the source contour when its origin is uncertain. Label an interpreted derivative, cite the reference that supports the change, and keep the original available.

For a task that depends on several structures, review the delivered composition as a separate learner action. Record the view or selection used, what the reviewer could locate or trace, and any step that failed. A collection lists its required actions and their outcomes. A blocked relationship stays visible even when every component has high scores.

A score below 3 can remain when a tested alternative loses a protected feature, the source cannot support the proposed correction, or a delivery constraint prevents a faithful replacement. Record the exact axis, attempted fix, evidence, permitted use and condition for reopening. The lead reviewer accepts each exception individually. Keep its actual score visible. An exception to surface or delivery quality only permits the learner action that the evidence demonstrates.
