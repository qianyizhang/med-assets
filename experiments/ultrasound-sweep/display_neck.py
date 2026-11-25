"""Fit an illustrative BodyParts3D bust around the measured thyroid probe window."""

import numpy as np
from scipy import ndimage as nd
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from build_study import volume
from display_body import BONES, BONES_SHA, SKIN, SKIN_SHA, atlas, primitive_stream, ras_from_gltf, smooth_atlas
from fit_abdomen import max_outer_error, ramp, surface_height
from geometry import VOXEL_MM

REGISTRATION_MASKS = {
    'vertebrae_C7': ('seventh cervical vertebra', 'c5072544a036cbe1d8849c44d89e1b4b0fa7fe599d629c0f587c03e4a8a891ad'),
    'vertebrae_T1': ('first thoracic vertebra', '7df8343c8d287cb6d04a5b81ee12fb89ac72b7603aba399d65489acf241a4ff2'),
    'vertebrae_T2': ('second thoracic vertebra', '2d6c169c6a77ba045656d3b5b6dd7154ba5aa05822d149b6fa056f076855cf80'),
    'vertebrae_T3': ('third thoracic vertebra', '5081be2bda278f4c0195967c0c0caba39b13af2b72258f716b4f7a7d938435d3'),
    'vertebrae_T4': ('fourth thoracic vertebra', '01fa86137a77b14b9e40ef86c636d66d67d06af5901bca743e481b0bdd8327ca'),
    'rib_left_1': ('left first rib', 'c0734d45022b7a90eafae6da9c81984c8cadea2941ef55d720cc0aa7a52c4f48'),
    'rib_right_1': ('right first rib', '5c7d250f6e2895d70bfa3b28d187b4aae1c35ada766ef7f41e348dbb1e74c13d'),
    'rib_left_2': ('left second rib', 'beef774472ba591a51faaf342dd7eb168af1eff93112e70a8af83a8b86959c65'),
    'rib_right_2': ('right second rib', '988094ca665cc9df9f02acb33004c8b248b6e480af40a5e1cbe0dd537643ec6e'),
}


def paired_landmarks(case, shape, affine):
    doc, _ = atlas(BONES, BONES_SHA)
    nodes = {node['name'].partition(' ')[2]: node for node in doc['nodes'] if 'mesh' in node}
    template, observed = [], []
    for name, (atlas_name, digest) in REGISTRATION_MASKS.items():
        mask = volume(case / 'segmentations' / f'{name}.nii.gz', digest, 'u1', shape, affine)
        components, _ = nd.label(mask)
        sizes = np.bincount(components.ravel())
        sizes[0] = 0
        if not sizes.max():
            raise ValueError(f'Missing registration bone: {name}')
        points = np.column_stack(np.nonzero(components == sizes.argmax()))
        # A tiny disconnected island in the second-rib source must not move its landmark.
        observed.append((points.min(0) + points.max(0)) / 2)
        node = nodes[atlas_name]
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        bounds = doc['accessors'][primitive['attributes']['POSITION']]
        template.append(ras_from_gltf(np.array([bounds['min'], bounds['max']])).mean(0) * 1000)
    return np.asarray(template), np.asarray(observed)


def registration(template, observed):
    origin, center = template.mean(0), observed.mean(0)
    # The source clips C7 and the case is supine. Permit pitch and bounded regional
    # scale, with smaller influence from the incomplete cervical landmark.
    weights = np.ones(len(template))
    weights[0] = .4

    def transform(vertices, params):
        sx, sy, sz, pitch, tx, ty, tz = params
        y, z = np.cos(pitch), np.sin(pitch)
        pitch_basis = np.array([[1, 0, 0], [0, y, -z], [0, z, y]])
        return np.einsum('ij,kj->ik', (vertices - origin) * [sx, sy, sz], pitch_basis) + center + [tx, ty, tz]

    def residual(params):
        delta = (transform(template, params) - observed) * weights[:, None]
        regularization = (np.array(params[:3]) - 1 / VOXEL_MM) * 15
        return np.r_[delta.ravel(), regularization]

    fit = least_squares(residual, [1 / VOXEL_MM] * 3 + [0, 0, 0, 0],
                        bounds=([.48, .48, .48, -.35, -20, -20, -20],
                                [1.12, 1.12, .98, .35, 20, 20, 20]))
    if not fit.success:
        raise ValueError('Could not register the illustrative neck exterior')
    errors = np.linalg.norm(transform(template, fit.x) - observed, axis=1) * VOXEL_MM
    return lambda points: transform(points, fit.x), errors


def crop_bust(vertices, faces):
    # Keep enough chest that an upward view toward the chin still hides the lower cut.
    upper_faces = faces[np.all(vertices[faces, 2] >= 1.0, axis=1)]
    used, indices = np.unique(upper_faces, return_inverse=True)
    return vertices[used], indices.reshape(-1, 3)


def refine(vertices, faces):
    # One shared midpoint per edge keeps the skin continuous across the fitted patch.
    edges = np.sort(faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    pairs, indices = np.unique(edges, axis=0, return_inverse=True)
    ab, bc, ca = (indices.reshape(-1, 3) + len(vertices)).T
    a, b, c = faces.T
    refined = np.concatenate([np.column_stack(part) for part in
                              [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]])
    return np.concatenate([vertices, vertices[pairs].mean(1)]), refined


def outer_height(vertices, faces, low, high, sampling=.5):
    """Rasterize the outer anterior sheet on a local XZ grid."""
    triangles = vertices[faces]
    xz = triangles[..., [0, 2]]
    good = np.all((xz.max(1) >= low) & (xz.min(1) <= high), axis=1)
    xz, depth = xz[good], triangles[good, :, 1]
    shape = tuple((np.rint((high - low) / sampling) + 1).astype(int))
    heights = np.full(shape, -np.inf)
    for xyz, y in zip((xz - low) / sampling, depth, strict=True):
        a, b, c = xyz
        ab, ac = b - a, c - a
        det = ab[0] * ac[1] - ab[1] * ac[0]
        if abs(det) < 1e-8:
            continue
        start = np.maximum(np.ceil(xyz.min(0)).astype(int), 0)
        end = np.minimum(np.floor(xyz.max(0)).astype(int) + 1, shape)
        x, z = np.ogrid[start[0]:end[0], start[1]:end[1]]
        u = ((x - a[0]) * ac[1] - (z - a[1]) * ac[0]) / det
        v = (ab[0] * (z - a[1]) - ab[1] * (x - a[0])) / det
        inside = (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
        patch = heights[start[0]:end[0], start[1]:end[1]]
        np.maximum(patch, np.where(inside, y[0] + u * (y[1] - y[0]) + v * (y[2] - y[0]), -np.inf), out=patch)
    return np.where(np.isfinite(heights), heights, np.nan)


def conform_neck(vertices, faces, shell, contacts):
    axes = [0, 2]
    projected = vertices[:, axes]
    contact_xz = contacts[:, axes]
    distance, _ = cKDTree(contact_xz / [1.15, .9]).query(projected / [1.15, .9])
    candidates = np.flatnonzero(distance < 30)
    xz = projected[candidates]
    low = np.floor(xz.min(0)) - 1
    high = np.ceil(xz.max(0)) + 1
    front = outer_height(vertices, faces, low, high)
    front_y = nd.map_coordinates(front, (xz - low).T * 2, order=1, cval=np.nan, prefilter=False)
    # Fade the fit on the upper neck before inheriting the separate CT chin contour.
    upper_window = contacts[:, 2].max() + 8
    case_xz = xz.copy()
    case_xz[:, 1] = np.minimum(case_xz[:, 1], upper_window)
    case_y = nd.map_coordinates(surface_height(shell, 1, 1), case_xz.T / 2,
                               order=1, cval=np.nan, prefilter=False)
    # Match measured skin close to the footprint. A shared shift preserves the gap
    # between the atlas's outer and inner sheets and leaves the posterior wall fixed.
    near = 1 - ramp((distance[candidates] - 13) / 17)
    near *= 1 - ramp((xz[:, 1] - upper_window) / 13)
    near *= ramp(((shell.shape[2] - 1) * 2 - xz[:, 1]) / 7)
    outer = 1 - ramp((front_y - vertices[candidates, 1] - 3) / 17)
    valid = np.isfinite(front_y) & np.isfinite(case_y)
    result = vertices.copy()
    result[candidates[valid], 1] += (near * outer * (case_y - front_y))[valid]
    return result


def fitted_neck(case, shell, contacts, beams, *, shape, affine, conformer=conform_neck):
    """Return the display-only atlas mesh and its registration/contact receipt."""
    template, observed = paired_landmarks(case, shape, affine)
    transform, landmarks = registration(template, observed)
    doc, binary = atlas(SKIN, SKIN_SHA)
    primitive = doc['meshes'][0]['primitives'][0]
    vertices = ras_from_gltf(primitive_stream(doc, binary, primitive['attributes']['POSITION']).reshape(-1, 3))
    faces = primitive_stream(doc, binary, primitive['indices']).reshape(-1, 3)
    vertices, faces = crop_bust(vertices, faces)
    vertices, faces = refine(transform(smooth_atlas(vertices, faces) * 1000), faces)
    vertices = conformer(vertices, faces, shell, contacts)
    error = max_outer_error(vertices, faces, contacts, beams)
    return vertices, faces, {
        'atlasSkinSha256': SKIN_SHA,
        'atlasBonesSha256': BONES_SHA,
        'registrationMaskSha256': {name: value[1] for name, value in REGISTRATION_MASKS.items()},
        'registrationBoneResidualMm': dict(zip(REGISTRATION_MASKS, landmarks.round(2).tolist(), strict=True)),
        'atlasDisplayMaxOuterContactErrorMm': round(error, 3),
    }
