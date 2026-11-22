import bpy
from pathlib import Path
package = Path(__file__).resolve().parents[1]
D = package / 'body-3d-delivery'
# A rebuilt scene has its own textures. The frozen scene uses the package root.
textures = D / 'textures'
if Path(bpy.data.filepath).resolve() == package / 'Anatomy_Workshop.blend':
    textures = package / 'textures'
if textures == package / 'textures' and any(
    image.source == 'FILE' and ' 1K' in image.name and not (textures / Path(image.filepath).name).is_file()
    for image in bpy.data.images
):
    from runpy import run_path
    run_path(str(package.parents[1] / 'tools/restore_textures.py'))['restore']('workshop')
for im in bpy.data.images:
 if im.source=='FILE' and ' 1K' in im.name:
  original=Path(im.filepath).name
  if (textures/original).is_file():
   if im.packed_file:im.unpack(method='REMOVE')
   im.filepath=bpy.path.relpath(str(textures/original))
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop_External_Textures.blend'),compress=True)
