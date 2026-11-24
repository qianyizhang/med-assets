# Abdomen ultrasound tour

Open the [local tour](http://127.0.0.1:8874/index.html) and choose an abdominal sweep. The probe, patient and imaging sector occupy one 3D scene, with simulated and acquired ultrasound images below. The camera orbits the selected organ or the named region of a larger vessel. **Oblique**, **Axial**, **Coronal** and **Sagittal** set the 3D viewing direction. Select a preset again after orbiting to restore its framing. Changing the camera preserves the selected ultrasound frame and torso opacity.

Scrub the timeline, play the sweep, or jump directly to either named reference tick. **Anatomy overlay** reveals the CT segmentation in that plane. Each acquired image comes from a separate case. Differences in plane, level and crop are identified on the card or in Sources. **Keyframe assets** groups the current frame into 3D anatomy, simulated scan and acquired ultrasound. Open **Related anatomy** on a supported sweep for additional acquired views and their credits. Returning to the tour preserves the selected frame. Its management and display design are reserved for joint review after the abdomen walkthrough. [Full tour specification](../../docs/gallery/use-cases/ultrasound-anatomy.md) · [Reference records](research/README.md)

## Replay

Use Python 3.12 with NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0. Retrieve the public s1233 case, the two original gallbladder images linked in the reference study, and the hydrated LFS inputs for the atlas meshes and the other [acquired comparisons](research/acquired/). Run from the repository root with a fresh output directory.

```sh
python experiments/ultrasound-sweep/build_study.py "$S1233_CASE" "$LONG_AXIS_PNG" "$SHORT_AXIS_GIF" "$STUDY_OUTPUT"
python experiments/ultrasound-sweep/prepare_scenes.py "$STUDY_OUTPUT" --vendor-dir lessons/one-breath/.local/vendor
python experiments/ultrasound-sweep/build_abdomen.py "$S1233_CASE" "$STUDY_OUTPUT/sweeps"
python experiments/ultrasound-sweep/assemble_tours.py "$STUDY_OUTPUT"
python -m http.server 8874 --bind 127.0.0.1 --directory "$STUDY_OUTPUT"
```

For a compact serving directory, run `python experiments/ultrasound-sweep/assemble_tours.py "$STUDY_OUTPUT" --delivery "$TOUR_OUTPUT"` and serve `$TOUR_OUTPUT`. Choose a fresh destination. The compact build includes one copy of each byte-identical mesh, every distinct torso fit, and the runtime images. Keep the generated receipts and source inputs with the staging tree for replay.

Open [the local study](http://127.0.0.1:8874/index.html). The scene preparation step checks the repository's pinned Three.js runtime and license. Omit `--vendor-dir` to retrieve those bytes if a staged copy is unavailable. WebGL 2 renders the spatial view. The scan timeline and image comparisons also work when it cannot load.

The builders sample 49 planes per sweep on the s1233 grid (1.5 mm per voxel, RAS axes). The contact is where the central ray meets the patient surface. The 3D sector and image sampler share its contact, direction and depth. The [track data](abdomen-tracks.json) identifies the target, context, section palette, camera focus, depth and named keyframes. The gallbladder retains its original paired render. Each additional sweep has a verification receipt alongside its generated frames. The projections and overlay share the structure palette. Rebuild a sweep after changing its pose or section colors. The catalogue assembler verifies the acquired derivatives against their hashes and checks the input inventory before writing its tour and reference indexes.

The synthetic images use CT-derived tissue interfaces and illustrative brightness. Acoustic properties, pressure and respiration are unmeasured. The fitted [BodyParts3D exterior](../../models/skin/exports/bp3d-envelope-r01/README.md) is an illustrative body around the CT organs. The [gallbladder fit](display_body.py) uses ribs 6–10 and conforms its contact window to the CT surface. For the eight additional sweeps, the [contact-window fit](fit_abdomen.py) checks the first intersection of each incoming beam with the exterior. The lateral kidney and left posterior splenic windows use a staged arm position to expose the flank. Each sweep records its exterior and contact error. These are illustrative placements, with independent technique review still open. The earlier Blender pose plates remain historical evidence.

Run `python experiments/ultrasound-sweep/verify_assembly.py "$STUDY_OUTPUT"` against a fresh build to check the compact delivery, reference bindings and rejection of stale or corrupt inputs. With the built study served locally, run `node experiments/ultrasound-sweep/verify_playback.mjs` in the Gallery Playwright environment. Set `MODEL_SURVEY_PLAYWRIGHT_MODULE` or `MODEL_SURVEY_BROWSER` to use an installed browser. Verification walks all sweep routes, reference ticks, overlays, camera presets, playback, asset return, responsive layout and unavailable-media states.
