import bpy,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1])
bpy.ops.export_scene.gltf(filepath=str(out),export_format="GLB",use_selection=True,export_extras=True,export_yup=True)
