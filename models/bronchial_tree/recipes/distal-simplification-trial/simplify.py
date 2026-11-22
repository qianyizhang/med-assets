"""Build one constrained simplification of the pinned authored r13 GLB."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
from mathutils import Vector
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from tools.glb import decode, encode

R13 = 'c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587'
WITNESSES = HERE.parent / 'authored-central-fairing-r13' / 'terminal-witnesses.json'
MAX_EDGE = 0.00060
MIN_FACE_COSINE = math.cos(math.radians(22.5))
ROUNDS = 5


def mesh_data(data):
    document, binary = decode(data)
    primitive, = document['meshes'][0]['primitives']
    attrs = primitive['attributes']

    def array(index, width):
        acc = document['accessors'][index]
        view = document['bufferViews'][acc['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[acc['componentType']]
        return np.frombuffer(binary, dtype, acc['count'] * width,
                             view.get('byteOffset', 0)).reshape(-1, width)

    return document, array(attrs['POSITION'], 3), array(attrs['NORMAL'], 3), array(primitive['indices'], 1).reshape(-1, 3)


def protection(positions):
    """Masks are in the canonical Blender frame (meters, Z up)."""
    world = positions[:, [0, 2, 1]] * [1, -1, 1]
    regions = {'central slab': np.abs(world[:, 0]) <= .028}
    neighborhoods = {
        'accepted left lobar': ((.042, .008, .068), .012),
        'right lobar': ((-.042, .008, .033), .012),
    }
    witnesses = json.loads(WITNESSES.read_text())
    if len(witnesses) != 16 or len({row['name'] for row in witnesses}) != 16:
        raise ValueError('Expected 16 distinct r13 terminal witnesses')
    neighborhoods.update({row['name']: (row['authored_recipe_position'], .006) for row in witnesses})
    regions.update({name: np.linalg.norm(world - center, axis=1) < radius
                    for name, (center, radius) in neighborhoods.items()})
    return regions


def safe_collapse(edge, keep, remove):
    # For this closed triangular surface the common neighbors must be exactly
    # the two opposite corners in the incident faces (the edge link condition).
    opposite = {v for face in edge.link_faces for v in face.verts if v not in (keep, remove)}
    keep_neighbors = {e.other_vert(keep) for e in keep.link_edges}
    remove_neighbors = {e.other_vert(remove) for e in remove.link_edges}
    if len(opposite) != 2 or keep_neighbors & remove_neighbors != opposite:
        return False
    for face in remove.link_faces:
        if keep in face.verts:
            continue
        a, b, c = (keep.co if v == remove else v.co for v in face.verts)
        normal = (b - a).cross(c - a)
        if normal.length_squared < 1e-26 or normal.normalized().dot(face.normal) < MIN_FACE_COSINE:
            return False
    return True


def collapse_distal(positions, faces, locked):
    mesh = bmesh.new()
    ids = mesh.verts.layers.int.new('source_vertex')
    vertices = []
    for i, position in enumerate(positions):
        vertex = mesh.verts.new(Vector(position))
        vertex[ids] = i
        vertices.append(vertex)
    for face in faces:
        mesh.faces.new([vertices[i] for i in face])

    counts = []
    for _ in range(ROUNDS):
        mesh.normal_update()
        eligible = []
        for edge in mesh.edges:
            v, w = sorted(edge.verts, key=lambda vert: vert[ids])
            i, j = v[ids], w[ids]
            if locked[i] or locked[j] or not edge.is_manifold:
                continue
            length = edge.calc_length()
            if length <= MAX_EDGE:
                eligible.append((length, i, j, edge, v, w))

        mapping = {}
        occupied = set()
        for _, _, _, edge, v, w in sorted(eligible):
            if v in occupied or w in occupied:
                continue
            keep, remove = v, w
            if not safe_collapse(edge, keep, remove):
                keep, remove = w, v
                if not safe_collapse(edge, keep, remove):
                    continue
            # Keep simultaneous collapses out of one another's vertex stars.
            mapping[remove] = keep
            occupied.update(e.other_vert(remove) for e in remove.link_edges)
            occupied.update(e.other_vert(keep) for e in keep.link_edges)
            occupied.update((keep, remove))
        counts.append(len(mapping))
        bmesh.ops.weld_verts(mesh, targetmap=mapping)
    simplified = np.array([[v[ids] for v in face.verts] for face in mesh.faces])
    mesh.free()
    if len(simplified) != len(faces) - 2 * sum(counts):
        raise ValueError('A collapse removed an unexpected number of faces')
    return oriented(simplified), counts


def oriented(faces):
    first = faces.argmin(axis=1)
    faces = np.take_along_axis(faces, (first[:, None] + np.arange(3)) % 3, axis=1)
    return faces[np.lexsort(faces.T[::-1])]


def compact(document, positions, normals, faces):
    used, indices = np.unique(faces, return_inverse=True)
    pos = positions[used]
    dtype, component = ('<u2', 5123) if len(used) <= 65535 else ('<u4', 5125)
    blobs = (pos.tobytes(), normals[used].tobytes(), indices.astype(dtype).tobytes())
    offset = 0
    for view, blob in zip(document['bufferViews'], blobs, strict=True):
        view.update(byteOffset=offset, byteLength=len(blob))
        offset += len(blob)
    for accessor, count in zip(document['accessors'], (len(used), len(used), faces.size), strict=True):
        accessor['count'] = count
    document['accessors'][0].update(min=pos.min(axis=0).tolist(), max=pos.max(axis=0).tolist())
    document['accessors'][2]['componentType'] = component
    document['buffers'][0]['byteLength'] = offset
    document['asset']['generator'] = 'med-assets AG-GAL-021 distal simplification trial'
    return encode(document, b''.join(blobs))


def build(source, out):
    data = source.read_bytes()
    if len(data) != 10_655_808 or hashlib.sha256(data).hexdigest() != R13:
        raise ValueError('Expected the exact hydrated r13 GLB')
    if out.exists():
        raise FileExistsError(f'Build directory already exists: {out}')
    document, positions, normals, faces = mesh_data(data)
    protected = np.logical_or.reduce(list(protection(positions).values()))
    protected_faces = protected[faces].any(axis=1)
    # Lock the neighbors as well so a face intersecting a witness survives whole.
    locked = protected.copy()
    locked[faces[protected_faces].ravel()] = True
    simplified, counts = collapse_distal(positions, faces, locked)

    candidate = compact(document, positions, normals, simplified)
    out.mkdir()
    (out / 'bronchial_distal_trial.glb').write_bytes(candidate)
    (out / 'build.json').write_text(json.dumps({
        'baselineSha256': R13,
        'candidateSha256': hashlib.sha256(candidate).hexdigest(),
        'candidateBytes': len(candidate),
        'triangles': len(simplified),
        'trianglesRemoved': len(faces) - len(simplified),
        'edgeCollapsesByRound': counts,
        'lockedVertices': int(locked.sum()),
    }, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    build(args.input, args.out)


if __name__ == '__main__':
    main()
