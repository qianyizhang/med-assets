import bpy
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'body-3d-delivery'
for im in bpy.data.images:
 if im.source=='FILE' and ' 1K' in im.name:
  original=Path(im.filepath).name
  if (D/'textures'/original).exists():
   if im.packed_file:im.unpack(method='REMOVE')
   im.filepath='//textures/'+original
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop_External_Textures.blend'),compress=True)
