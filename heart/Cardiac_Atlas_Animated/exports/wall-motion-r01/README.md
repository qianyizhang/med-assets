# Ventricular wall motion

Scrub the 0.8-second authored cycle and compare the left ventricular wall against the fixed aorta. The focused edition retains both exact mesh selections, materials, source frame and ventricular morph track from the [complete clinical atlas](../../Heart_Clinical_Animated.glb). Use that atlas for orientation and the other synchronized structures.

The two-part export has 30,646 triangles and is 1,158,724 bytes. The [matched phase comparison](../../../../reviews/teaching-assessments/target-risk/views/heart.webp) shows the contour movement at the largest 24 fps sample. Native review measured 5.047 mm peak ventricular motion and zero aortic motion in the tested frames. The motion illustrates an authored deformation of the wall. Flow, valve timing and measured physiology lie outside the exercise.

[Historical review](../../../../reviews/teaching-assessments/target-risk/README.md) · [Source motion, coordinates and atlas variants](../../README.md)

## Rebuild

From the repository root, use the hydrated source and Python 3.12. The recipe checks the new output against the reviewed SHA-256 and byte count before writing it to a fresh directory.

```sh
python3.12 tools/rebuild_asset.py heart/Cardiac_Atlas_Animated/recipes/wall-motion-r01.json .artifacts/rebuild-cardiac_atlas_animated-wall-motion-r01
```
