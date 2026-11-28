"""Apply Blender's curvature-sensitive quadric collapse and pack the retained surface."""

import struct
import sys
from pathlib import Path

import bpy
import numpy as np

TRIANGLES = 5900


def main():
    source, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with np.load(source, allow_pickle=False) as mesh:
        vertices, faces, affine = mesh["vertices"], mesh["faces"], mesh["affine"]
    center = vertices.mean(0)
    data = bpy.data.meshes.new("Thyroid gland")
    data.from_pydata(vertices - center, [], faces)
    data.update()
    obj = bpy.data.objects.new("Thyroid gland", data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Surface reduction", "DECIMATE")
    modifier.ratio = TRIANGLES / len(faces)
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    data = obj.data
    data.calc_loop_triangles()
    positions = np.empty(len(data.vertices) * 3, dtype=np.float32)
    data.vertices.foreach_get("co", positions)
    inverse = np.linalg.inv(affine)
    voxel = (positions.reshape(-1, 3) + center) @ inverse[:3, :3].T + inverse[:3, 3]
    indices = np.empty(len(data.loop_triangles) * 3, dtype=np.int32)
    data.loop_triangles.foreach_get("vertices", indices)
    with output.open("xb") as stream:
        stream.write(struct.pack("<2I", len(voxel), len(indices) // 3))
        stream.write(voxel.astype("<f4").tobytes())
        stream.write(indices.astype("<u4").tobytes())


if __name__ == "__main__":
    main()
