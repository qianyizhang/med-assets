# Terminal airspace study

Trace air from the last conducting bronchiole through the respiratory bronchiole into the alveolar duct and distal common airspace. The enlarged longitudinal cutaway shows where alveolar recesses open into the central passage and where adjacent recesses share a septum.

The standalone [GLB](terminal-airspaces.glb) has four named, selectable tissue regions. The near wall is cut away to expose their shared lumen. The terminal bronchiole starts with a bare lumen. Two shallow pockets mark the transition to the respiratory bronchiole. Six deeper pockets open from the duct and three open into the far common space. The section edge is pale peach, the conducting airway warm ivory and the alveolar surfaces muted terracotta.

## Basis and scale

The [One Breath airway route](../airway-r01/README.md) preserves the full teaching sequence. Its terminal view displays five cups receiving capped connectors. The separate cutaway lets the gallery show openings through the wall, a continuous lumen and shared septa. The comparison imports the pinned original GLB and displays its 11 terminal meshes.

The conducting-to-respiratory sequence, airway openings and common airspace follow [OpenStax Anatomy and Physiology 2e §22.1, Respiratory Zone](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system). Branch counts, mouth shape, septal thickness, cutaway and proportions are authored. The pockets share the illustrated lumen. Tiny direct pores through the septa, vessels, respiratory membrane layers and motion are outside this study. The model occupies approximately 43 × 14 × 23 display millimetres near the original inset, without patient registration or anatomical scale calibration. The GLB uses metres with Blender +Z up converted to glTF +Y. [One Breath source credit and licenses](../licenses/ATTRIBUTION.md) apply to the original comparison. The updated geometry uses no source meshes or reference artwork.

## Replay

Use Blender 5.2.3 from the repository root. Supply a fresh output directory. The build exports the GLB, editable scene and airspace check targets. The comparison produces both clean-import pairs, the render receipt and mesh metrics. On the Mac, run Blender outside the agent command sandbox with the required approval.

```sh
owner=lessons/one-breath/terminal-study-r02
out=.artifacts/terminal-study-replay
blender -b -t 2 --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/build.py" -- "$out"
blender -b -t 3 --factory-startup --disable-autoexec --python-exit-code 1 -P "$owner/compare.py" -- "$out"
cmp "$owner/terminal-airspaces.glb" "$out/terminal-airspaces.glb"
```

Use `--check-only` after the output path to skip rendering. The delivered GLB SHA-256 is `77f19cc2b261b6d11413c8bb78c949ab8d9c78091f33c47a3dc82a9543781158`.

## Verification

Blender 5.2.3 reproduced the GLB and airspace targets byte for byte and reproduced the geometry metrics. On clean import all four selectable parts rejoined after a 40 nm weld in display coordinates. The joined tissue is one component with zero nonmanifold or inconsistently wound edges. Eight centerline spans and eleven spans from the lumen to 90% of pocket depth cleared the tissue. A missing target caused the check to fail without writing metrics. The build rejected an existing output directory.

Both pairs use one 0.058405 m orthographic scale, identical camera poses within each pair, the same three-light studio, AgX and a transparent background. The original is a fresh render with native materials. The earlier gallery plate assigned a brighter display palette to the same original objects. In grayscale, the open channel, early pockets, common space and shared septa can be traced by the section edge and shading. The frontal view partly occludes some upper and lower mouths, which are clearer in the iso view. The [gallery review](../../../reviews/body-systems/2026-11-20-surface-quality/README.md) includes the local WebGL part-visibility and reset checks. Specialist review remains open.

| Mesh selection | Triangles | glTF primitives | Per-node welded components |
|---|---:|---:|---:|
| Original cups, each of five | 862 | 1 | 1 |
| Original duct connectors, each of four | 308 | 1 | 1 |
| Original terminal bronchiole | 596 | 1 | 1 |
| Original respiratory bronchiole and duct | 596 | 1 | 1 |
| **Original terminal selection** | **6,734** | **11** | **11** |
| Updated terminal bronchiole | 948 | 3 | 1 |
| Updated respiratory bronchiole | 1,416 | 3 | 1 |
| Updated alveolar duct | 3,792 | 3 | 1 |
| Updated distal common space and alveoli | 2,240 | 3 | 1 |
| **Updated standalone selection** | **8,396** | **12** | **4** |

The delivered mesh adds 24.7% triangles to the original terminal selection for two tissue surfaces, visible section edges and eleven open pocket transitions. A finer same-geometry trial used 14,004 triangles. The chosen sampling uses 40.0% fewer triangles than that trial and keeps 99.89% isometric and 99.86% orthographic silhouette intersection-over-union at 800 × 640 with alpha threshold 128. Both foreground bounding boxes match exactly. Some curved edges show slight faceting at higher zoom. Frame rate was outside this check.
