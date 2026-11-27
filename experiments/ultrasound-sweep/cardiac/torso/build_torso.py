"""Pack the native BP3D chest surfaces used in cardiac probe positioning."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from display_body import load_body_atlas, primitive_stream
from prepare_scenes import mesh_bytes

# glTF in millimetres: +X patient left, +Y cranial, +Z anterior. Keep the same
# native frame for the envelope, cartilage, bone and all surface intersections.
def mesh(doc, binary, node):
    primitive = doc['meshes'][node['mesh']]['primitives'][0]
    vertices = 1000 * primitive_stream(doc, binary, primitive['attributes']['POSITION']).reshape(-1, 3)
    faces = primitive_stream(doc, binary, primitive['indices']).reshape(-1, 3)
    return vertices, faces


def cluster(vertices, faces, cell):
    # Project each active cell to its mean source position. Keep original triangle
    # winding and connectivity; discard collapsed faces and unreferenced vertices.
    used, remap = np.unique(faces, return_inverse=True)
    vertices = vertices[used].astype(float)
    faces = remap.reshape(-1, 3)
    _, groups = np.unique(np.floor(vertices / cell).astype(np.int32), axis=0, return_inverse=True)
    counts = np.bincount(groups)
    means = np.column_stack([np.bincount(groups, weights=values) / counts for values in vertices.T])
    faces = groups[faces]
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    used, remap = np.unique(faces, return_inverse=True)
    return means[used], remap.reshape(-1, 3)


def export(destination):
    source = load_body_atlas()
    records = {'sourceSkin': {'path': source.skin.path, 'sha256': source.skin.sha256},
               'sourceSkeleton': {'path': source.skeleton.path, 'sha256': source.skeleton.sha256}}
    def save(name, vertices, faces):
        raw = mesh_bytes(vertices, faces)
        (destination / (name + '.raw')).write_bytes(raw)
        records[name] = {'vertices': len(vertices), 'triangles': len(faces),
                         'sha256': hashlib.sha256(raw).hexdigest()}

    skin, binary = source.skin.document, source.skin.binary
    source_v, source_f = mesh(skin, binary, skin['nodes'][0])
    upper_body = source_f[source_v[source_f, 1].max(axis=1) > 950]
    # The original includes a thin inner skin surface. Clustering adjacent
    # inner and outer vertices would merge opposing normals on the chest.
    used, remap = np.unique(upper_body, return_inverse=True)
    skin_v, skin_f = source_v[used], remap.reshape(-1, 3)
    save('skin', skin_v, skin_f)
    skeleton, binary = source.skeleton.document, source.skeleton.binary
    for group, endings in [('bones', (' rib', ' clavicle', ' sternum')), ('cartilage', (' costal cartilage',))]:
        pieces = [mesh(skeleton, binary, node) for node in skeleton['nodes']
                  if node.get('name', '').endswith(endings)]
        if not pieces:
            raise ValueError(f'No {group} surfaces')
        vertices, faces, offset = [], [], 0
        for v, f in pieces:
            vertices.append(v)
            faces.append(f + offset)
            offset += len(v)
        merged_v, merged_f = np.concatenate(vertices), np.concatenate(faces)
        v, f = cluster(merged_v, merged_f, 2.8)
        save(group, v, f)

    (destination / 'geometry.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    target = parser.parse_args().output
    target.mkdir(parents=True, exist_ok=True)
    export(target)
