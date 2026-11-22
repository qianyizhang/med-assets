# Medical teaching assets

Current reusable teaching assets, preserved as their original ZIP packages. Updated 2026-10-21.

## Heart
- Cardiac_Atlas_Blender_and_Source.zip: editable animated Blender master, generators and anatomy documentation.
- Cardiac_Atlas_Exported_Meshes.zip: static GLB/STL meshes, geometry data and QA records.
- Cardiac_Atlas_Baked_Textures.zip: actual baked base-color, roughness, OpenGL normal and UV-layout maps.
- synthetic-heart-imaging-examples.zip: generated NIfTI/NRRD/NumPy/raw volumes, illustrations, orientation metadata and generators. Synthetic teaching examples, not patient scans.

Extract the three Cardiac_Atlas packages together, keeping their paths. Keep the imaging package separate: its geometry_spec.json is distinct from the cardiac master.

## Whole-body 2D · v4
whole-body-anatomy-v4-spatial-2026-10-21.zip contains 54 primary SVG parts, 15 variants, 54 overlays and 21 regional views, with manifests, provenance, coordinate mappings and previews.

## Anatomy Workshop 3D · r1
Extract all eight Anatomy_Workshop_r1 packages into one folder. Repeated README, manifest and documentation files are byte-identical. The native Blender file needs all three texture packages alongside it; GLBs embed their textures. Preserve the sibling body-3d-assets, body-3d-source and body-3d-delivery directories in the rebuild package. Do not run rebuild scripts merely to import or view the assets.

This is a thoracoabdominal-focused collection with selected extras, not a complete body atlas. It contains 18 grouped assets and 17 source-derived exterior surfaces. Exported assets are static. Original source mesh JSONs are included; patient CT intensity scans are not.

## Rights and limitations
- 2D v4: Servier Medical Art adaptations use CC BY 4.0. Preserve LICENSE-NOTES.md, artwork-provenance.json, source-relationships.json and license-registry.json. Independent original portions have no newly declared public license.
- 3D r1: source-derived surfaces credit Jakob Wasserthal and TotalSegmentator contributors, University Hospital Basel, TotalSegmentator v2.0.1, under CC BY 4.0. Preserve all notices, full license texts, source receipts and modification records. The separate label-source Apache 2.0 license does not replace CC BY attribution.
- Heart and synthetic imaging: authored geometric teaching assets; no separate public LICENSE file was found in the four packages.
- No blanket license is applied to this collection. These are simplified educational assets, not clinically validated diagnostic, measurement or surgical-planning resources.

Sources: https://zenodo.org/records/10047263 and https://creativecommons.org/licenses/by/4.0/ . Per-asset references and rights are retained inside the packages.

## Integrity
SHA256SUMS.txt records the SHA-256 of each ZIP. These checksums validate file integrity, not clinical accuracy.

## Packages
- Anatomy_Workshop_r1_GLB_Abdomen_Urinary.zip — 15,604,260 bytes
- Anatomy_Workshop_r1_GLB_Brain_Detailed_Heart.zip — 10,596,360 bytes
- Anatomy_Workshop_r1_GLB_Thorax.zip — 12,765,838 bytes
- Anatomy_Workshop_r1_Native.zip — 17,446,884 bytes
- Anatomy_Workshop_r1_Rebuild_and_Originals.zip — 6,208,513 bytes
- Anatomy_Workshop_r1_Textures_Abdomen_Urinary.zip — 13,554,275 bytes
- Anatomy_Workshop_r1_Textures_Brain_Detailed_Heart.zip — 3,550,745 bytes
- Anatomy_Workshop_r1_Textures_Thorax.zip — 10,093,092 bytes
- Cardiac_Atlas_Baked_Textures.zip — 7,040,265 bytes
- Cardiac_Atlas_Blender_and_Source.zip — 17,857,469 bytes
- Cardiac_Atlas_Exported_Meshes.zip — 19,277,448 bytes
- synthetic-heart-imaging-examples.zip — 9,694,994 bytes
- whole-body-anatomy-v4-spatial-2026-10-21.zip — 20,895,654 bytes
