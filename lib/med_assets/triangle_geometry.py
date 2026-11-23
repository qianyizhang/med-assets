"""Triangle ordering, topology and face-orientation guards for mesh contraction."""

import numpy as np


def edges(faces):
    directed = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    return np.unique(np.sort(directed, axis=1), axis=0, return_counts=True)


def oriented(faces):
    start = faces.argmin(axis=1)
    rotated = np.take_along_axis(faces, (start[:, None] + np.arange(3)) % 3, axis=1)
    return rotated[np.lexsort(rotated.T[::-1])]


def neighbors(vertex):
    return {edge.other_vert(vertex) for edge in vertex.link_edges}


def preserves_faces(keep, remove, min_face_cosine):
    for face in remove.link_faces:
        if keep in face.verts:
            continue
        a, b, c = (keep.co if vertex == remove else vertex.co for vertex in face.verts)
        normal = (b - a).cross(c - a)
        if normal.length_squared < 1e-26 or normal.normalized().dot(face.normal) < min_face_cosine:
            return False
    return True
