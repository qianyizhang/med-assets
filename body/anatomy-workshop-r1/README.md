# Anatomy Workshop · 2026-10-21 r1

Reusable educational 3D collection: 18 grouped assets, 17 source-derived exterior meshes, independently authored teaching details, and the existing detailed heart as an optional static alternative.

## Use
Open Anatomy_Workshop.blend in Blender 4.3.2 or later. Select WORKSHOP CONTROL to set material_mode: 0 tissue-style, 1 categorical teaching colors, 2 transparent. cutaway: 0 exterior, 1 supported teaching sections. Individual named meshes remain editable. Source trachea/main-airway and authored bronchial hierarchy are alternative collections: enable one at a time. Source trachea is the default. Likewise, choose one of the two heart alternatives. The native file uses editable procedural materials; portable baked PBR materials are also retained. GLBs embed textures and require no external files. A viewer can use node extras organ_id, anatomy_id, view_role and derivation to isolate parts.

## Actual scope
Liver; paired kidneys with separately authored renal teaching sections; spleen; pancreas with illustrative duct; source stomach exterior and independent mucosal teaching section; gallbladder with illustrative wall/duct; source heart shell; five lung lobes; aorta; trachea with authored C-rings; pulmonary vein; L3 vertebra; five-lobar bronchial hierarchy; bladder with ureters and one urethral outlet; recognition-level brain; independent detailed heart.

This is a thoracoabdominal-focused collection with selected additional structures, not a complete whole-body anatomical atlas. Kidneys and stomach use explicitly authored conceptual sections, not registered cut planes of the segmented source. Gastric inlet/outlet, cardia and pylorus are omitted from the section. Renal pyramids are representative sections embedded in continuous backing; fine nephron anatomy is omitted. Brain folds/tracts and distal airway branches are schematic. Static assets have no physiological animation. The original separate heart project contains heartbeat animation; its GLB here is a static clinical-color version.

## Geometry and coordinates
Immutable source JSONs are RAS millimetres. 17 surfaces use case s1233; the raw-source prostate s1336 is excluded from the assembly. Common conversion to glTF metres: (-R/1000, (S-430)/1000, (A-155)/1000). Axes: +X patient left, +Y superior, +Z anterior. Blender metres: (-R/1000, -(A-155)/1000, (S-430)/1000). Authored additions and the independently authored heart are pedagogically positioned and not scan registered.

Source exteriors underwent tiny-edge cleanup, outward-normal correction, subdivision and smoothing. Four remaining problematic surfaces (heart, liver, lower lung lobes) underwent 1.2 mm voxel remeshing and simplification. All 17 exported source exteriors pass exact-seam-welded boundary/nonmanifold edge and positive-volume checks. This is not a guarantee that all authored details or intersections form a single watertight solid. Relative to raw source, extremal bounds changed approximately 0.31–4.67 mm. REPAIR_QA nearest-surface distances compare only remesh output with the already-smoothed derivative, not with the original segmentation.

## UVs and textures
17 new groups have a single exported shared Teaching UV atlas and actual 1024×1024 BaseColor, Roughness and OpenGL (+Y) tangent-space Normal maps. Base color is sRGB; roughness and normals are non-color/linear data. Maps are baked from artistic organ-specific procedural materials, not photographs, histology or recovered scan texture. Normal relief is intentionally subtle; see controlled normal-on/off proof. UV atlases include all display variants, so some atlas regions belong to hidden section geometry. Two negligible brain triangles have near-zero UV area; renal and gastric replacements have none. Clinical and transparent modes are material presets, not three separate photographic texture sets.

## Rights and provenance
Source-derived surfaces: Jakob Wasserthal and TotalSegmentator contributors, University Hospital Basel, TotalSegmentator v2.0.1, https://zenodo.org/records/10047263, CC BY 4.0. Source tb3 revision 75ec4e6530abe4d434b07958e90bdc9dec062bef. Retain docs/licenses/NOTICE.md and full licenses, source/version attribution and this modification record in reuse. Raw JSONs are unmodified. The retained label-source license is Apache 2.0; it does not replace the dataset's CC BY 4.0 attribution. No source endorsement is implied.

Educational inspiration and tutorial assets only. Not clinically validated, patient-specific diagnosis, scanner simulation or surgical planning geometry.
