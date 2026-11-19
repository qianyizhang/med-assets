# Cardiovascular circuit review

Restore the local screenshots from the [body-systems teaching backup](../../sites/body-systems-survey/README.md#restore-the-media).

The [assembly](../../assemblies/cardiovascular-loop/README.md) demonstrates one complete directed loop from the right atrium through both beds and back. Native editable scene SHA-256 `e6ee8413a5b59eb2f87c4a5064d509be306ca830b9f212587a06f8092390e58c`. Export SHA-256 `89f80adddacddb3915c82d971ac7d4c68c180344eb1ae47dda2d659fa55ab4f2`. [Render bindings](renders.json) identify the exact GLB, screenshots, visible nodes, scales and cameras.

| Clean-import evidence | Straight | Isometric |
|---|---|---|
| Entire loop, labels and flow arrows | [Anterior](loop-ortho.png) | [Oblique](loop-iso.png) |
| Right atrium and ventricle, tricuspid and pulmonary valves | [Tilted anterior](right-valves-ortho.png) | [Right-heart detail](right-valves-iso.png) |
| Left atrium and ventricle, mitral and aortic valves | [Tilted anterior](left-valves-ortho.png) | [Left-heart detail](left-valves-iso.png) |

- **Technical passed.** Two independent runs of the build produced identical portable GLBs and placement files. Clean import preserved 50 nodes. The [decoded-position check](../../assemblies/cardiovascular-loop/check.py) traced 10 ordered transitions, tested all 20 ends and counted 3/3/2/3 tricuspid, pulmonary, mitral and aortic leaflets. Bridge cap centres, pool surface vertices and bed ends matched within 0.001 mm. Native valve rings were matched at the aperture centre within 0.223051 mm of their bounding-box centre. The tolerance of 0.3 mm is below 5% of the smallest source annular radius. Intentional 2 mm displacement of a right-atrial endpoint failed the check. Image hashes and GLB identity passed.
- **Visual passed with limits.** Inspected six actual GLB renders. The anterior view shows both beds and the complete line without unrelated crossings. Arrowheads and bed forks remain distinct without relying on color. The valve close-ups expose the annular apertures at matched scale within each pair. Direction cones, bridge tissue and valve leaflets intentionally overlap at a few ports. Individual structures can be isolated. Labels are angled and overlap some anatomy in the isometric overview. Use the anterior overview to read them. An early export lost its matte colors on import. Writing the base color into the exported shader and re-rendering restored the two circulation colors and distinct valve and bed materials.
- **Anatomy reference-screened.** The direction and ordering match the NHLBI reference linked in the assembly. ED pool and valve shape come from a procedural atlas. The schematic ports and exploded relative positions have no anatomical registration, lumen or specialist validation.
- **Runtime unverified.** Blender 5.2.3 imported and rendered the exact GLB. No live viewer or frame-time test was run.
