# Lymphatic return · 19 November 2026

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Source, portable export, placements and replay](../../../assemblies/lymphatic-return/r01/README.md). GLB SHA-256 `e46b62ae432daccaf0b216c15179c98473e7817c296793fd774f1351cddf4507`. Editable BLEND `8a6faacea87110f11520470f21214d2a5bf863f1f6cb4017dd88f21d67013587`. [Per-image hashes, source identity, cameras and visible meshes](renders.json).

| Inspect | Isometric | Straight |
|---|---|---|
| Tissue through node, duct and venous confluence | [Overview](overview-iso.png) | [Anterior](overview-ortho.png) |
| Initial capillaries and node entry | [Entry](nodal-entry-iso.png) | [Anterior](nodal-entry-ortho.png) |
| Afferent vessel, illustrative passage and efferent vessel | [Inside](node-transit-iso.png) | [Anterior](node-transit-ortho.png) |
| Short terminal bridge and three named veins | [Venous angle](venous-angle-iso.png) | [Posterior](venous-angle-ortho.png) |
| Thymus above and spleen to subject left | [Locators](organ-locators-iso.png) | [Anterior](organ-locators-ortho.png) |

**Technical.** Clean import recovered 23 meshes. Sixteen measured landing points on named mesh surfaces agreed to within 2.4 × 10⁻¹⁰ m. Rays from the trunk end and the lower duct cap started inside the imported cisterna. A 30 mm lateral displacement of the cisterna caused the revised geometry check to fail. The original check had tested only the intended ellipsoid coordinates. A second independent process reproduced the measurements. Fresh rebuilds produced equivalent scenes, named nodes, materials and oriented triangles including per-corner attributes. Blender changed triangle index order on the two UV spheres, hence the two GLB byte streams differ.

**Visual.** Independent inspection of ten clean-import images found the node, long duct and vein join visible at their respective scales. The capsule hides the gold passage in the combined view. Isolate the three gold structures to inspect it. A small disconnected feature in the source afferent/efferent set is visible in the straight transit view. Follow the documented entry and exit coordinates to identify the selected teaching route. The terminal bridge is axially foreshortened in the oblique view.

**Anatomy.** Reference-screened for directional teaching. Source surfaces and authored connections have separate names. The setup does not establish lymph sinus microanatomy, lumen patency, measured flow, patient registration or clinical validation.

**Runtime.** Blender import and static CPU rendering exercised. Live viewer interaction and performance are unverified.
