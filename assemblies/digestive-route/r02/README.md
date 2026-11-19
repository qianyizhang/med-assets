# Gastroduodenal teaching section

Follow the open stomach section through the narrowed pyloric lumen into the
duodenum. Gold and blue identify the common bile and main pancreatic ducts.
The violet channel leads to the single opening at the major duodenal papilla
on the posteromedial wall of the descending duodenum. Use the
[complete food route](../r01/README.md) to orient the upstream esophagus and
downstream bowel. The cutaway makes the walls, lining and duct entry visible
together. [Matched comparison and review](../../../reviews/digestive-route/r02/README.md).

## Reuse

Open the BLEND or import the GLB into a clean scene and select the
**Gastroduodenal section** meshes by name or glTF `extras.anatomy_id`.
There are separate stomach and duodenal walls, lining and cut faces,
plus the pyloric rim, the papillary rim and three ducts. The close view
isolates the duodenal group. The two incoming ducts can be selected
independently. Keep the violet channel and the papilla visible when explaining
the common opening. All generated parts use identity transforms in the
r01 teaching frame. Blender coordinates use metres, +X patient left,
−Y anterior and +Z superior. In glTF they become +X left, +Y superior and
+Z anterior.

The [r01 recipe](../r01/build.py) supplies the inlet, pyloric and duodenal
centerline controls. The r02 recipe reshapes the gastric body, limits sweep
foldover at tight bends, adds illustrative mucosal relief and leaves an
anterior window. The authored opening pierces the descending wall. Separate
duct surfaces meet the common channel in the schematic. The model represents
one common-channel drainage pattern. Relative duct thickness, folds and
wall thickness are illustrative, and no underlying scan was used to infer an
interior. [OpenStax stomach anatomy](https://openstax.org/books/anatomy-and-physiology-2e/pages/23-4-the-stomach) ·
[Duodenum and common channel](https://www.ncbi.nlm.nih.gov/books/NBK482390/).

The geometry derives from the authored portion of r01. The Workshop and
BodyParts3D exteriors in the r01 comparison source retain their
[original credits and terms](../r01/README.md#inputs-and-reuse). The reference
concept plate guided presentation. No illustration or scan surface is used
in the revised GLB.

## Replay

Restore the r01 GLB with the [teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).
From the repository root, choose a fresh output path and run Blender 5.2.3
with auto-execution disabled. On macOS get command-specific approval before
the first headless invocation.

```sh
out=.artifacts/gastroduodenal-replay
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/digestive-route/r02/build.py -- --output "$out"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P assemblies/digestive-route/r02/render.py -- \
  --glb "$out/gastroduodenal-section.glb" --output "$out/renders"
```

Open the GLB or BLEND from `$out`. Review `geometry.json` for exported part
identities and the tissue topology checks. The render receipt pins the r01
and r02 GLB hashes and all six PNGs. Use the PNGs with the same original and
updated camera IDs for a comparison.
