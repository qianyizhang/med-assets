# Skin section and nail unit

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Use the [BP3D envelope](../exports/bp3d-envelope-r01/README.md) for whole-body orientation, then open [the cut sections](skin-block.glb). At the skin cut face, the thin superficial epidermis dips into the deeper dermis. The dark hair passes through its cut follicular sheath. The teal eccrine coil drains through a separate duct and open pore. The lobules belong to the subcutaneous tissue. The second section shows the nail plate over the pink bed and the mauve matrix under its proximal root. Each structure has a named mesh in the GLB and [editable Blender scene](skin-block.blend). Select a named object and use Local View to isolate it.

## Scope and sources

The compared BP3D model contains one external surface (FJ2810, GLB SHA-256 `d86719833a17dc7b45c8eb970498f1e2feefd352b5812942f4b147a9ffcfbe4f`). Its [source review](../../../reviews/skin/2026-10-24-bp3d-envelope-r01-bounded-migration/bounded-record.json) retains the existing locator and attribution. The [skin-detail plate](../../../body/2d-v4/whole-body-anatomy-v4-spatial/regions/skin-detail.svg) specifies the cutaway features in 2D. This teaching addition supplies editable depth, isolated appendages, a hollow pore and a separate nail insert for the body-systems survey. The skin owner maintains one procedural build, one editable scene, one portable export and four evidence pairs. Neither the atlas nor the SVG is embedded in the GLB.

Layer and appendage relationships were screened against OpenStax, *Anatomy and Physiology 2e*, [§5.1](https://openstax.org/books/anatomy-and-physiology-2e/pages/5-1-layers-of-the-skin) and [§5.2](https://openstax.org/books/anatomy-and-physiology-2e/pages/5-2-accessory-structures-of-the-skin). The plate is derived from Servier Medical Art by Les Laboratoires Servier, CC BY 4.0, and retains its [modification and rights notice](../../../body/2d-v4/whole-body-anatomy-v4-spatial/LICENSE-NOTES.md). The two 3D sections were authored from coordinates for this study. No reference mesh, figure, texture or image-generated geometry was copied. The survey concept informed the cutaway presentation. A redistribution license for this new geometry remains unspecified.

The build uses millimetres and exports metres. Blender +Z points toward the surface, +Y away from the cut face and +X toward the free nail edge. glTF uses +Y up and +Z toward the cut face. These local, side-neutral samples have no registered body position. The nail unit is reduced to share the overview; relative dimensions, colors, layer thickness and coil shape are illustrative. A longitudinal half section omits the near nail fold. The skin relief brings the coil forward of the cut for visibility.

## Replay and review

From the repository root with Blender 5.2.3 available as `blender`, use new output directories.

```sh
skin=models/skin/teaching-block-r01
blender -b -t 1 --factory-startup --disable-autoexec --python-exit-code 1 -P "$skin/build.py" -- .artifacts/skin-block-replay
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$skin/check.py" -- .artifacts/skin-block-replay/skin-block.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/skin-block-replay/skin-block.glb --views "$skin/views.json" --output .artifacts/skin-block-review
python3.12 tests/review_records/validate_record.py reviews/skin/teaching-block-r01/record.json
```

[Review, views and technical limits](../../../reviews/skin/teaching-block-r01/README.md)
