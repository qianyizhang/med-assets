"""Conform a rib-registered bust to the bilateral s1127 carotid contact windows."""

import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree

from display_neck import outer_height
from fit_abdomen import ramp, surface_height


def conform_neck(vertices, faces, shell, contacts):
    """Fit the measured windows and extend the correction smoothly toward the jaw.

    The CT ends across the upper neck. Applying that clipped boundary directly
    to a complete head produces a ledge under the chin. Only the two measured
    lateral windows constrain the displacement; the collar around them blends
    back into the source head and shoulders.
    """
    anchors = contacts[:, [0, 2]]
    # Set the anterior head position as a rigid translation above the fitted
    # neck. The gradual transition from the upper chest preserves the lips,
    # underside of the mandible and the original facial silhouette.
    result = vertices.copy()
    pose = ramp((vertices[:, 2] - 361) / 34)
    result[:, 1] += 16 * pose
    margin = 49
    low = np.floor(anchors.min(0)) - margin
    high = np.ceil(anchors.max(0)) + margin
    atlas = outer_height(result, faces, low, high, sampling=1.)
    gx, gz = np.indices(atlas.shape) + low[:, None, None]
    distance = cKDTree(anchors).query(np.stack((gx, gz), axis=-1))[0]
    case = nd.map_coordinates(surface_height(shell, 1, 1), (gx / 2, gz / 2),
                              order=1, cval=np.nan, prefilter=False)
    observed = (distance <= 11) & np.isfinite(atlas) & np.isfinite(case)
    # The native chin becomes a separate anterior surface above the central
    # throat. It supplies no constraint between the two lateral windows.
    observed &= ~((gz > 398) & (gx > 116) & (gx < 151) & (distance > 8))
    if not observed.any():
        raise ValueError('Carotid probe windows miss the atlas or CT surface')
    delta = np.where(observed, case - atlas, 0)
    # A neighboring chin/skin fold can appear in the anterior CT projection
    # beside the lens. Bound its influence by the correction actually needed
    # at the beam centers, then interpolate over several CT voxels.
    anchor_grid = (anchors - low).T
    anchor_delta = nd.map_coordinates(delta, anchor_grid, order=1, mode='nearest')
    d, ids = cKDTree(anchors).query(np.stack((gx, gz), axis=-1), k=3)
    local_anchor = np.mean(anchor_delta[ids], axis=-1)
    allowance = 2.0 + .26 * d[..., 0]
    delta = np.where(observed, np.clip(delta, local_anchor - allowance, local_anchor + allowance), 0)
    # Extension is progressively smoother outside the windows. Normalized
    # kernels avoid propagating the CT edge or a nearest-station seam upward.
    shift = np.zeros_like(delta)
    for sigma in (12., 7., 3.):
        weights = nd.gaussian_filter(observed.astype(float), sigma)
        local = nd.gaussian_filter(delta, sigma) / np.maximum(weights, 1e-7)
        mix = ramp(weights / .7)
        shift += mix * (local - shift)
    shift *= 1 - ramp((distance - 12) / 29)
    above = max(anchors[:, 1]) + 7
    shift *= 1 - ramp((gz - above) / 14)
    points = (result[:, [0, 2]] - low).T
    correction = nd.map_coordinates(shift, points, order=1, mode='constant', cval=0)
    anterior = ramp((result[:, 1] - 80) / 54)
    result[:, 1] += anterior * correction
    return result
