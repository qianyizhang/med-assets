# BP3D skin envelope navigation trial

This trial tests whether a smaller whole-body locator preserves the shoulder, hand and foot outlines and their depth cues. It starts from the [exact FJ2810 r01 surface](../../exports/bp3d-envelope-r01/README.md), with [BodyParts3D attribution](../../exports/bp3d-envelope-r01/ATTRIBUTION.md). The [Gallery assessment](../../../../records/work-items/items/AG-GAL-025-assess-next-teaching-cohort.md#skin-envelope-refinement-trial) supplies the teaching task and the two display views. Its subpixel counts motivate the trial.

## Acceptance set before simplification

- Replay the pinned anterior and isometric Body Systems cameras at 680 × 560 with a 2.376396 m orthographic width. Lock candidate framing to the control, including the control's world placement and scale. Use matched 4× neutral captures for the detail inspection and outline measurement.
- Preserve positions, normals and all incident faces through the bilateral shoulder caps, the entire hands including wrists and interdigital spaces, and both feet including ankles, toes and heels. Preserve all source index seams and envelope extrema. The spatial bands are in the source glTF frame in metres. The comparison independently checks those bands and verifies both GLBs after clean import.
- Require an exact world matrix and bounds, matching indexed topology counts for components, seam edges and Euler characteristic, and no new non-manifold edges, inconsistent winding or degeneracy. The maximum sampled distance in either direction, using clean-import vertices and face centroids, must be no greater than 2 mm.
- Require a worst foreground mask shift of at most 1 display pixel across the two views. Use the symmetric maximum nearest-foreground distance at 50% alpha on the fourfold captures, divided by four. This is a sampled image measurement. Inspect the native overviews and the enlarged paired wrist, hand, ankle and foot crops. Require every visible finger gap and toe/heel contour to survive and the head, neck, shoulders, torso and knees to read at the pinned scale.
- Aim for at least 25% fewer triangles and 30% fewer bytes for the same single selectable envelope.

## Replay

Run from the repository root with Blender 5.2.3 LTS Release Candidate (`fab76e95306d`) and the hydrated control and teaching plates. The image check uses Python 3.12, NumPy 2.5.4, SciPy 1.18.1 and Pillow 13.0.0. Use fresh output directories.

```sh
recipe=models/skin/recipes/navigation-trial
trial=.artifacts/skin-navigation-replay
source_glb=models/skin/exports/bp3d-envelope-r01/skin_source_frame.glb
mkdir "$trial"
blender --background --factory-startup --threads 4 --python-exit-code 1 \
  --python "$recipe/build.py" -- --input "$source_glb" --output "$trial/build"
blender --background --factory-startup --threads 4 --python-exit-code 1 \
  --python "$recipe/compare.py" -- --input "$source_glb" \
  --candidate "$trial/build/skin_navigation_trial.glb" --output "$trial/capture"
python3.12 "$recipe/pixels.py" "$trial/capture" "$trial/evidence"
```

The builder contracts edges of up to 6 mm in six shortest-first passes. Each merge keeps one source endpoint, preserves the edge link, and limits the turn of each surviving incident face to 25°. The builder compacts the surviving source vertices, normals and faces in stable order. The GLB retains the source scene, node, material and attribution identity metadata. The comparison writes exact artifact and capture bindings and the image check produces the paired evidence. The [owner review](../../../../reviews/skin/2026-11-21-navigation-trial/README.md) records the exact outcome and decision.
