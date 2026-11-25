"""Read the exported NRRD and check its voxels against independently projected B-mode pixels."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image


def read_nrrd(path):
    header, compressed = path.read_bytes().split(b'\n\n', 1)
    fields = dict(line.split(': ', 1) for line in header.decode().splitlines() if ': ' in line and not line.startswith('#'))
    assert fields['space'] == 'right-anterior-superior' and fields['type'] == 'short'
    assert fields['encoding'] == 'gzip' and fields['endian'] == 'little'
    size = list(map(int, fields['sizes'].split()))
    origin = np.fromstring(fields['space origin'].strip('()'), sep=',')
    directions = [np.fromstring(v.strip('()'), sep=',') for v in fields['space directions'].split()]
    return np.frombuffer(gzip.decompress(compressed), '<i2').reshape(size[::-1]), origin, np.array(directions)


def sample_frame(root, frame, points):
    relative = points - frame['contact']
    xy = relative @ np.array([frame['width'], frame['beam']]).T / frame['mmPerPx'] + frame['centerPx']
    with Image.open(root / frame['path']) as image:
        intensity = np.asarray(image.convert('L'), dtype='f4')
    h, w = intensity.shape
    xy0 = np.floor(xy).astype(int)
    valid = (xy[:, 0] >= 0) & (xy[:, 0] <= w-1) & (xy[:, 1] >= 0) & (xy[:, 1] <= h-1)
    i, j = np.clip(xy0, [0, 0], [w-2, h-2]).T
    u, v = xy.T - [i, j]
    value = ((1-u) * (1-v) * intensity[j,i] + u * (1-v) * intensity[j,i+1] +
             (1-u) * v * intensity[j+1,i] + u * v * intensity[j+1,i+1])
    return value, valid


def verify(root):
    geometry = json.loads((root / 'protocol-geometry.json').read_text())
    rng = np.random.default_rng(8271)
    for side, info in geometry['volumes'].items():
        voxels, origin, matrix = read_nrrd(root / info['path'])
        assert list(voxels.shape[::-1]) == info['size'] and np.allclose(origin, info['originMm'])
        assert np.allclose(matrix, np.diag(info['spacingMm']))
        frames = geometry['tracking'][side]
        z = np.array([f['contact'][2] for f in frames])
        assert np.isclose(origin[2], z[0]) and np.isclose(origin[2] + matrix[2,2]*(voxels.shape[0]-1), z[-1])
        valid_count = outside_count = 0
        for k, image in enumerate(voxels):
            h, w = image.shape
            xy = rng.integers([0, 0], [w, h], size=(80, 2))
            points = np.column_stack([xy, np.full(len(xy), k)]) @ matrix + origin
            level = points[0,2]
            nearest = int(np.argmin(abs(z-level)))
            if abs(z[nearest]-level) < 1e-6:
                expected, known = sample_frame(root, frames[nearest], points)
            else:
                upper = int(np.searchsorted(z, level))
                a, av = sample_frame(root, frames[upper-1], points)
                b, bv = sample_frame(root, frames[upper], points)
                fraction = (level-z[upper-1])/(z[upper]-z[upper-1])
                expected = a*(1-fraction) + b*fraction
                known = av & bv & (z[upper]-z[upper-1] <= 2.1 * np.median(np.diff(z)))
            actual = image[xy[:,1],xy[:,0]]
            assert np.all(abs(actual[known] - expected[known]) <= .51)
            assert np.all(actual[~known] == -1)
            valid_count += known.sum()
            outside_count += (~known).sum()
        assert valid_count > 1000 and outside_count > 100
        print(f'{side}: NRRD RAS calibration verified, {valid_count} sampled intensities and {outside_count} outside-field voxels agree.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    verify(parser.parse_args().data)
