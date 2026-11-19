# Right root and ramus teaching insert

Open the standalone GLB or editable Blender scene to inspect the dorsal
root with its included ganglion, ventral root, mixed nerve and authored
ventral ramus and plexus bridge. Isolate these four parts by name or glTF
`extras.anatomy_id`. The oblique junction image crops the long roots to
show how they meet the mixed nerve. The [full pathway and sensory study](../README.md)
provides the brainstem, spinal cord, sciatic course and separate ear studies.

The four meshes are the exact selection from the original
[root view](../../../reviews/nervous-senses/README.md). Their triangle corners
and orientation agree after clean reimport on a one-micrometre grid.
The derivative keeps their staged placement in Blender metres and adds
distinct matte materials and readable names. Source provenance on each
node refers to the original assembly. The dorsal root and ganglion use one
continuous mesh. The anatomical frame and attribution follow the
[source study](../README.md#geometry-and-ownership). The depicted bridge and
root group are illustrative. The selected example has no assigned
patient-specific level.

## Replay

Restore the original `nervous-senses.glb` from the
[teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).
From the repository root, use a fresh output location and Blender 5.2.3
with auto-execution disabled.

```sh
out=.artifacts/body-systems-refinement-2026-11-19/nervous-root
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/nervous-senses/root-study-r01/build.py -- --output "$out"
```

The build saves `right-root-ramus.blend` and `right-root-ramus.glb`, verifies
the four named parts and writes six exact images with their render and model
hashes under `renders/`. The original and updated pairs share camera, scale
and lighting. The junction uses a closer camera with part of the long stems
outside the frame.
