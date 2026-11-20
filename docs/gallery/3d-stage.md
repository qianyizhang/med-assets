# 3D Stage PRD

**Outcome.** An author can load identified models in Three.js, compose a view, save it as a persistent link and export the poster another surface will display.

## Preset and export

Allow authors to open a local GLB, frame it and try appearance changes immediately. Saving a persistent preset requires a retrievable, versioned copy of every referenced model. If a model exists only on the author’s device, keep the composition open and identify which model needs a durable reference.

A saved preset pins the asset revisions, pose and placement, part visibility, material overrides, camera target and projection, framing, lighting and output settings. The link opens that saved revision. Editing and saving creates a new revision; earlier links keep their meaning. An exported image identifies its preset and renderer. Keep the actual image as evidence when it supports a review.

The library chooses a portrait, a lesson chooses its sequence and Compare chooses the matched pair. Stage reproduces their choices. Historical Blender plates, clinical source sections and gross specimen images retain their provenance as external evidence.

The first export delivers a persistent preset link and a WebP poster. Size gallery previews for their display slot. Use lossy WebP for ordinary portraits and lesson posters after checking the silhouette, labels and teaching detail at display size. For a comparison that depends on subtle surface changes, serve lossless WebP at inspection resolution and verify its decoded pixels against the reference render. The original GLB remains available from the asset page. [Existing survey preview encoder](../../sites/model-survey/tools/add_previews.py) · [WebP formats](https://developers.google.com/speed/webp)

## Acceptance example

From a right-adrenal close-up, save the staged view and export its poster. Opening the link in a fresh session recovers the same gland, angle, finish and framing. Changing the light and saving again gives the new poster a distinct preset revision. If pinned model bytes are unavailable, expose the missing revision and offer the retained poster where available.

The current viewer loads named scenes with authored starting directions. Saving arbitrary composed state and exporting its bound poster are target capabilities. [Current scene bindings](../../sites/body-systems-survey/viewer_catalog.py) · [Gallery product requirements](README.md)
