"""Extract normalized right-sided and thoracic footprints from a delivered breast study."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct

import numpy as np


def read_mesh(path):
    raw = path.read_bytes()
    vertices, faces = struct.unpack_from('<II', raw)
    points = np.frombuffer(raw, '<f4', 3 * vertices, 8).reshape(-1, 3)
    triangles = np.frombuffer(raw, '<u4', 3 * faces, 8 + 12 * vertices).reshape(-1, 3)
    return points, triangles, sha256(raw).hexdigest()


def gland_depth(vertices, faces, projected, footprint):
    """Read actual anterior/posterior y intersections on a polar footprint grid."""
    a, b, c = projected.transpose(1, 0, 2)
    ab, ac = b-a, c-a
    det = ab[:, 0]*ac[:, 1] - ab[:, 1]*ac[:, 0]
    valid = np.abs(det) > 1e-8
    depth = vertices[faces][:, :, 1]
    angles = np.arange(len(footprint)) * (2*np.pi/len(footprint))
    directions = np.column_stack((np.cos(angles), np.sin(angles)))
    radial = np.linspace(0, .94, 10)
    locations = radial[:, None, None]*footprint[None, :, None]*directions[None, :, :]
    hits = np.full((*locations.shape[:2], 2), np.nan)
    for index in np.ndindex(locations.shape[:2]):
        target = locations[index] - a
        u = np.divide(target[:, 0]*ac[:, 1] - target[:, 1]*ac[:, 0], det, out=np.zeros_like(det), where=valid)
        v = np.divide(ab[:, 0]*target[:, 1] - ab[:, 1]*target[:, 0], det, out=np.zeros_like(det), where=valid)
        inside = valid & (u >= -1e-6) & (v >= -1e-6) & (u+v <= 1+1e-6)
        if np.count_nonzero(inside) < 2:
            continue
        y = depth[inside, 0]*(1-u[inside]-v[inside]) + depth[inside, 1]*u[inside] + depth[inside, 2]*v[inside]
        if np.ptp(y) > 1e-4:
            hits[index] = [-y.max(), -y.min()]
    observed = np.isfinite(hits[..., 0])
    if np.count_nonzero(observed) < hits.shape[0] * hits.shape[1] * .6:
        raise ValueError('Native gland surface does not enclose the sampled footprint.')
    for index in zip(*np.nonzero(~observed), strict=True):
        nearest = np.argmin(np.linalg.norm(locations[observed] - locations[index], axis=1))
        hits[index] = hits[observed][nearest]
    centered = hits.mean(axis=-1)
    half = (.5*np.ptp(hits, axis=-1))
    midpoint = np.median(centered[:5])
    calibre = np.median(half[:5])
    return {'radii': radial.round(4).tolist(), 'mid': ((centered-midpoint)/calibre).round(3).tolist(),
            'half': (half/calibre).round(3).tolist(), 'sampled': int(observed.sum()), 'total': int(observed.size)}


def profile(path, right, upper_outer=False, include_depth=False):
    vertices, faces, digest = read_mesh(path)
    if right:
        faces = faces[np.all(vertices[faces, 0] > 0, axis=1)]
    if upper_outer:
        # Use the upper outer part of the retained right mound as a regional
        # footprint witness. The medial and inferior borders are editorial cuts.
        full = vertices[np.unique(faces)][:, (0, 2)]
        cut = full.min(axis=0) + .40 * np.ptp(full, axis=0)
        centers = vertices[faces].mean(axis=1)[:, (0, 2)]
        faces = faces[np.all(centers >= cut, axis=1)]
    cloud = vertices[np.unique(faces), :][:, (0, 2)]
    lower = cloud.min(axis=0)
    upper = cloud.max(axis=0)
    center = (lower + upper) / 2
    half = (upper - lower) / 2
    projected = (vertices[faces][:, :, (0, 2)] - center) / half
    start = projected.reshape(-1, 2)
    end = np.roll(projected, -1, axis=1).reshape(-1, 2)
    delta = end - start
    radius = []
    for angle in np.arange(48) * (2 * np.pi / 48):
        axis = np.array([np.cos(angle), np.sin(angle)])
        ortho = np.array([-axis[1], axis[0]])
        offsets = np.einsum('ij,j->i', start, ortho)
        transverse = np.einsum('ij,j->i', delta, ortho)
        fraction = np.divide(-offsets, transverse, out=np.full(len(delta), -1.), where=np.abs(transverse) > 1e-8)
        cross = (fraction >= 0) & (fraction <= 1)
        hits = np.einsum('ij,j->i', start[cross] + delta[cross] * fraction[cross, None], axis)
        radius.append(float(hits.max()))
    radius = np.asarray(radius)
    smooth = (.14*np.roll(radius, -1) + .72*radius + .14*np.roll(radius, 1)).round(4)
    result = {'sha256': digest, 'radii': smooth.tolist()}
    if include_depth:
        result['depth'] = gland_depth(vertices, faces, projected, smooth)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path)
    args = parser.parse_args()
    code = (args.study / 'abdomen-tours.js').read_text().strip()
    tours = json.loads(code.removeprefix('const abdomenTours = ').removesuffix(';'))
    tour = next(t for t in tours if t['id'] == 'breast')
    output = {}
    for key, part, right in [('lobular', 'fibroglandular_zone', True), ('tail-region', 'fibroglandular_zone', True),
                             ('pectoral', 'pectoralis', True), ('thoracic', 'chest_wall', False)]:
        name = tour.get('meshPaths', {}).get(part, f"{tour['assetRoot']}scenes/{part}.mesh")
        output[key] = {'part': part, **profile(args.study / name, right, upper_outer=key == 'tail-region',
                                                   include_depth=key in ('lobular', 'tail-region'))}
    print('// Generated by build-breast-profiles.py from the delivered breast sweep meshes.')
    print('export const breastProfiles = ' + json.dumps(output, indent=2) + ';')


if __name__ == '__main__':
    main()
