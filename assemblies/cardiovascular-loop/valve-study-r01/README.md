# Reusable heart valve cutaway

Use the right-heart section to locate the tricuspid valve between the right atrium and ventricle. Use the left-heart section to locate the mitral valve, then relate its two leaflets to their annulus, chordae and papillary muscles. The [complete circulation schematic](../README.md) supplies ordered flow, outflow, return and distal beds.

The portable export uses the [Cardiac Atlas teaching cutaway](../../../heart/Cardiac_Atlas/docs/README.md) in its assembled reference end-diastolic pose. The two close-ups hide obstructing vessels and semilunar valves. The preserved aorta, pulmonary trunk, pulmonary arteries, caval return and pulmonary venous return remain distinct groups. The original LV septal contrast region is available as a selectable portion of the wall surface. Chamber spaces are visible around their cut rims.

In Blender, expand the units root and select the **Mitral apparatus** group and its descendants. Keep the parent units root when reusing the group in another scene. The 25 meshes include one annulus, two separate leaflets, 20 chordae and two papillary muscle volumes. The portable GLB keeps assembled positions. The separate comparison plate lifts each leaflet by 12 mm and separates them laterally by 5 mm each. This illustration leaves the chordae and annulus seated for orientation and has no motion interpretation.

## Sources and scope

The build pins the published repository copy of the static procedural Atlas GLB. It preserves the original vertex positions, normals, texture coordinates, triangle indices, parts and metre conversion. Named matte materials distinguish fibrous valve structures, chamber surfaces and major vessel groups. The tissue colors are illustrative. The [University of Minnesota Valve Nomenclature atlas](https://www.vhlab.umn.edu/atlas/anatomy-tutorial/cardiac-valve-nomenclature.shtml) supports the valve and supporting apparatus relationships. Retain the Atlas provenance. The source documentation supplies no standalone redistribution grant.

Blender uses +X patient left, +Y posterior, +Z superior. The portable asset uses +X patient left, +Y superior, +Z anterior in metres, from the unchanged 0.025 m/BU root. The reference origin belongs to the procedural Atlas. The same-case s1233 overview has a separate frame. Modelled vessel and chamber interfaces retain the Atlas's visible overlaps, open ends and gaps. The cutaways do not establish patent lumens or specialist approval.

## Replay

From the repository root with Blender 5.2.3 and the pinned source hydrated:

```sh
package=assemblies/cardiovascular-loop/valve-study-r01
study=.artifacts/valve-study-replay
python3.12 "$package/build.py" --output "$study/build"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P "$package/replay.py" -- "$study"
python3.12 "$package/check.py" "$study"
```

Replay yields the editable `build/heart-valve-cutaway.blend`, the static `build/heart-valve-cutaway.glb` and three local image receipts. The source-palette and displaced GLBs are comparison intermediates. [Review and exact evidence](../../../reviews/cardiovascular-loop/valve-study-r01/README.md)
