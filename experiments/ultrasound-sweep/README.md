# Gallbladder sweep interaction study

Compare direct probe control with guided stops on the same local gallbladder tour. Open the built index in a browser. Switch **Interaction design** to keep the current pose while trying the other variant. In **Probe control**, drag the probe view. In **Guided stops**, playback pauses at each teaching view. Both offer keyboard scrubbing, anatomy reveal, point-to-identify, and a side-by-side acquired reference. **Keyframe assets** breaks the selected pose into patient and probe, internal anatomy, simulated image and acquired evidence. Return takes you to that pose.

The [collection brief](../../docs/gallery/use-cases/ultrasound-anatomy.md) owns the accepted product decisions. This standalone study is for choosing an interaction before Gallery integration. Both versions use one ordered set of poses, anatomical sections and scan frames. This sequence can also drive later video rendering. The design choice and independent ultrasound review remain open.

## Replay

Use Python 3.12 with NumPy 2.2.6, SciPy 1.16.1, scikit-image 0.25.2 and Pillow 11.3.0. Retrieve the public s1233 case and the two original images linked in the [reference study](research/README.md). The builder checks their identities. Run from the repository root, passing a fresh output directory.

```sh
python experiments/ultrasound-sweep/build_study.py "$S1233_CASE" "$LONG_AXIS_PNG" "$SHORT_AXIS_GIF" "$STUDY_OUTPUT"
blender --background --factory-startup --python-exit-code 1 --python experiments/ultrasound-sweep/render_pose.py -- "$STUDY_OUTPUT"
python experiments/ultrasound-sweep/finish_plates.py "$STUDY_OUTPUT"
```

The first command samples 49 planes in the isotropic s1233 grid (1.5 mm per voxel, axes RAS). Contact is the intersection of the central ray with the smoothed body envelope. The probe and image use the same contact, axis and lateral basis. Frame 12 intersects the gallbladder along its major axis. Frame 48 rotates the lateral basis a quarter turn. Tissue interfaces and stationary scatter generate the illustrative brightness. The CT supplies geometry and tissue context. Acoustic properties, pressure and breathing are unmeasured.

The Blender command uses Blender 5.2.3 to render a curved-array probe and abdominal cutaway with the right ribs, liver and gallbladder. The final command composites the internal anatomy through a soft window while preserving the probe. Only the inset uses a separate whole-body atlas. Keep the generated review bundle under ignored `.artifacts/` for this design comparison. The recipe, source identities and reference terms live here.
