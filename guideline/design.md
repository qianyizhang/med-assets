# Gallery design

Start with one visitor, one object and one question. “Which adrenal model can I reuse?”, “What changed in this revision?” and “Where are the glands?” deserve different first views of the same collection.

The [gallery product requirements](../docs/gallery/README.md) define the four surfaces and link their individual PRDs. This guide owns how people move between them and how each view serves its purpose.

## Current galleries and pilot

| Entry point | Primary job | Handoff |
| --- | --- | --- |
| **Model Survey** | Find a family or product by anatomy or purpose. Show a representative preview and its main limitation. | **Review this version** opens the candidate for the selected export. **See in a system** opens a teaching scene that uses it. [Survey owner](../sites/model-survey/README.md) |
| **Anatomy Verification** | Inspect an identified revision. Show matched evidence, the decision and the outstanding defect. | Download the identified export or return to the selected family. The external Site owns this interface. [Viewer integration](../gallery/README.md) |
| **Body Systems** | Orient in a system assembly, then isolate a structure or trace a route. | Open the exact model and review behind the detail. Give enlarged or separately authored details a locator and scale note. [Systems owner](../sites/body-systems-survey/README.md) · [Vocabulary](../GLOSSARY.md#gallery-presentation) |

**Adrenal pilot.** The survey's `adrenals` family includes a 115,440-byte BodyParts3D export. Its SHA-256 starts with `c7de1afa5394`, matching Verification's `/review/#candidate-adrenals__source-candidate-01`. The local prototype exposes **Review this version** for that measured match. The s1233 study uses a different source and deserves **Related teaching study**. Its rating belongs to its own export. [Survey definition](../sites/model-survey/tools/build_survey.py) · [BP3D export binding](../reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json) · [Verification entries](../tests/gallery/fixtures/entries.json) · [System bindings](../sites/body-systems-survey/refinements/surface-quality.json)

For the two survey views, carry the visitor’s selection both ways. From **Adrenal pair**, offer **Related teaching study** targeting Body Systems’ existing `#refinement-surface-adrenal` anchor. From that study, **Browse adrenal models** returns to the family, **Compare surfaces before scoring** opens the blind comparison, and **Build and checks** opens the s1233 revision’s own evidence. If the local system gallery is unavailable, offer its checked-in matched views. This makes the catalogue useful to someone choosing an export and the system view useful to someone learning placement. [System anchor builder](../sites/body-systems-survey/report.py) · [s1233 matched views](../reviews/endocrine-locator/adrenal-study-r05/README.md)

Try the [local cross-gallery prototype](../sites/gallery-links/README.md) before moving either site. Group by stable family ID and bind each review by export identity. Read labels, credits and decisions from their owners. Verification already accepts candidate and asset fragments. The local survey source accepts `#family-adrenals` and other family IDs while retaining its FDI31 bookmark. The hosted version has a separate publication cycle. Test direct reload, Back, unmatched variants and old bookmarks. [Survey selection](../sites/model-survey/app/src/content/report/ReportContent.jsx) · [Verification selection](../tests/gallery/fixtures/review.js)

## Shared design across four surfaces

Use **Asset Library** and **Use Cases** as the main navigation entries. Place **Compare revisions** beside the revision selector and **Open in 3D Stage** beside the view it opens. Give Compare and 3D Stage direct URLs and list both under **Tools** for visitors starting a new session.

Carry the selected name, source and revision across a handoff. Keep the originating selection available through the return link. Use a common part name and laterality label across images, legends and controls. Keep colors consistent within a teaching sequence and explain a palette change at the view where it happens.

| Surface | Start the visitor here | What the handoff carries |
| --- | --- | --- |
| Asset Library | A portrait that makes the selected export recognizable | The lineage, revision and portrait preset |
| Use Cases | The overview that answers the lesson question, followed by asset and part details | The selected lesson stop, asset revisions and its view |
| Compare | The close-up that reveals the difference, with a whole-object locator | Both input identities, comparison settings and the saved finding when available |
| 3D Stage | The exact composed view opened by the previous surface | The pinned preset revision and exported image |

A useful first test is to open the adrenal from each surface. The library should identify it, the lesson should establish placement and the comparison should reveal the fold. Each should offer the exact staged view behind its poster with a route back to the originating record.

The current Three.js URL selects a named scene. It restores the authored starting direction and selected parts. Orbit and visibility changes are transient. The reviewed adrenal plates currently come from Blender, and its studio light differs visibly from the browser. A versioned preset and image-export path would let a new gallery poster reproduce its browser view. Retain the renderer and revision with historical evidence. Smithsonian Voyager’s state editor provides a precedent for saving camera, light and material changes. [Current Three.js scene bindings](../sites/body-systems-survey/viewer_catalog.py) · [Viewer controls](../sites/body-systems-survey/viewer/viewer.mjs) · [Voyager state editor](https://smithsonian.github.io/dpo-voyager/story/usage/state-editor/)

## Scaffold for a new gallery

| Surface | Build | Check |
| --- | --- | --- |
| Browse | Use cards for visual recognition or rows for comparing status. Give each entry a poster, name and distinguishing fact. Keep orientation consistent and label independent scales. | Find an entry by partial name and by category. Back restores filter, scroll and keyboard focus. |
| Inspect | Start in an authored view that answers the question. Show the target, its limitation and the applicable controls. Offer isolate and reset where useful. | Identify the target at laptop size. A failed load keeps the poster, explanation and retry action available. |
| Compare | Show the whole object and one decisive detail. Hold camera, light, scale and pose fixed for surface A/B. Label deliberate offsets. | Switch versions without losing the landmark. Try grayscale or neutral material when appearance could explain the difference. |
| Reuse or verify | Carry the selected version into its export, review or lesson. Keep provenance and rights one step away. | Check identity at the destination. An unavailable review links to the owner with the status visible. |

Copy this brief into the owning project and build one representative entry end to end.

~~~text
Audience and question
Family ID / variant / export identity
Poster and identifying caption / initial view / primary action
Comparison settings / feature the visitor should see
Destination / return state / unavailable-state behavior
Owners of model, rights and review / acceptance evidence
~~~

For the endocrine entry, a learner locates the glands in the posterior assembly, isolates one, compares its close-up with the previous surface and returns to the same system entry. The paired posters also answer the placement question without orbit controls.

## Design precedents

- **Game DCC workbench.** Its fixed angles and Material, Clay and Wire views inspect one selected asset. Borrow the neutral diagnostic when color or sheen could conceal a form defect. [Workbench source](https://github.com/qianyizhang/game/blob/8960be85bc34f7741914e805dc612897b7857fd5/packages/dcc-workbench/src/Workbench.tsx)
- **Mill Shader Lab.** The DCC catalogue restores browse context. Lessons stage the same assets with a shared A/B camera and clock. Borrow this division of ownership for organ libraries and system assemblies. [DCC gallery](https://github.com/qianyizhang/3d-game-shaders-for-beginners/blob/f104423bbb2022bdd8321c5acfc39a561731736d/project-docs/dcc-gallery.md) · [Scene and part gallery](https://github.com/qianyizhang/3d-game-shaders-for-beginners/blob/f104423bbb2022bdd8321c5acfc39a561731736d/project-docs/scene-gallery.md)
- **Smithsonian Voyager.** Curated tours and surface annotations coexist with free inspection. A system route can use a few named stops with an open inspector. [Voyager guide](https://3d.si.edu/es/how-use-3d-viewer)
- **Accessible static views.** Google's model-viewer demonstrates posters during loading and model failure. W3C pairs a short image identification with a nearby account of the essential information. Describe the anatomical relationship in the caption. [Poster examples](https://modelviewer.dev/examples/loading/) · [W3C complex images](https://www.w3.org/WAI/tutorials/images/complex/)

Score the object with the [teaching-asset rubric](asset-quality.md). Judge the gallery by whether the visitor can complete the journey.
