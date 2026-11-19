"""Soften voxel steps while holding neighboring source surfaces in place."""

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

# Half a source voxel. Smoothing moves points; it cannot edit the face graph.
MAX_SHIFT_METRES = 0.00075
PASSES = 8


def mesh_graph(vertices, faces):
    first = faces.ravel()
    second = np.roll(faces, -1, axis=1).ravel()
    rows, cols = np.r_[first, second], np.r_[second, first]
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(vertices),) * 2).tocsr()
    graph.data.fill(1)
    max_edge = np.linalg.norm(vertices[first] - vertices[second], axis=1).max()
    return graph, max_edge


def guard_vertices(vertices, tree, distance):
    nearest, _ = tree.query(vertices, distance_upper_bound=distance + MAX_SHIFT_METRES)
    return np.clip((nearest - distance) / MAX_SHIFT_METRES, 0, 1)


def face_normals(vertices, faces):
    first, second, third = vertices[faces].transpose(1, 0, 2)
    return np.cross(second - first, third - first)


def polish(vertices, faces, graph, weight):
    average = diags(1 / np.asarray(graph.sum(axis=1)).ravel()) @ graph
    original_normals = face_normals(vertices, faces)
    minimum_alignment = 0.1 * np.einsum("ij,ij->i", original_normals, original_normals)
    # A constrained pass can create a pinched triangle at the edge of a guard.
    # Keep those triangles fixed and recompute from the original surface.
    for _ in range(len(vertices)):
        candidate = vertices.copy()
        for _ in range(PASSES):
            for gain in (0.5, -0.53):
                proposed = candidate + gain * weight[:, None] * (average @ candidate - candidate)
                delta = proposed - vertices
                length = np.linalg.norm(delta, axis=1, keepdims=True)
                candidate = vertices + delta * (MAX_SHIFT_METRES / np.maximum(length, MAX_SHIFT_METRES))
        alignment = np.einsum("ij,ij->i", original_normals, face_normals(candidate, faces))
        unsafe = alignment < minimum_alignment
        if not np.any(unsafe):
            return candidate
        weight[faces[unsafe]] = 0
    raise ValueError("Surface smoothing could not preserve triangle orientations")


def refine_overviews(meshes, assemblies):
    graphs = {label: mesh_graph(vertices, faces) for label, (vertices, faces) in meshes.items()}
    trees = {label: cKDTree(vertices) for label, (vertices, _) in meshes.items()}
    results = {}
    for assembly in assemblies.values():
        for label in assembly["parts"]:
            vertices, faces = meshes[label]
            graph, max_edge = graphs[label]
            weight = np.ones(len(vertices))
            # If two swept triangles could intersect, every pair of their
            # original corners is within the sum of their longest edges and
            # both movement caps. By holding those corners still, the pass
            # preserves their original intersection or separation.
            for neighbor in assembly["parts"].keys() - {label}:
                distance = max_edge + graphs[neighbor][1] + 2 * MAX_SHIFT_METRES
                weight = np.minimum(weight, guard_vertices(vertices, trees[neighbor], distance))
            component_count, membership = connected_components(graph, directed=False)
            components = [np.flatnonzero(membership == index) for index in range(component_count)]
            for component in components:
                if len(component) <= 32:
                    weight[component] = 0
                if component_count > 1:
                    others = cKDTree(vertices[membership != membership[component[0]]])
                    distance = 2 * (max_edge + MAX_SHIFT_METRES)
                    weight[component] = np.minimum(
                        weight[component], guard_vertices(vertices[component], others, distance),
                    )
            protected = int(np.count_nonzero(weight == 0))
            updated = polish(vertices, faces, graph, weight)
            displacement = np.linalg.norm(updated - vertices, axis=1) * 1000
            evidence = {
                "sourceSurfaceComponents": component_count,
                "vertices": len(vertices),
                "protectedVertices": protected,
                "orientationGuardVertices": int(np.count_nonzero(weight == 0)) - protected,
                "maxDisplacementMm": round(float(displacement.max()), 6),
                "p95DisplacementMm": round(float(np.percentile(displacement, 95)), 6),
                "rmsDisplacementMm": round(float(np.sqrt(np.mean(displacement**2))), 6),
            }
            results[label] = updated, evidence
    return results
