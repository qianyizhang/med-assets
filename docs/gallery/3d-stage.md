# 3D Stage PRD

**Outcome.** An author can load identified models in Three.js, compose a view, save it as a persistent link and export the poster another surface will display.

## Preset and export

Stage owns the shared Three.js scene presentation used by every interactive 3D showcase on the Site. Asset Library embeds a revision portrait scene, Use Cases embeds a lesson scene, and Compare can embed two scenes with matched controls. Opening an embed in Stage restores the same preset. A public preset resolves each exact export through [Site R2](../../transport/README.md#public-r2-downloads). A preset for a moving subject also pins its animation, phase or frame where that affects what is shown.

Allow authors to open a local GLB, frame it and try appearance changes immediately. Saving a persistent preset requires a retrievable, versioned copy of every referenced model. If a model exists only on the author’s device, keep the composition open and identify which model needs a durable reference.

A saved preset pins the asset revisions, pose and placement, part visibility, material overrides, camera target and projection, framing, lighting and output settings. The link opens that saved revision. Editing and saving creates a new revision; earlier links keep their meaning. An exported image identifies its preset and renderer. Keep the actual image as evidence when it supports a review.

The library chooses a portrait, a lesson chooses its sequence and Compare chooses the matched pair. Stage reproduces their choices. Historical Blender plates, clinical source sections and gross specimen images retain their provenance as external evidence.

The first export delivers a persistent preset link and a WebP poster. Apply the shared [display image policy](design.md#display-images) when adopting a poster in the gallery. The original GLB remains available from the asset page.

## Acceptance example

From a right-adrenal close-up, save the staged view and export its poster. Opening the link in a fresh session recovers the same gland, angle, finish and framing. Changing the light and saving again gives the new poster a distinct preset revision. If pinned model bytes are unavailable, expose the missing revision and offer the retained poster where available.

The current Stage page links to the selected asset revision. Returning directly to the originating lesson stop or review is part of the [ordinary Site handoff](../../records/work-items/items/AG-GAL-002-absorb-adrenal-pilot.md). The local Site restores the versioned adrenal scene from a shared link and embeds that link in its exported WebP. Visitors can also inspect a local GLB. Future scene types extend the [route and preset contract](routes-and-api.md). The older Body Systems viewer still loads its named scenes. [Current scene bindings](../../sites/body-systems-survey/viewer_catalog.py) · [Gallery product requirements](README.md)
