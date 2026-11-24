"""Compare the exported triangle cuts with the image sampler at pregnancy reference stops."""
import argparse
from pathlib import Path
import struct

import numpy as np
from PIL import Image

from build_abdomen import ImagingGrid
from build_pregnancy import read_pregnancy_tracks, sample_section
from delivery import read_poses
from geometry import KEYFRAMES


def plane_segments(path, pose, voxel_mm):
    data = path.read_bytes()
    vertex_count, face_count = struct.unpack_from('<II', data)
    vertices = np.frombuffer(data, '<f4', vertex_count * 3, 8).reshape(-1, 3)
    faces = np.frombuffer(data, '<u4', face_count * 3, 8 + vertex_count * 12).reshape(-1, 3)
    width, beam = np.array(pose['width']), np.array(pose['beam'])
    axes = np.array([width, beam, np.cross(width, beam)])
    local = np.einsum('vi,ji->vj', vertices - pose['contact'], axes) * voxel_mm
    triangles = local[faces]
    distances = triangles[:, :, 2]
    triangles = triangles[(distances.min(axis=1) < 0) & (distances.max(axis=1) >= 0)]
    segments = np.empty((len(triangles), 2, 2))
    ends = np.zeros(len(triangles), dtype=int)
    for first, second in [(0, 1), (1, 2), (2, 0)]:
        a, b = triangles[:, first], triangles[:, second]
        crossed = (a[:, 2] < 0) != (b[:, 2] < 0)
        a, b = a[crossed], b[crossed]
        fraction = -a[:, 2, None] / (b[:, 2, None] - a[:, 2, None])
        segments[crossed, ends[crossed]] = a[:, :2] + fraction * (b[:, :2] - a[:, :2])
        ends[crossed] += 1
    assert (ends == 2).all(), f'Incomplete triangle intersection in {path}'
    return segments


def rasterize(segments, grid):
    """Fill the closed mesh section from ordered contour crossings on each raster row."""
    a, b = segments[:, 0], segments[:, 1]
    mask = np.zeros_like(grid.field)
    for row, height in enumerate(grid.y[:, 0]):
        crossed = (a[:, 1] < height) != (b[:, 1] < height)
        p, q = a[crossed], b[crossed]
        fraction = (height - p[:, 1]) / (q[:, 1] - p[:, 1])
        edges = np.sort(p[:, 0] + fraction * (q[:, 0] - p[:, 0]))
        assert len(edges) % 2 == 0, f'Open contour at row {row}'
        mask[row] = np.searchsorted(edges, grid.x[row]) % 2 == 1
    return mask & grid.field


def verify(sweeps):
    for track in read_pregnancy_tracks():
        root = sweeps / track['id']
        poses = read_poses(root / 'sweep.js')
        grid = ImagingGrid(track['sectorDepthMm'])
        for frame, landmarks in zip(KEYFRAMES, track['landmarkMinimums'], strict=True):
            pose = poses[frame]
            gray, masks, _ = sample_section(grid, pose)
            with Image.open(root / 'media' / f'scan-{frame:02}.webp') as image:
                delivered = np.asarray(image.convert('L'), dtype=float)
            # Allow WebP compression, while detecting a different frame or a reversed image.
            assert np.abs(delivered - gray).mean() < 1.5, f'Scan mismatch: {root.name}, frame {frame}'
            for name in landmarks:
                lines = plane_segments(root / 'scenes' / f'{name}.mesh', pose, track['voxelMm'])
                cut = rasterize(lines, grid)
                expected = masks[name]
                denominator = cut.sum() + expected.sum()
                score = 2 * (cut & expected).sum() / denominator if denominator else 0
                assert score > .95, f'{root.name}, frame {frame}, {name}: mesh/section Dice {score:.3f}'
                print(f'{root.name} {frame} {name} {score:.4f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps', type=Path, help='Staging sweeps directory containing both pregnancy routes')
    verify(parser.parse_args().sweeps)
