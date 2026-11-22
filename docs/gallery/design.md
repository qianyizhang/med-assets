# Gallery design

Start with one visitor, one object and one question. “Which adrenal model can I reuse?”, “What changed in this revision?” and “Where are the glands?” deserve different first views of the same collection.

The [gallery product requirements](README.md) define the four surfaces and link their individual PRDs. This guide owns how people move between them and how each view serves its purpose.

<a name="current-galleries-and-pilot"></a>

## Current galleries

| Entry point | Primary job | Handoff |
| --- | --- | --- |
| **Anatomy Gallery** | Find a lineage in Asset Library and a teaching experience in Use Cases. Show a representative view and its main limitation. | Carry the exact revision to a saved review or teaching scene. [Site owner](../../sites/anatomy-gallery/README.md) |
| **Anatomy Verification** | Inspect an identified revision. Show matched evidence, the decision and the outstanding defect. | Download the identified export or return to the selected family. The external Site owns this interface. [Viewer integration](../../tests/viewer/README.md) |
| **Body Systems** | Orient in a system assembly, then isolate a structure or trace a route. | Open the exact model and review behind the detail. Give enlarged or separately authored details a locator and scale note. [Systems owner](../../lessons/body-systems/README.md) · [Vocabulary](../../GLOSSARY.md#gallery-presentation) |

The ordinary local Site connects the s1233 Library entry, lesson, comparison and Stage preset. Keep the BodyParts3D pair and s1233 distinct and link them as related studies. Each review or rating belongs to its own export. Preserve direct reload, Back and a return link to the selected revision or imported family. An unavailable model should offer its retained poster and a return route. [Current routes and API](routes-and-api.md)

The exact BodyParts3D review opens in Compare and links back to the same Library family. The [dated census](existing-visualizations.md) records the original survey and legacy inspection routes.

## Shared design across four surfaces

Use **Asset Library** and **Use Cases** as the main navigation entries. Place **Compare revisions** beside the revision selector and **Open in 3D Stage** beside the view it opens. Give Compare and 3D Stage direct URLs and list both under **Tools** for visitors starting a new session.

Keep the gallery controls neutral, with graphite text, cool-gray surfaces and indigo for selection. Reserve anatomical display colors for structures and show their legend beside the views. A direct Body Systems shortcut opens its collection within Use Cases.

Carry the selected name, source and revision across a handoff. Keep the originating selection available through the return link. Use a common part name and laterality label across images, legends and controls. Keep colors consistent within a teaching sequence and explain a palette change at the view where it happens.

| Surface | Start the visitor here | What the handoff carries |
| --- | --- | --- |
| Asset Library | A portrait that makes the selected export recognizable | The lineage, revision and portrait preset |
| Use Cases | The overview that answers the lesson question, followed by asset and part details | The selected lesson stop, asset revisions and its view |
| Compare | The close-up that reveals the difference, with a whole-object locator | Both input identities, comparison settings and the saved finding when available |
| 3D Stage | The exact composed view opened by the previous surface | The pinned preset revision and exported image |

A useful first test is to open the adrenal from each surface. The library should identify it, the lesson should establish placement and the comparison should reveal the fold. A Stage-exported poster opens its exact preset and offers a return to the originating record or lesson stop. A historical plate, photograph or section opens its original evidence. Label a companion browser scene as a related 3D view.

The older Body Systems Three.js URL selects a named scene. It restores the authored starting direction and selected parts. Orbit and visibility changes are transient. The reviewed adrenal plates currently come from Blender, and its studio light differs visibly from the browser. The unified Site’s [preset and poster contract](routes-and-api.md#sharing-and-authorship) lets a visitor reopen the browser view behind a new export. Retain the renderer and revision with historical evidence. Smithsonian Voyager’s state editor provides a precedent for saving camera, light and material changes. [Current Three.js scene bindings](../../sites/body-systems-survey/viewer_catalog.py) · [Viewer controls](../../sites/body-systems-survey/viewer/viewer.mjs) · [Voyager state editor](https://smithsonian.github.io/dpo-voyager/story/usage/state-editor/)

## Display images

Give a composite overview the full content width when its labels or teaching landmark are hard to see at laptop size. Follow it with the detail that answers the same question. Keep matched views side by side when readers need to compare the same landmark across revisions.

Serve new and migrated gallery raster images as WebP to reduce bandwidth. Generate display variants from the owning package’s canonical images under the [repository retention policy](../WORKFLOW.md#retention). Size them for their display slot. Check ordinary lossy portraits, thumbnails and lesson posters at display size for readable labels, silhouettes and teaching detail. When a comparison depends on exact pixels, use lossless WebP at inspection resolution and verify the decoded pixels against the reference. For an existing hash-addressed image, pin the encoder and settings and check the encoded size and SHA-256. Preserve the original-image fallback. [Survey preview encoder](../../sites/anatomy-gallery/tools/add_previews.py)

## Authoring a Gallery entry

Use the [authoring path and working example](README.md#author-a-gallery-entry). Check the view at laptop size and complete the onward and return actions with keyboard input. Compare matched landmarks with a whole-object locator. Keep the available evidence and exact asset link reachable when a view cannot load.

## Design precedents

- **Game DCC workbench.** Its fixed angles and Material, Clay and Wire views inspect one selected asset. Borrow the neutral diagnostic when color or sheen could conceal a form defect. [Workbench source](https://github.com/qianyizhang/game/blob/8960be85bc34f7741914e805dc612897b7857fd5/packages/dcc-workbench/src/Workbench.tsx)
- **Mill Shader Lab.** The DCC catalogue restores browse context. Lessons stage the same assets with a shared A/B camera and clock. Borrow this division of ownership for organ libraries and system assemblies. [DCC gallery](https://github.com/qianyizhang/3d-game-shaders-for-beginners/blob/f104423bbb2022bdd8321c5acfc39a561731736d/project-docs/dcc-gallery.md) · [Scene and part gallery](https://github.com/qianyizhang/3d-game-shaders-for-beginners/blob/f104423bbb2022bdd8321c5acfc39a561731736d/project-docs/scene-gallery.md)
- **Smithsonian Voyager.** Curated tours and surface annotations coexist with free inspection. A system route can use a few named stops with an open inspector. [Voyager guide](https://3d.si.edu/es/how-use-3d-viewer)
- **Accessible static views.** Google's model-viewer demonstrates posters during loading and model failure. W3C pairs a short image identification with a nearby account of the essential information. Describe the anatomical relationship in the caption. [Poster examples](https://modelviewer.dev/examples/loading/) · [W3C complex images](https://www.w3.org/WAI/tutorials/images/complex/)

Score the object with the [teaching-asset rubric](../guides/asset-quality.md). Judge the gallery by whether the visitor can complete the journey.
