# Rebuild recipe
Blender 4.3.2, Python3 with Pillow and NumPy (available in build environment). Extract this archive preserving body-3d-assets, body-3d-source and body-3d-delivery siblings. Create body-3d-delivery/{textures,meshes,renders,docs}. First run blender -b --python body-3d-assets/build_collection.py. Then for each script below run blender -b body-3d-delivery/Anatomy_Workshop.blend --python body-3d-assets/SCRIPT.py:
1. refine_and_preview
2. finalize_geometry
3. repair_topology
4. fix_bladder
5. author_clean_sections
6. bake_and_export
7. final_visibility
8. render_release

Run render_normal_proof in a fresh Blender process. Scripts preserve intermediate revision steps so source changes and replaced sections are inspectable. Some intermediate scripts generate obsolete previews; only final 07/08 and release09 onward belong to the approved gallery. Rebuild overwrites output files. The delivered frozen blend/GLBs are the reviewed revision; regenerated images can differ across Blender versions. Manifest editorial release notes are in the root manifest.
