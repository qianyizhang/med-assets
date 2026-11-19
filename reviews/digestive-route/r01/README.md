# Digestive route review · 19 November 2026

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Editable composition, attribution and replay](../../../assemblies/digestive-route/r01/README.md). GLB SHA-256 `f91ee8cb160b182d932b991a1dff61d465213431b87cff535cf907fa8822834a`. Delivered BLEND SHA-256 `bcad703846f7003def27934d19e317ff5e24787d32e000c856400deec92d32d9`. The BLEND container changes across saves. Two fresh builds generated identical GLB bytes.

| Inspection | Isometric | Straight orthographic |
|---|---|---|
| Source regions at left, continuous schematic at right | [Image](context-iso.png) | [Anterior](context-ortho.png) |
| Mouth to outlet in isolation | [Image](food-iso.png) | [Anterior](food-ortho.png) |
| Parotid secretion enters the oral cavity | [Image](saliva-iso.png) | [Anterior](saliva-ortho.png) |
| Bile and pancreatic branches reach the duodenum | [Image](duodenal-entry-iso.png) | [Anterior](duodenal-entry-ortho.png) |
| Rectal inlet and terminal outlet | [Superior opening](outlet-iso.png) | [Anteroinferior opening](outlet-ortho.png) |

**Technical — passed for teaching continuity.** Clean import recovered 22 individually named meshes. [Decoded geometry check](joins.json) found nine pairs of exactly coincident 32-vertex boundary rims between consecutive food segments. All ten food segments have two open rims. Four accessory confluences matched within one micrometre by rim center. Entry center to nearest recipient vertex measured 2.25 mm at the oral cavity and 1.72 mm at the duodenum, within the modelled entry diameters. These overlays contact recipient surfaces without a Boolean cut. A negative test shifted the exported esophagus 1 mm and the same verifier rejected the pharynx–esophagus join.

**Visual — passed with limitations.** Clean-import paired renders use matched scale within each pair. The front overview separates the external anatomy and route. Source liver hides much of the stomach. The transverse colon crosses in front of the duodenum. Isolating the ducts and recipient removes the colon occlusion. The mouth opening appears best in the angled view, the anal outlet in the inferior view. The accessory common channel is short at overview scale. [Exact visible nodes, camera scale and image hashes](renders.json).

**Anatomy — reference-screened.** Food order, hepatic/cystic convergence, duodenal delivery and salivary entry follow the cited sources. The source exterior groups preserve local relationships. The diagram at right is an intentionally shortened, opened and uncoiled teaching tract. It represents route order, not measured luminal diameters or individual anatomy. Specialist review remains open.

**Runtime — unverified.** Clean Blender reimport and Cycles rendering were exercised. Browser rendering, interaction performance and clinical use were not tested.
