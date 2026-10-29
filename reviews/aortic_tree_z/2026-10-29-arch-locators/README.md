# Private arch locator review — issue #149

Prepared on `wip/aortic-arch-locators-149` from main
`384b785c5f647234077dc34dcae56fbb10b6178c`. No remote branch, PR, raster publication
or Site delivery is part of this private preparation. PR #153 remains unchanged.

The teaching sheet and two Original/Updated comparisons add bilingual numbered
source locators. Actual source-node surface ray hits bind every leader in both
views. The source's joined brachiocephalic/right-carotid group is labeled as a
composite, with no invented internal component split.

## Evidence and scope

- [render.json](render.json): exact GLB identity, nine meshes/15 source structures,
  all-vertex source/import coordinate checks, topology/material signatures, new
  cameras and eight named-node ray hits with projected pixel centers. Source bytes,
  imported vertices, topology, transforms and materials are unchanged.
- [visual-binding.json](visual-binding.json): actual Inkscape exports, image hashes,
  exact source-pixel equality in Original, localized editorial changes in Updated,
  visible numeric badges and byte-identical SVG composition replay.
- [review.json](review.json): local review status, deterministic render replay,
  selected checks, iteration finding and remaining limits.

Source model: `aortic_tree_z__r02`, retained PR #33, SHA-256
`d4b3dbd2d09fd76795f47bb96844acdeba5f1b4f48dd630f2a294f33816deaeb`, 881,168 bytes.
Source-named bilateral subclavian, renal and iliac groups agree on +X = left.
The documented glTF `(x,y,z)` → Blender `(x,-z,y)` import basis matches every
vertex exactly. New cameras preserve that laterality: source left is screen right.

Historical renders remain valid historical evidence. Their camera script
`tests/aortic_tree_z/render_z_aortic_context.py` (SHA-256
`04ae8d8a014a7b571a77708d7f840accf8f11d48822ed19f0b95981d36670086`)
is declared unbundled by the migrated dependency manifest and absent from retained
Git history. That unavailable recipe was reported before new views were chosen.
New Original captures use unchanged exact source geometry and the recorded camera;
they are not claimed pixel-identical to the historical contact.

The source's open/unfused junctions, cropped ends, composite meshes and illustrative
material are preserved. A source identity pass is not specialist anatomy approval.
Static native rendering and pixel checks do not certify browser behavior.

Attribution and **CC BY-SA 4.0** terms are retained on the sheets and in the
[teaching guide](../../../lessons/aortic-arch-locators/README.md).
