"""Separate overlapping atlas daughter tubes for the teaching bifurcation.

The native CCA, branch origins, radii and upper courses are retained. The two
daughter centers are displaced equally in opposite directions only where the
source walls overlap. A short smooth transition preserves a common bulb.
"""

import numpy as np
from scipy import ndimage


def section_points(vertices, edges, level):
    a, b = vertices[edges[:, 0]], vertices[edges[:, 1]]
    crosses = (a[:, 2] <= level) != (b[:, 2] <= level)
    a, b = a[crosses], b[crosses]
    t = (level - a[:, 2]) / (b[:, 2] - a[:, 2])
    return a + t[:, None] * (b - a)


def separate_daughters(meshes, paths):
    names = ('ica', 'eca')
    lines = [paths[key] for key in names]
    fork = paths['cca'][-1]
    if any(np.linalg.norm(line[0] - fork) > .15 for line in lines):
        raise ValueError('Unmatched source bifurcation')
    levels = np.arange(fork[2], fork[2] + 61, .25)
    centers = []
    cuts = []
    for name, line in zip(names, lines, strict=True):
        # The upper carotid canal turns back; use the ascending cervical course.
        cervical = line[:np.argmax(line[:, 2] >= levels[-1]) + 1]
        if len(cervical) < 3 or np.any(np.diff(cervical[:, 2]) <= 0):
            raise ValueError('Missing ascending cervical centerline')
        centers.append(np.column_stack([np.interp(levels, cervical[:, 2], xyz) for xyz in cervical.T[:2]]))
        v, f = meshes[name]
        edges = np.unique(np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1), axis=0)
        cuts.append([section_points(v, edges, z)[:, :2] for z in levels])

    direction = centers[1] - centers[0]
    near_origin = levels < fork[2] + 3
    direction[near_origin] = direction[np.flatnonzero(~near_origin)[0]]
    direction /= np.linalg.norm(direction, axis=1)[:, None]
    overlap = np.zeros(len(levels))
    for i, axis in enumerate(direction):
        if len(cuts[0][i]) and len(cuts[1][i]):
            # Clearance is along the native separation direction in each RAS
            # axial plane. A nonpositive value means the envelopes are separate.
            overlap[i] = max(0., np.max(cuts[0][i] @ axis) - np.min(cuts[1][i] @ axis) + .65)
    t = np.clip((levels - fork[2]) / 9., 0., 1.)
    ramp = t * t * (3 - 2*t)
    shift = .5 * ndimage.gaussian_filter1d(overlap, 3.) * ramp
    if shift.max() > 4 or shift[-1] > .01:
        raise ValueError('Proximal branch correction exceeds the teaching rig bounds')
    delta = shift[:, None] * direction

    def warp(points, sign):
        result = points.copy()
        for j in (0, 1):
            result[:, j] += sign * np.interp(points[:, 2], levels, delta[:, j], left=0, right=0)
        return result

    for key, sign in zip(names, (-1, 1), strict=True):
        vertices, faces = meshes[key]
        meshes[key] = (warp(vertices, sign), faces)
        paths[key] = warp(paths[key], sign)
    active = np.flatnonzero(shift > .01)
    return {'maximumCenterShiftMm': round(float(shift.max()), 3),
            'adjustedZRangeMm': [round(float(levels[i]), 3) for i in (active[0], active[-1])],
            'transitionMm': 9., 'interbranchClearanceMm': .65}
