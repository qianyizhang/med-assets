# Whole-body anatomy · Spatial SVG assets

54 stable anatomy IDs, 54 primary SVGs, 15 named variants, 54 complete overlays
and 21 regional views. These editable teaching drawings are not 3D meshes,
patient scans or a rigged model. No disease or treatment overlays are included.

## Use

`manifest.json` maps each ID to its primary file, variants, source coordinates,
bounds, placement, body origin and current SVG hash. Each `preview` points to the
same self-contained SVG as `file`; render it directly as an image. Separate PNG
thumbnails and overview montages are no longer maintained.

- `atlas.svg`, `head.svg`, `kidney-depth.svg`: editable source drawings with
  independent coordinate spaces.
- `parts/`: one presentation view per anatomy ID. Paired organs or a distributed
  tissue can remain together in one view.
- `variants/`: explicitly named alternative depictions.
- `overlay-parts/`: complete source groups, including any inset depictions.
- `regions/`, `overview.svg`, `body-locator.svg`: context and whole-body location.
- `parts-index.csv`: compact index for design tools.

SVGs contain their definitions and have no scripts, remote images or downloaded
fonts. Separate image elements need no ID rewriting. When inlining several SVGs,
namespace IDs and their references or share one definitions block. The host owns
accessible interactions. See [integration](INTEGRATION.md) for selection,
body-origin highlighting and camera transitions.

## Coordinates and provenance

A cropped viewBox does not move geometry. Use `reassemble_source.image_placement`
to place an export back in its named source; retain `local_origin_transform` when
using a zero-origin editor. Head and kidney-section coordinates cannot be placed
in the full-body atlas without a separate transform. Annotation centers are
anchors, not anatomical centroids; an alternative view can have a different
center. Source paths, transforms, gradients, bounds and export clips remain intact.

`spatial.json` and `coordinates.json` describe schematic whole-body locators and
source placements. A `bodyBox` is not measured registration. Show the body origin
before switching to an independent orientation or scale; do not imply a literal
3D morph. The kidney section looks from the feet: anterior at top, patient right
at image left. Reproductive configurations and pregnancy views are alternatives,
not one person's simultaneous anatomy.

`source-relationships.json` retains original export derivation;
`artwork-provenance.json`, `license-registry.json` and [license notes](LICENSE-NOTES.md)
retain source-specific attribution and modification notices. Servier adaptations
are CC BY 4.0; reference-informed original artwork does not acquire that license.
No reference-image directory is bundled.

## Review and historical identities

`validation.json` and its 18 hash-bound `contact-sheets/` images retain the
2026-10-21 review of primary, variant and regional drawings. They are historical
evidence, not a fresh review of later edits. `SHA256SUMS.txt` and the manifest's
`sourceInputSHA256` retain that original snapshot. Current import exceptions are
recorded in [current-import-overrides.json](../../../metadata/current-import-overrides.json).
The current manifest binds edited head, abdomen and urinary SVGs to their current
bytes; their original derivation and review identities remain unchanged.

Shapes, scale, overlap, tissue counts and vessel/nerve routes are simplified.
Blood is a tissue sample and the reproductive overview is a locator. Fetal
illustration does not specify gestational age. Geometry checks and visual review
do not establish anatomical or clinical approval. These assets are unsuitable
for diagnosis, procedures or anatomical measurement.
