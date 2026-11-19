# Bilateral urinary junctions and a renal filtration inset

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Open the [GLB](urinary-junctions.glb) or [editable Blender scene](urinary-junctions.blend). Each Workshop kidney section exposes the collecting system and single ureter origin. Follow the left or right proximal, middle and distal ureter into its corner of the trigone. The lower trigone corner leads to the bladder neck and outlet. Teal arrowheads are separately selectable flow cues. The enlarged lateral inset traces blood through a glomerular tuft and shows filtrate entering capsular space and the proximal tubule. Select the named segments and use Local View, or inspect the [seven matched pairs](../../../reviews/urinary-junctions/r01/README.md).

## Sources and placement

The [Workshop](../../../body/anatomy-workshop-r1/README.md) supplies two gross renal exteriors, their authored collecting sections, and a separate bladder asset with long ureters. Its exterior view hides the internal joins. The Workshop long ureters start at enriched points inside the renal exteriors, while its cutaway kidneys already have short ureter origins. Using both would duplicate the proximal route. This assembly takes the cutaway origins, routes each side through the Workshop course landmark at X=±.026 m and lands on its trigone corner. Independent segment names make each transition visible in isolation. The [2D urinary locator](../../../reviews/urinary_region/README.md) remains a separate overview. This composition owns the connections, inset and evidence used by the survey.

[Input GLB paths and SHA-256](inputs.json). [Junction coordinates](junctions.json) are in Blender metres, +X patient left, +Y posterior, +Z superior. glTF maps (x,y,z) to (x,z,−y). The selected kidney and bladder sections retain Workshop world coordinates. The ureter starts and outlet connection are anchored to the centres of the corresponding exported end rings. The bladder connection uses the source named trigone vertices. The filter inset is enlarged and displaced laterally for visibility. The pictured capillary tuft, opened capsule profile, arterioles, proximal tubule and arrows are schematic. [OpenStax, Anatomy and Physiology 2e §25.4](https://openstax.org/books/anatomy-and-physiology-2e/pages/25-4-microscopic-anatomy-of-the-kidney)

Jakob Wasserthal and TotalSegmentator contributors, University Hospital Basel, TotalSegmentator v2.0.1, CC BY 4.0. Preserve the Workshop's [source and modification notices](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md) and companion licenses. The sections and bladder are previously authored educational forms in the Workshop frame. This derivative selects and recolors their surfaces and adds ureters, neck, inset and overlays. No third-party illustration was incorporated.

## Replay

From the repository root with hydrated inputs and Blender 5.2.3:

```sh
package=assemblies/urinary-junctions/r01
out=.artifacts/urinary-junctions-new
blender -b -t 3 --factory-startup --disable-autoexec --python-exit-code 1 -P "$package/build.py" -- --output "$out"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$package/check.py" -- --glb "$out/urinary-junctions.glb" --junctions "$package/junctions.json"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb "$out/urinary-junctions.glb" --views "$package/views.json" --output "$out/views"
```
