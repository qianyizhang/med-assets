"""Apply quadric-collapse reduction to the full aorta and each crop."""

import struct
import sys
from pathlib import Path

import bpy
import numpy as np

TARGET = {"aorta": 5990, "aorta-abdomen": 5790, "aorta-screening": 4990}


def weld_packed_points(voxel, faces):
    """Keep the index topology on the actual float32 positions delivered to the viewer."""
    _, first, inverse = np.unique(voxel, axis=0, return_index=True, return_inverse=True)
    if len(first) == len(voxel):
        return voxel, faces
    order = np.argsort(first)
    faces = np.argsort(order)[inverse[faces]]
    distinct = (faces != np.roll(faces, 1, axis=1)).all(axis=1)
    return voxel[first[order]], faces[distinct]


def pack(directory, part):
    with np.load(directory / f"{part}-dense.npz", allow_pickle=False) as source:
        vertices, faces, affine = source["vertices"], source["faces"], source["affine"]
    center = vertices.mean(0)
    data = bpy.data.meshes.new(part)
    data.from_pydata(vertices - center, [], faces)
    data.update()
    obj = bpy.data.objects.new(part, data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Surface reduction", "DECIMATE")
    modifier.ratio = TARGET[part] / len(faces)
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
    voxel, faces = weld_packed_points(voxel.astype("<f4"), indices.reshape(-1, 3))
    with (directory / f"{part}.mesh").open("xb") as stream:
        stream.write(struct.pack("<2I", len(voxel), len(faces)))
        stream.write(voxel.tobytes())
        stream.write(faces.astype("<u4").tobytes())
    bpy.data.objects.remove(obj, do_unlink=True)


if __name__ == "__main__":
    work, *parts = sys.argv[sys.argv.index("--") + 1 :]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name in parts:
        pack(Path(work), name)
