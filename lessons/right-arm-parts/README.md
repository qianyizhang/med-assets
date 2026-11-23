# Right-arm practice and answer plates

Compare the elbow capsule with the ulnar nerve in the same posteromedial view. At the shoulder, switch between the exposed glenoid and the rotator cuff with the scapula fixed. The Gallery shows four unlabeled practice images and two annotated answers. [Gallery lesson acceptance](../../records/work-items/items/AG-GAL-029-right-arm-part-lessons.md)

[Layer selections](arm-lesson-layers.json) name the four exact GLBs, selected nodes and cameras. The Gallery build copies this file into its project. [Landmark coordinates](anchors.json) are in Blender world axes and come from the reviewed posteromedial nerve and anterior/posterior cuff views. The glenoid, labral rim and capsule labels use pixels placed on the approved clean-import renders. [Nerve bindings](../../reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v2/raw-128/bindings.json) · [Cuff checks](../../reviews/joints/2026-10-30-rotator-cuff-r01/checks.json)

## Rebuild and compare

Run from the repository root with the four GLBs hydrated. Use Blender 5.2.3 Release Candidate `fab76e95306d` with Cycles CPU and Pillow 11.3.0 with libwebp 1.5.0 and macOS Supplemental Arial. Pass `--font` to use an alternate path to the same font file.

```sh
arm_replay="$(mktemp -d)"
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python lessons/right-arm-parts/render.py -- --out "$arm_replay/renders"
python3 lessons/right-arm-parts/plates.py \
  --renders "$arm_replay/renders" --out "$arm_replay/webp" --verify
```

The renderer checks every input identity before opening a GLB and starting a render. The plate command compares all six WebPs with the retained Gallery copies before writing verified outputs. The four practice views are 640 × 480. The elbow and shoulder answer images are 1290 × 528 and 1940 × 528.

The [earlier right-arm source replay review](../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/README.md) retains its own three bilingual plates, camera targets and asset identities. Both renderers use the lesson's [orthographic scene setup](arm_scene.py).

The source geometry and lesson derivatives retain Z-Anatomy and BodyParts3D credit. The views illustrate static gross surface relationships. [Source attribution and license](../../sources/datasets/z-anatomy/joint-regional-studies/upstream/ATTRIBUTION.md)
