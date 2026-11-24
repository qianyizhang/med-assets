"""Complete the open HRA papillary surface for the focused breast study."""

from dataclasses import replace

import numpy as np
from scipy import ndimage as nd
from scipy.sparse import coo_array
from scipy.sparse.csgraph import connected_components

from breast_anatomy import boundary_edges, concatenate, select_faces
from breast_echo import septal_echo


def closed_papilla(mesh):
    """Keep the native anterior cap and loft its rim into a shallow basal surface."""
    vertices, faces = mesh
    right = np.all(vertices[faces, 0] > 0, axis=1)
    skin, triangles = select_faces(vertices, faces, right)
    skin, weld = np.unique(skin, axis=0, return_inverse=True)
    triangles = weld[triangles]
    graph = coo_array((np.ones(triangles.size), (triangles.ravel(), triangles[:, [1, 2, 0]].ravel())),
                      shape=(len(skin), len(skin)))
    count, groups = connected_components(graph, directed=False)
    if count != 2:
        raise ValueError('Expected the two open sheets of the pinned right HRA nipple')
    outer = groups[np.argmax(skin[:, 1])]
    cap, triangles = select_faces(skin, triangles, groups[triangles[:, 0]] == outer)
    edges = boundary_edges(triangles)
    successor = dict(edges.tolist())
    rim = [int(edges[0, 0])]
    while successor and rim[-1] in successor:
        rim.append(successor.pop(rim[-1]))
    if successor or rim.pop() != rim[0] or len(rim) != len(edges):
        raise ValueError('Expected one simple boundary on the anterior nipple sheet')
    ring = cap[rim]
    center = ring.mean(axis=0)
    radii = ring - center
    normal = np.linalg.svd(radii, full_matrices=False)[2][-1]
    if normal[1] < 0:
        normal = -normal
    # The atlas bounds the external width. Use this width to size the
    # illustrative fibromuscular base, tapering smoothly toward the ducts.
    depth = .92 * np.sqrt(np.mean(np.sum(radii**2, axis=1)))
    vertices_out = [cap]
    faces_out = [triangles]
    prev = np.array(rim)
    offset = len(cap)
    for angle in np.linspace(0, np.pi / 2, 13)[1:-1]:
        vertices_out.append(center + np.cos(angle) * radii - np.sin(angle) * depth * normal)
        curr = offset + np.arange(len(rim))
        faces_out.extend((np.stack((np.roll(prev, -1), prev, curr), axis=1),
                          np.stack((np.roll(prev, -1), curr, np.roll(curr, -1)), axis=1)))
        offset += len(rim)
        prev = curr
    vertices_out.append((center - depth * normal)[None, :])
    faces_out.append(np.stack((np.roll(prev, -1), prev, np.full(len(rim), offset)), axis=1))
    solid = np.concatenate(vertices_out), np.concatenate(faces_out)
    if len(boundary_edges(solid[1])):
        raise ValueError('Focused nipple volume has an open boundary')
    return concatenate([solid, select_faces(vertices, faces, ~right)])


def focused_anatomy(anatomy):
    mesh = closed_papilla(anatomy.meshes['nipple'])
    return replace(anatomy, meshes={**anatomy.meshes, 'nipple': mesh},
                   receipt={**anatomy.receipt, 'nippleVolume': (
                       'The native anterior right papillary sheet defines the exposed contour. '
                       'Its exact rim bounds a modeled fibromuscular base. Duct meshes retain their atlas coordinates.')})


def nipple_echo(brightness, interfaces, labels, fine, broad, depth, xyz):
    """Give the closed papilla a tissue return and a posterior interface along its own contour."""
    pitch = depth[1] - depth[0]
    tissue = nd.gaussian_filter(labels['nipple'].astype(float), (.18 / pitch, .28 / pitch))
    duct = labels['lactiferous_ducts']
    lumen = nd.gaussian_filter(duct.astype(float), .16 / pitch)
    # The atlas specifies the duct envelope. Model partial-volume return from
    # its boundary so an oblique wall does not appear as a solid black bar.
    interior = nd.distance_transform_edt(duct) * pitch
    wall_echo = np.exp(-.5 * ((interior - .14) / .24) ** 2)
    duct_echo = (18 + 14 * fine) + (53 + 20 * broad) * wall_echo
    fat = nd.gaussian_filter(labels['breast_fat'].astype(float), .16 / pitch)
    brightness = brightness * (1 - .46 * fat) + (96 + 40 * fine) * fat * (1 - lumen) * septal_echo(xyz, broad)
    brightness = brightness * (1 - lumen) + duct_echo * lumen
    stroma = (53 + 48 * fine + 21 * broad) * (1 - .79 * lumen)
    brightness = (1 - tissue) * brightness + tissue * stroma
    basal = np.maximum(-np.gradient(tissue, axis=0), 0)
    return brightness, interfaces + 108 * (.23 / pitch) * basal


def nipple_shadow(mask, depth):
    """Attenuate through papillary tissue and increase dropout along its refracting margins."""
    pitch = depth[1] - depth[0]
    thickness = nd.gaussian_filter(np.cumsum(mask, axis=0).astype(float) * pitch,
                                   (.24 / pitch, .48 / pitch))
    edge = np.abs(np.gradient(thickness, pitch, axis=1))
    return np.exp(-.034 * thickness - .53 * np.minimum(edge, 2.3))
