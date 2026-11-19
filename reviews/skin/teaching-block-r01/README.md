# Skin block and nail section review

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

| Scope | Isometric | Straight cut face |
| --- | --- | --- |
| Whole teaching setup | [Combined](combined-iso.png) | [Combined](combined-ortho.png) |
| Skin layers, left in overview | [Block](skin-block-iso.png) | [Block](skin-block-ortho.png) |
| Isolated follicle, hair, coil and duct from the same block | [Pore and shaft](appendages-iso.png) | [Coil to surface](appendages-ortho.png) |
| Nail insert, right in overview | [Proximal fold and free edge](nail-iso.png) | [Matrix, bed and plate](nail-ortho.png) |

The clean GLB supplied all four pairs. [Camera, visible meshes, dimensions and image hashes](renders.json) bind the complementary views. Scale is fixed within each pair. The axial extent and framing vary between isolated studies. The overview is the locator for the two disconnected sections. Use the existing [BP3D surface study](../2026-10-24-bp3d-envelope-r01-bounded-migration/bounded-record.json) for the original whole-body context. The added block has no counterpart at that magnification in the body envelope.

| Gate | Result and limit |
| --- | --- |
| Technical | Two fresh builds on Blender 5.2.3 produced the same GLB. The clean import had 27 meshes and 89,554 triangles. A cross-section through the bulb sampled a dermal depth interval of 0.970–3.676 mm with the follicle base at 1.480 mm. The coil and duct share 40 quantized inner/outer-ring coordinates. Rays sampled the open pore and adjacent rim at 4.100 mm and tested each layer interface at four positions. Nail plate contact gaps at matrix and bed samples were below 0.001 mm. The wrong-source envelope failed the node check as expected. These tests measure sampled interfaces and landmarks. |
| Visual | Inspected all eight images at 800 × 640 after clean reimport. Both cut sections and all required features are visible. The angled view resolves the pore rim and projection of the nail beyond the bed. The straight view distinguishes layer heights, the hair within its sheath and the proximal matrix beneath the plate. The isolated view removes the tissue behind the coil. Projected coil turns overlap in the straight view. |
| Anatomy | Reference-screened against the educational references linked in the [asset owner](../../../models/skin/teaching-block-r01/README.md). Side-neutral schematics; site-specific dimensions, histology, specialist validation and clinical use are outside this review. |
| Runtime | Unverified in an interactive WebGL viewer. Blender import and Cycles rendering were exercised. |

The first section had conspicuous vertical recesses continuing past the follicle and coil. Rebuilding local channels with depth-dependent relief removed the unused recesses. The revised export passed an independent import, a second build and the matched-view inspection. [Exact bound record](record.json).
