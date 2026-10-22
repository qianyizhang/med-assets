# Cardiac Atlas
## An editable beating-heart teaching model

This is a procedural, anatomically informed educational model. It is not patient-derived, clinically validated, a surgical planning model, a biomechanical simulation, or a diagnostic imaging phantom. Its scale, wall thicknesses, chamber volumes, leaflet motion and timing are illustrative. Do not infer normal ranges, ejection fraction, disease or treatment decisions from it.

### Open and use
1. Open `Cardiac_Atlas.blend` in Blender 4.3 or later.
2. Select **HEART CONTROL • material + cutaway + pulse**, in **00 CONTROLS**.
3. In Object Properties → Custom Properties, change:
   - **material_set**: 0 tissue-style; 1 clinical circulation colors; 2 transparent educational shells
   - **cutaway**: 0 exterior; 1 anterior teaching sections
   - **show_pericardium**: show the simplified removable pericardial envelope
4. Press Space to play. The scene runs at 30 fps and 75 illustrative beats/minute. Frames 1–24 form one cycle; the rig repeats it. Frame 1 is the registered end-diastolic reference.
5. Choose one of the four named cameras for anterior, cutaway, posterior or valve-apparatus views. Anatomical structures are separate, editable meshes organized in named collections.

### What “rigged” means here
The deformable myocardium uses editable shape keys, driven by one central control object. Ventricular shortening and subtle torsion follow ventricular systole; atria contract earlier. Separate AV and semilunar leaflet opening shape keys follow an illustrative cardiac cycle. Chordal endpoints track leaflet opening/closure. This is a deformation rig, not a skeletal armature. It does not simulate pressure, stress, flow, electrical conduction or fluid–structure interaction.

### Material sets
- **Tissue-style:** self-contained procedural mottling, fine bump, wet-surface coat and modest subsurface shading. This is an illustrative realistic-style material, not photographic tissue, a scan-derived texture or a claim of photorealistic accuracy.
- **Clinical:** red/blue circulation categories, ivory fibrous valves/chordae and amber septal muscle. Blue represents lower oxygenation schematically; venous blood is not blue. These are teaching colors, not a universal clinical coding standard.
- **Transparent:** a deliberately nonphysical educational view through the cardiac walls. Transparency and tint do not represent X-ray attenuation, MR signal or ultrasound acoustic properties.

All three material networks are embedded in the `.blend`; no image-texture downloads are required. Generic mesh exports use simpler display materials. The native `.blend` is the authoritative animated/material deliverable.

### Anatomy coverage
- Four separate chamber walls and closed reference blood-pool volumes: LA, RA, LV, RV
- LV-dominant apex and an anterior/right crescent-shaped RV wrapping the LV
- Distinct curved interventricular muscular partition and interatrial septum; representative fossa ovalis
- Mitral valve with two leaflets, tricuspid with three, and three cusps each for aortic and pulmonary valves
- AV chordae and representative papillary muscle groups; no chordae on semilunar valves
- Wall-attached ventricular trabecular ridges, right ventricular moderator band, right atrial pectinate ridges
- Endocardial, myocardial and epicardial surfaces/material regions; removable simplified parietal pericardial envelope
- Aortic root, ascending aorta, arch, descending segment; brachiocephalic trunk and its branches, left common carotid and left subclavian
- Pulmonary trunk and right/left pulmonary arteries
- Superior/inferior vena cavae and four representative pulmonary veins
- Representative right-dominant coronary pattern: left main, LAD, circumflex, RCA, right marginal and posterior descending arteries; great/middle/small cardiac veins and coronary sinus
- Atrial appendages and localized epicardial fat

### Important anatomical simplifications
This is a pedagogical construction from continuous analytic shapes and hand-authored vessel paths. It is not a segmented clinical scan. Chamber, vessel and valve junctions are idealized; several adjoining structures overlap geometrically rather than forming one surgically accurate, fully connected lumen. Reference label volumes apply explicit blood-pool priority at overlaps. Branch vessels are individually editable tube-wall meshes, not a single Boolean-unioned vascular tree. The major chamber pools are closed for voxelization; presentation cutaways are separate objects.

The annular/leaflet shapes, chordal branching, papillary origins and trabecular patterns are representative rather than exhaustive. Tiny vessels, valves of coronary sinus/IVC, all pericardial recesses and reflections, microvascular anatomy, a detailed conduction system, nerves, lymphatics, exact cardiac fibrous skeleton, histology and individual variants are omitted or simplified. The pericardial sac does not reproduce all attachments or detailed fibrous/serous layer anatomy. Epicardium represents the visceral serous pericardium; it is not an additional thick muscular wall.

Cutaway views intentionally remove anterior tissue and may hide the great vessels, coronary overlay, epicardial fat and appendages to expose chambers and valves. They are teaching sections, not exact echocardiographic or diagnostic scan planes. The registered imaging viewer provides explicit, separate slice planes for model–volume correspondence.

### Registration and units
Blender coordinates: +X patient left, +Y posterior, +Z superior. One Blender unit = 25 mm (`scale_length = 0.025`).

RAS millimetres = **(-25X, -25Y, +25Z)**. The origin is an arbitrary model origin near the ventricular base, not a patient reference. The affine and label definitions are in `geometry_spec.json`. Exact chamber occupancy and reference-surface functions are in `heart_geometry.py`; lumen centerline samples are in `vessel_geometry.json`.

`exports/anatomy_meshes.json` holds closed reference ED chamber wall/pool meshes and septa. `exports/anatomy_details.json` holds static ED detail meshes without duplicate main wall/pool objects. Detail objects with label 0 are not resolved in the synthetic imaging volume. Do not imply that every chord or trabecula is visible in the illustrative images.

### Reproduce
Run Blender in background mode:

    blender -b --python build_heart.py

Then run the supplied finalization/render and export scripts as needed. The generation source is also embedded as Blender text blocks. The scene uses only native Blender geometry and procedural nodes; no paid/downloaded anatomical asset or external texture is required. Rendered previews are genuine Blender scene renders.

### Anatomy references
- University of Minnesota, Visible Heart Laboratories: [attitudinally correct anatomy](https://www.vhlab.umn.edu/atlas/anatomy-tutorial/attitudinally-correct-anatomy.shtml), [anterior external anatomy](https://www.vhlab.umn.edu/atlas/external-images/anterior/), [valve nomenclature](https://www.vhlab.umn.edu/atlas/anatomy-tutorial/cardiac-valve-nomenclature.shtml), [coronary anatomy](https://www.vhlab.umn.edu/atlas/coronary-system-tutorial/what-is-the-coronary-system.shtml), [coronary veins](https://www.vhlab.umn.edu/atlas/coronary-system-tutorial/coronary-venous-anatomy.shtml)
- OpenStax, Anatomy and Physiology 2e: [heart anatomy](https://openstax.org/books/anatomy-and-physiology-2e/pages/19-1-heart-anatomy), [cardiac cycle](https://openstax.org/books/anatomy-and-physiology-2e/pages/19-3-cardiac-cycle)

These sources inform the organization and teaching relationships. They do not validate the generated geometry.

### Actual UV and baked texture deliverables
The four major chamber walls have an additional shared **Baked tissue atlas** UV layer. A real Blender Cycles bake supplies 2048×2048 base-color, roughness and tangent-space normal PNGs in `textures/`. The normal map uses the OpenGL +Y convention; use Non-Color/linear data for normal and roughness, sRGB for color. The normal detail is subtle surface microrelief, not a geometry displacement map. The atlas also includes the inner endocardial surfaces. `textures/UV_QA.json` verifies zero UV-coordinate transfer error between the atlas mesh and the original four separate wall meshes.

The optional **11 TEXTURE PIPELINE STUDY** collection and `Cardiac_Walls_Baked_PBR_ED.glb` demonstrate the actual textures on a standard PBR mesh. That study mesh coincides with the original chamber walls: hide the original walls before displaying it. The complete animated model retains its self-contained procedural shader network so all three presets and cutaway surfaces remain available. Fine structures are not baked into the wall atlas. `renders/09_texture_pipeline.png` shows the actual UV layout and map files.

To reproduce the expanded deliverable, run `build_heart.py`, then `finalize_and_render.py`, `bake_tissue_atlas.py`, `post_bake_finalize.py`, `export_details.py`, `export_meshes.py`, and `prepare_portable_exports.py` in that order. The last script adds explicit metre conversion to GLB scene roots and writes RAS-mm STLs. Run `fix_continuous_controls.py` to verify continuous floating-point control tracks, then `render_animation.py` and `compose_animation.py` to render all 24 native frames per 0.8-second cycle and create the 30 fps movie. Each Blender postprocessing script should be invoked with `blender -b Cardiac_Atlas.blend --python SCRIPT.py`. Run `prepare_portable_exports.py` and `compose_animation.py` with ordinary Python 3 (NumPy/Pillow; FFmpeg for video). Scripts resolve their data root from their own location. Blender baking/plate scripts also use Pillow.

The delivered file opens without running any script. Regeneration was tested on Linux with Blender 4.3.2, Python 3, NumPy, Pillow and FFmpeg. Image-plate scripts use system DejaVu Sans fonts; adjust their font-file constants on platforms where those paths differ. The atlas is 8-bit PNG with subtle microrelief; `renders/11_normal_map_verification.png` and `textures/Normal_QA.json` show the measured map variation and same-light normal-on/off check.
