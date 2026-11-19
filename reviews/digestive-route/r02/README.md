# Gastroduodenal section review · 19 November 2026

The r01 teaching render shows duct branches over an undivided duodenal
surface. The r02 section exposes the two mucosal surfaces, retains the
pyloric constriction and shows a single papillary opening opposite the
separate incoming ducts. The
[editable assembly](../../../assemblies/digestive-route/r02/README.md)
owns replay and source references.

The reviewed local output is
`.artifacts/body-systems-refinement-2026-11-19/digestive-r03/`.
The input revision is `219eee4d28acf777c283776adcfaa0945e07371a`.
`geometry.json` binds the executed recipe hash and the portable and editable
files. The GLB is 563,248 bytes, SHA-256
`07ea22658bea2f3106c6afa69e8917ff5adef4fbc3bac368658523d072258af0`.
The 426,120-byte BLEND has SHA-256
`4bfafdaf1e74fe5a4354bfa3ddd7e5ce6fc6d4e6664949b9fc33f56240ea0a22`.
The full r01 export includes other teaching scenes and source exteriors,
so its file size does not measure section simplification.

| Inspection | Original | Updated |
| --- | --- | --- |
| Anterior, fixed scale and lighting | `renders/original-ortho.png` | `renders/updated-ortho.png` |
| Isometric, fixed scale and lighting | `renders/original-iso.png` | `renders/updated-iso.png` |
| Isolated duodenal group | | `renders/duct-entry-ortho.png` and `renders/duct-entry-iso.png` |

- **Technical** · Blender 5.2.3 clean import recovered all 11 named meshes,
  materials and 29,112 triangles. World positions agree at 1 μm rounded
  precision. The welded 25,656-triangle tissue shell is one connected,
  consistently oriented component. It has Euler characteristic zero and no
  intersection between non-neighbour triangles in the clean import. That
  check covers the wall and its one through-wall papillary aperture. Ducts
  remain authored teaching overlays. A modified copy of the GLB failed the
  render recipe with a receipt mismatch before output creation.
- **Visual** · The first sweep folded at the lesser curvature and hid most
  of the bile branch. Limiting the inner bend radius removed the foldover
  and a new posterior course made both duct branches readable. In the front
  comparison the short common channel is partly obscured. The angled detail
  shows the gap in the raised papillary rim. Use the legend for branch names.
  The shared render receipt records camera scale, both GLB hashes and image
  hashes. Grayscale and live accessibility remain unverified.
- **Anatomy** · Reference-screened for representative pyloric and common
  duct entry. The two authored ducts follow a common-channel example. Source
  imaging, interindividual variants and specialist review remain open.
- **Runtime** · Blender build and reimport passed. Browser behavior and
  animation were outside this asset check.
