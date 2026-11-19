# A regional lymphatic route to the left venous angle

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Open the [portable GLB](lymphatic-return.glb) or [editable Blender scene](lymphatic-return.blend). Trace the lower-body tissue bed into the afferent vessel, follow the gold passage through the node to the efferent trunk and cisterna chyli, then trace the source thoracic duct and green terminal bridge to the junction of the left jugular and subclavian veins. The blue brachiocephalic vein continues medially. Spleen and thymus are separate regional landmarks. Select named objects in the outliner and use Local View to isolate them. The [five matched pairs](../../../reviews/lymphatic-return/r01/README.md) give the node interior and terminal join their own views.

## Admission, coordinates and rights

The [seven-route scaffold](../../../models/lymph-collecting-routes/source-context-r01/README.md) has capped ends and 372 triangles. The [single node](../../../models/lymph_node/README.md) supplies afferent, efferent and capsule surfaces. Its conflicted vascular-network label precludes using that network as an intranodal route. This assembly uses just the source thoracic duct and those three node meshes. The new bridges supply relationships absent from either source. Maintain them here with the editable composition and its review for the systems survey.

Blender metres, +X subject left, +Y posterior, +Z superior. glTF uses +Y superior and +Z anterior. The source duct retains world coordinates. The node is enlarged 2.4× about its bounds. The spleen and thymus retain their source sizes. [Placement and join coordinates](placement.json) record the translations after world-coordinate baking. Cross-source organ placement and the representative lower-body tissue bed are editorial. Source cap centres (0, .040, −.200) and (.045, .005, .210) m fix the start and end of the adapted duct. The intranodal passage, collecting links and venous confluence are illustrative. OpenStax's description of a lower-body collecting route and typical thoracic drainage supports the sequence. [Anatomy and Physiology 2e §21.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/21-1-anatomy-of-the-lymphatic-and-immune-systems)

[Input identities](inputs.json) bind the commissioned duct scaffold, the [HRA male lymph node](../../../sources/datasets/hra/lymph-node-v1.2), [HRA female spleen](../../../reviews/spleen/source-locator-r01/README.md) and [BP3D thymus](../../../models/thymus/README.md). Kristen Browne and Heidi Schlehlein, HuBMAP/HRA, CC BY 4.0. BodyParts3D © DBCLS, CC BY 4.0 per its retained license record. Changes include selection, scale/translation, matte materials and additions authored for this assembly. The commissioned scaffold has separate rights. No uniform redistribution license is established.

## Replay

From the repository root, with hydrated inputs and Blender 5.2.3:

```sh
package=assemblies/lymphatic-return/r01
out=.artifacts/lymph-return-new
blender -b -t 3 --factory-startup --disable-autoexec --python-exit-code 1 -P "$package/build.py" -- --output "$out"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$package/check.py" -- --glb "$out/lymphatic-return.glb" --placement "$package/placement.json"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb "$out/lymphatic-return.glb" --views "$package/views.json" --output "$out/views"
```
