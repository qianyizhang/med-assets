"""Compound stored B-mode pixels and their tracked poses into a calibrated grayscale volume."""

import gzip
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from reconstruction import plane_to_world, world_to_pixel


def compound(root, frames, lateral_pitch=.5):
    z = np.array([f['contact'][2] for f in frames])
    if len(z) < 3 or np.any(np.diff(z) <= 0):
        raise ValueError('Volume requires successive inferior-to-superior tracking planes')
    for f in frames:
        axes = np.array([f['width'], f['beam']])
        if not np.allclose(axes @ axes.T, np.eye(2), atol=1e-5) or abs(axes[:, 2]).max() > 1e-5:
            raise ValueError('Volume requires calibrated in-plane transverse axes')
    corners = np.concatenate([plane_to_world(f, [[x, y] for y in (0, f['heightPx'] - 1)
                                                 for x in (0, f['widthPx'] - 1)]) for f in frames])
    low = np.floor(corners[:, :2].min(0) / lateral_pitch) * lateral_pitch
    high = corners[:, :2].max(0)
    x, y = [np.arange(a, b + lateral_pitch, lateral_pitch) for a, b in zip(low, high, strict=True)]
    xx, yy = np.meshgrid(x, y)
    points = np.stack([xx, yy, np.zeros_like(xx)], axis=-1)
    # Keep the acquisition's native inter-plane resolution. -1 specifies a voxel
    # outside coverage; 0 is a valid black B-mode observation.
    typical_step = np.median(np.diff(z))
    heights = np.linspace(z[0], z[-1], round((z[-1] - z[0]) / typical_step) + 1)
    volume = np.full((len(heights), len(y), len(x)), -1, dtype='<i2')
    previous = None
    for index, f in enumerate(frames):
        with Image.open(root / f['path']) as image:
            if image.size != (f['widthPx'], f['heightPx']):
                raise ValueError(f"Uncalibrated B-mode frame {f['id']}")
            pixels = np.asarray(image.convert('L'), dtype='f4')
        col, row = world_to_pixel(f, points).transpose(2, 0, 1)
        current = ndimage.map_coordinates(pixels, [row, col], order=1, mode='constant', cval=np.nan)
        # Reject subpixel extrapolation beyond an observed field or a missing
        # chunk of the acquisition. A genuine recorded plane stands on its own.
        for layer in np.flatnonzero(np.isclose(heights, z[index], rtol=0, atol=1e-6)):
            valid = np.isfinite(current)
            volume[layer, valid] = np.rint(current[valid])
        if previous is not None and z[index] - z[index - 1] <= 2.1 * typical_step:
            between = np.flatnonzero((heights > z[index - 1] + 1e-6) & (heights < z[index] - 1e-6))
            valid = np.isfinite(previous) & np.isfinite(current)
            for layer in between:
                t = (heights[layer] - z[index - 1]) / (z[index] - z[index - 1])
                volume[layer, valid] = np.rint(previous[valid] * (1 - t) + current[valid] * t)
        previous = current
    return volume, [*low, z[0]], [lateral_pitch, lateral_pitch, heights[1] - heights[0]]


def write_volumes(root, tracking):
    folder = Path(root) / 'volumes'
    folder.mkdir(exist_ok=True)
    summary = {}
    for side, frames in tracking.items():
        values, origin, pitch = compound(root, frames)
        nx, ny, nz = values.shape[::-1]
        header = ('NRRD0005\n# Z-Anatomy / BodyParts3D adapted under CC BY-SA 4.0\n'
                  '# -1 = outside acquired image coverage; 0..255 = modeled B-mode intensity\n'
                  f'type: short\ndimension: 3\nsizes: {nx} {ny} {nz}\nspace: right-anterior-superior\n'
                  f'space directions: ({pitch[0]},0,0) (0,{pitch[1]},0) (0,0,{pitch[2]})\n'
                  f'space origin: ({origin[0]},{origin[1]},{origin[2]})\n'
                  'space units: "mm" "mm" "mm"\nencoding: gzip\nendian: little\n\n')
        path = f'volumes/{side}-bmode.nrrd'
        (root / path).write_bytes(header.encode('ascii') + gzip.compress(values.tobytes(), compresslevel=6, mtime=0))
        # Open on the first fork with two substantial observed contours.
        view = next((f for f in frames if f['segment'] == 'branches' and len(f['contours']) >= 2),
                    frames[len(frames) // 2])
        rings = view.get('contours') or [plane_to_world(view, [[view['widthPx'] / 2, view['heightPx'] / 2]])]
        focus = np.mean(np.concatenate(rings), axis=0)
        summary[side] = {'path': path, 'size': [nx, ny, nz], 'spacingMm': pitch, 'originMm': origin,
                         'focusMm': focus.tolist(), 'planes': len(frames), 'missingValue': -1}
    return summary
