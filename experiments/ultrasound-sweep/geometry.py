"""Shared physical dimensions and authored transducer sections for the sweep."""

import math

VOXEL_MM = 1.5
LENS_RADIUS_MM = 38
SECTOR_DEPTH_MM = 133
SECTOR_HALF_ANGLE_DEG = 36

# Local +X points along image width, +Z out of the patient. Values are in case voxels.
PROBE_RINGS = {
    'lens': [(-.7, 14, 3, 2.5), (1, 16, 4.4, 3), (3, 16, 4.5, 3)],
    'housing': [(2.6, 16, 4.5, 3), (5, 17, 5, 2.5), (10, 15, 5.7, 1.2),
                (18, 10, 5.2, 0), (30, 7, 4.4, 0), (45, 7.3, 4.8, 0),
                (49, 5, 4, 0), (50, 3.5, 3.1, 0)],
    'relief': [(49, 3.5, 3, 0), (55, 3.3, 2.9, 0), (60, 2, 2, 0)],
}
PIP_POSITION = (-13.8, 0, 11)
PIP_SCALE = (2, 2.1, 2.7)


def probe_geometry(rings):
    """Return the same elliptical sections and closed faces for both renderers."""
    segments = 48
    vertices = []
    faces = []
    for z, width, depth, curvature in rings:
        for i in range(segments):
            a = 2 * math.pi * i / segments
            vertices.append((width * math.cos(a), depth * math.sin(a), z + curvature * math.cos(a) ** 2))
    for j in range(len(rings) - 1):
        for i in range(segments):
            a, b = segments * j + i, segments * j + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.extend([tuple(reversed(range(segments))), tuple(range(len(vertices) - segments, len(vertices)))])
    return vertices, faces
