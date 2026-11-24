# Gallbladder sweep study

Orbit the probe on the body to inspect its contact and direction. In the separate scan-plane scene, orbit the wireframe imaging sector through the liver and gallbladder. Both cameras hold their angles as the timeline moves the transducer. Drag the scrubber or select a reference tick to compare the simulated image and the acquired ultrasound. **Anatomy overlay** shows the labeled section. **Keyframe assets** opens the geometry and images used at the selected pose.

The [collection brief](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns the scope. The [reference study](research/README.md) records the two independent cases, acquisition sources, reuse terms and current appearance gaps.

## Replay

Use Python 3.12 with NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0. Retrieve the public s1233 case and the two original images linked in the reference study. Run from the repository root with a fresh output directory.

```sh
python experiments/ultrasound-sweep/build_study.py "$S1233_CASE" "$LONG_AXIS_PNG" "$SHORT_AXIS_GIF" "$STUDY_OUTPUT"
python experiments/ultrasound-sweep/prepare_scenes.py "$STUDY_OUTPUT" --vendor-dir lessons/one-breath/.local/vendor
python -m http.server 8874 --bind 127.0.0.1 --directory "$STUDY_OUTPUT"
```

Open [the local study](http://127.0.0.1:8874/index.html). The scene preparation step checks the repository's pinned Three.js runtime and license. Omit `--vendor-dir` to retrieve those bytes if a staged copy is unavailable. WebGL 2 renders the spatial views. The scan timeline and image comparisons also work when a scene cannot load.

The builder samples 49 planes on the s1233 grid (1.5 mm per voxel, axes RAS). The contact point is where the central ray meets the smoothed patient surface. The transducer and image share the contact point, beam direction and lateral axis. Frame 12 intersects the gallbladder along its long axis. By frame 48 the probe has rotated a quarter turn. The acquired images correspond to these two named views. Between them the comparison identifies the nearest reference.

The synthetic images use CT tissue interfaces and a stationary scatter field. Acoustic properties, probe pressure and respiration are unmeasured. The earlier Blender pose plates are historical evidence for the first interaction study. The live scenes use the retained meshes and authored transducer dimensions.

With the built study served locally, run `node experiments/ultrasound-sweep/verify_playback.mjs` using the Gallery's Playwright environment. The browser regression checks the annotated laptop viewport through replay and verifies recovery from a missing scan frame. Set `MODEL_SURVEY_PLAYWRIGHT_MODULE` or `MODEL_SURVEY_BROWSER` for an existing installation.
