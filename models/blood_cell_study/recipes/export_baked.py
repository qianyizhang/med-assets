"""Export the selection stored in the baked blood-cell source."""

from pathlib import Path
import sys

import bpy

if bpy.app.version != (4, 3, 2):
    raise ValueError("Use Blender 4.3.2 for the exact baked-source replay")

output = Path(sys.argv[sys.argv.index("--") + 1])
bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", use_selection=True,
                         export_extras=True, export_yup=True)
