# Magnified lymph-node teaching section

Trace the three afferent entries to the cut section and locate the efferent
exit at the hilum. The ivory arrow is an illustrative direction cue. The
capsule, section face, cortical follicles, illustrative sinus band, entries,
exit and arrow are selectable. Use the
[regional return assembly](../r01/README.md) to follow the longer route
and locate its authored venous-angle junction.

The section is authored for reuse in a lesson. It uses Blender metres,
+X toward the pictured hilum, +Z up and −Y toward the cut-face camera.
The glTF mapping is (X, Z, −Y). It has its own illustrative dimensions and
frame. The node interior is a teaching schematic. The
[r01 source notices and reference screening](../r01/README.md#admission-coordinates-and-rights)
document the regional material. The new section is built from its own design
coordinates. [Review and evidence](../../../reviews/lymphatic-return/r02/README.md).

## Replay

From the repository root with Blender 5.2.3, use a fresh output bundle.

```sh
package=assemblies/lymphatic-return/r02
study=.artifacts/body-systems-refinement-2026-11-19/lymphatic
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P "$package/build.py" -- --output "$study/checked-build"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/render_teaching.py -- --glb "$study/checked-build/lymph-node-section.glb" \
  --views "$package/views.json" --output "$study/checked-renders"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P "$package/check.py" -- --glb "$study/checked-build/lymph-node-section.glb" \
  --renders "$study/checked-renders"
```

The build exports an editable `lymph-node-section.blend` and a portable GLB.
The receipt binds the section and passage-isolation image pairs to the
exact exported model.
