# Z-Anatomy gland source attribution

Downloaded and inspected 2026-10-23 UTC from the original Z-Anatomy project:
- https://github.com/Z-Anatomy/Models-of-human-anatomy
- https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/master/Z-Anatomy.zip
- https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/master/License.txt
- GitHub archive blob SHA: f43cabc6f366b2a6058dd2ed4a2b3c7b9b2492cb (87 MB); SHA256 in provenance.json.

Required project credits preserved:
- BodyParts3D — The Database Center for Life Science — CC-BY-SA 2.1 Japan (historic source attribution used by this derivative).
- Z-Anatomy — The libre 3D atlas of anatomy — CC-BY-SA 4.0.
- Kousaku Okubo (original BodyParts3D model), Gauthier Kervyn (design, 3D, anatomy), Marcin Zielinski (Blender add-on).

Selected gland geometry and derivatives: **CC BY-SA 4.0**, https://creativecommons.org/licenses/by-sa/4.0/. Do not relabel CC BY 4.0 merely because independent BodyParts3D assets now use that license. Retain credit, license link and changes; distribute derived models under the same license.

The original repository lists additional inner-ear and kidney third-party noncommercial exceptions. Neither those models nor their images are selected here. Do not blanket-redistribute the entire source atlas under a single permissive label.

# Extraction / limitations

Startup.blend is a CAD atlas, not a patient scan or clinically validated sample. No downloaded Python scripts, application template, drivers or embedded auto-execution were run. Our local inspection scripts use Blender --disable-autoexec and load only exact named gland/context objects via bpy.data.libraries.load. Existing source Mirror/Solidify/Subdivision modifiers are evaluated, not new authored detail. Exact recorded native object transforms are baked into exported world-coordinate OBJ. No registration to BodyParts3D or prior wholebody assets, no per-organ centering, no invented topology.

World axes observed from source object placement: +X left, -Y anterior, +Z superior; world coordinates near metre dimensions. This remains **Z-Anatomy native space**, not proven identical to current BodyParts3D source space. Source Blender unit settings were not recovered from full scene because memory limit prevented full-scene load. Scale interpretation must be validated against source landmarks before wholebody integration. Exported meshes are unreviewed candidates, not anatomical/visual/runtime passes.

# Alternative investigated

Original TotalSegmentator dataset v2.0.1 at https://zenodo.org/records/10047292 has CC BY 4.0 verified via https://zenodo.org/api/records/10047292 metadata. Public CT-derived thyroid segmentation is an alternative, but would be a separate patient frame with imaging-resolution/pathology limitations; not interchangeable with CAD. No patient CT data downloaded for this research.
