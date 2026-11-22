# Respiratory teaching animation

Eleven GLB clips add illustrative respiratory motion to the retained Anatomy Workshop organ surfaces and an authored diaphragm. They use the [Workshop coordinate frame](../anatomy-workshop-r1/README.md#geometry-and-coordinates) in glTF metres, with +Y superior. Motion is authored for teaching and has no patient-specific or clinical validation.

## What moves

- Five lung lobes share an inspiration field. At peak inspiration the most superior vertices descend about 0.18 mm on the left and 0.30 mm on the right. Lower regions descend up to about 18 mm and widen preferentially in lateral and anterior directions. Each lobe deforms at the vertex level.
- The open schematic diaphragm flattens as the dome descends 21 mm at its centre and 3 mm at the rim. It depicts the motion without modeled attachments or openings.
- Liver and gallbladder descend up to 8 mm, stomach and spleen 6 mm, kidneys 4 mm, pancreas 3 mm and the source heart 2 mm.

Each clip is four seconds long, with peak inspiration at 1.6 seconds and matching start and end poses. The separate [Cardiac Atlas animation](../../heart/Cardiac_Atlas_Animated/) had a uniform teaching fit in the original body viewer and ran at an illustrative 75 beats per minute. That optional playback used five heart cycles per respiratory cycle and carries its own source and verification.

## Files and attribution

- The eleven `*_breathing.glb` files are self-contained exports. [The animation manifest](animation-manifest.json) records their delivered identities, exact static inputs, source and motion metadata. Keep the [Breathing attribution](NOTICE.md), [CC BY 4.0](CC-BY-4.0.txt) and [Workshop source notices and licenses](../anatomy-workshop-r1/docs/licenses/) with source-derived assets.
- [Breathing_Assembly.blend](Breathing_Assembly.blend) is the delivered editable assembly with lung and diaphragm shape keys and neighbor translations at 30 fps, frames 1–121.
- [Expiration](expiration.webp) and [inspiration](inspiration.webp) are retained Blender renders. The earlier Site packaged the GLBs as a ZIP and used [a historical component check](test_motion.mjs) with [recorded results](component-qa.json). That JS check expects the original Site's viewer tree and dependencies. Its renderer and image-decoding doubles limited the recorded result to DOM behavior, GLB loading and CPU deformation.

## Replay and verify

Hydrate the [Workshop meshes](../anatomy-workshop-r1/meshes/) and the delivered Breathing GLBs and Blender file through Git LFS. Run from the repository root with Python and NumPy plus Blender. The tested combination was Python 3.13 with NumPy 2.3.4 and Blender 5.2.3 Release Candidate. An explicit `--source` for the first command selects a directory containing the same manifest-pinned static meshes. Assembly accepts any directory with the eleven animated GLB filenames, and defaults to this package's delivered clips.

```sh
replay_dir="$(mktemp -d)"
python3 body/breathing/build_motion.py --output "$replay_dir/clips"
blender --background --factory-startup --python-exit-code 1 \
  --python body/breathing/native_assembly.py -- \
  --source "$replay_dir/clips" --output "$replay_dir/Breathing_Assembly.blend"
blender --background --factory-startup --python-exit-code 1 \
  --python body/breathing/verify_replay.py -- \
  --clips "$replay_dir/clips" --assembly "$replay_dir/Breathing_Assembly.blend"
```

Use fresh output paths under an existing directory. The generator verifies the size and digest of every static mesh and emits a channel-count receipt with the GLBs. The verifier requires exact bytes for the ten Workshop-derived clips and allows up to 10 nm of float rounding confined to the diaphragm position morph. It checks clip names, channels, loop poses, peak phase, lung apex restraint, diaphragm shape and organ translations. The Blender check compares object names, mesh counts, action channels and sampled motion against the delivered assembly. Blender 5.2 groups imported actions into 11 datablocks across the same 67 animated objects and tracks. This verifies replayed motion in Blender and at the GLB level. The retained Site component results have their original scope.
