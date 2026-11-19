"""Compare decoded triangles by corners, allowing GLB accessor/vertex reordering."""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from glb import decode


def snapshot(path):
    document, binary = decode(path.read_bytes())

    def values(index):
        accessor = document['accessors'][index]
        view = document['bufferViews'][accessor['bufferView']]
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        kind = {5126: 'f', 5125: 'I', 5123: 'H'}[accessor['componentType']]
        width = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[accessor['type']]
        item = struct.Struct('<' + kind * width)
        stride = view.get('byteStride', item.size)
        return [item.unpack_from(binary, start + i * stride) for i in range(accessor['count'])]

    meshes = []
    for mesh in document['meshes']:
        primitives = []
        for primitive in mesh['primitives']:
            names = sorted(primitive['attributes'])
            corners = list(zip(*(values(primitive['attributes'][name]) for name in names)))
            indices = [entry[0] for entry in values(primitive['indices'])]
            triangles = []
            for i in range(0, len(indices), 3):
                triangle = tuple(corners[j] for j in indices[i:i+3])
                triangles.append(min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2]))
            primitives.append((names, primitive['material'], sorted(triangles)))
        meshes.append((mesh['name'],primitives))
    return document['scenes'], document['nodes'], document['materials'], meshes


if __name__ == '__main__':
    original, replay = [Path(arg) for arg in sys.argv[1:]]
    if snapshot(original) != snapshot(replay):
        raise ValueError('Replay changed scene, nodes, materials or decoded triangle corners')
    print('Matched scenes, node attributes, materials, triangle positions, normals, UVs and winding.')
