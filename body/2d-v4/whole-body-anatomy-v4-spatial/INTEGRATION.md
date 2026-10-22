# Link a part to its whole-body origin

The stable identifier is manifest.parts[i].id (for example, kidneys). Use that ID for selection, explanations and any future disease/treatment overlay. This package contains normal educational anatomy only.

## Select the right file

- A presentation part is entry.file: one anatomical depiction with a tight crop.
- A named alternative is one of manifest.variants. Its sourceView explicitly describes its direction and scale.
- A contextual region is entry.sourceView.regionFile, when present. The 21 region IDs match regions.json and spatial.json.
- A source SVG is entry.source_file / entry.sourceView.sourceFile. Its coordinate space is independent unless it is atlas.svg.
- overlay-parts preserves the complete canonical group in atlas coordinates. These groups may include inset/thumbnail depictions; they are not all literal geometry inside the body silhouette.

## Show location before detail

1. Show body-locator.svg or overview.svg with the whole-body viewport [78, 25, 405, 955].
2. Read originBox = entry.bodyOrigin.bodyBox in atlas.svg anterior body coordinates. Highlight the box or the paired entry.bodyOrigin.points. Use the bilingual location text for the visible explanation and accessible description.
3. For same-source atlas detail, move the camera/viewBox toward entry.sourceView.viewBox and show the indicated regionFile. Do not translate or rewrite organ paths.
4. For a different source, keep the body locator visible and use a visible connector or transition to the new panel. Show sourceView.orientation and bodyOrigin.orientationChange. The head and transverse kidney sources are not registered 3D body geometry, so do not morph their paths into the frontal anatomy.
5. To return, preserve the selected ID and restore the whole-body viewport. Keep focus on the selected structure. Honor reduced-motion settings by replacing camera/connector motion with an immediate state change.

bodyOrigin.regionBodyBox records the contextual region footprint, while bodyOrigin.bodyBox is the canonical structure's locator. For the kidney depth view, the region box marks a representative transverse slab; the canonical kidney box marks the pair's broader position. Neither is a measurement or exact scan plane.

## Coordinate placement

For a tight SVG crop inserted back into its own named source, use entry.reassemble_source.image_placement x, y, width and height. A nonzero viewBox origin does not move the paths. For an editor that needs a zero-origin drawing, use entry.reassemble_source.local_origin_transform and a [0, 0, width, height] canvas. Do not use this source-space placement to position head/section geometry on the body.

For a locator embedded at display width W and height H with preserveAspectRatio="xMidYMid meet", scale = min(W / 405, H / 955); offsetX = (W - 405 * scale) / 2; offsetY = (H - 955 * scale) / 2. Map an atlas point (x, y) to (offsetX + (x - 78) * scale, offsetY + (y - 25) * scale). Use the same transform for locator highlights and connectors.

Every standalone SVG has local definitions and no script/network dependency. Keep individual files as image elements, or namespace IDs when inlining multiple SVGs. Host applications supply interaction and accessibility behavior. Keep adaptation attribution with assets as documented in license-registry.json and LICENSE-NOTES.md.
