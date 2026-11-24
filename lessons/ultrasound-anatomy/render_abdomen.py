"""Replay matched color and teaching grayscale views of one s1233 axial section."""

import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, features

OWNER = Path(__file__).resolve().parent
WORKSHOP = OWNER.parents[1] / 'assemblies/workshop-s1233/inputs.json'


def mask_plane(path, source, index):
    compressed = path.read_bytes()
    expected_sha = source['maskSha256'][path.name.removesuffix('.nii.gz')]
    if hashlib.sha256(compressed).hexdigest() != expected_sha:
        raise ValueError(f'Unexpected source identity: {path.name}')
    raw = gzip.decompress(compressed)
    shape = struct.unpack_from('<3h', raw, 42)
    datatype = struct.unpack_from('<2h', raw, 70)
    affine = np.array(struct.unpack_from('<12f', raw, 280)).reshape(3, 4)
    offset = int(struct.unpack_from('<f', raw, 108)[0])
    if (shape != tuple(source['shape']) or datatype != (2, 8)
            or not np.array_equal(affine, source['rasMmFromVoxel'][:3])
            or not 0 <= index < shape[2]):
        raise ValueError(f'Incompatible source grid: {path.name}')
    nx, ny, _ = shape
    return np.frombuffer(raw, dtype=np.uint8, count=nx * ny, offset=offset + index * nx * ny).reshape(ny, nx)


def sample(mask, x, y):
    # Match smooth boundaries while retaining the original label grid and coordinates.
    left = np.floor(x).astype(int)
    top = np.floor(y).astype(int)
    fx, fy = x - left, y - top
    nx, ny = mask.shape[1], mask.shape[0]
    inside = (0 <= left) & (left + 1 < nx) & (0 <= top) & (top + 1 < ny)
    left, top = np.clip(left, 0, nx - 2), np.clip(top, 0, ny - 2)
    return inside * (
        (1 - fx) * ((1 - fy) * mask[top, left] + fy * mask[top + 1, left])
        + fx * ((1 - fy) * mask[top, left + 1] + fy * mask[top + 1, left + 1])
    )


def render(mask_dir, pose, source):
    display = pose['display']
    width, height, pitch = display['width'], display['height'], display['mmPerPixel']
    radius0 = pose['fieldOriginBehindContactMm']
    affine = np.array(source['rasMmFromVoxel'])
    contact_r, contact_a, contact_s = pose['contactRasMm']
    index = pose['sliceIndex']
    if abs(contact_s - (affine[2, 2] * index + affine[2, 3])) > 0.001:
        raise ValueError('Probe and section disagree on their superior position.')
    if (not np.array_equal(affine[:3, :3], np.diag([1.5] * 3))
            or pose['case'] != source['case']):
        raise ValueError('Unsupported case or affine for the authored view.')
    x = (np.arange(width)[None, :] + 0.5 - width / 2) * pitch
    y = (np.arange(height)[:, None] + 0.5 - display['probeRow']) * pitch
    radius = np.hypot(x, y + radius0)
    angle = np.arctan2(x, y + radius0)
    depth = radius - radius0
    field = (depth >= 0) & (depth <= pose['depthMm']) & (abs(angle) <= np.deg2rad(pose['halfAngleDegrees']))
    vx = (contact_r - x - affine[0, 3]) / affine[0, 0]
    vy = (contact_a - y - affine[1, 3]) / affine[1, 1]
    liver, gallbladder = (
        sample(mask_plane(mask_dir / f'{part}.nii.gz', source, index), vx, vy)
        for part in ('liver', 'gallbladder')
    )
    liver *= 1 - gallbladder
    labels = {'liver': liver, 'gallbladder': gallbladder}
    for target in pose['targets']:
        column = int(target['xPercent'] * width / 100)
        row = int(target['yPercent'] * height / 100)
        if not (0 <= column < width and 0 <= row < height and field[row, column]
                and labels[target['part']][row, column] > 0.9):
            raise ValueError(f"Teaching marker {target['label']} misses its in-field label.")
    tissue = 1 - liver - gallbladder

    rng = np.random.default_rng(417)
    coarse = Image.fromarray(rng.integers(0, 255, size=(62, 118), dtype=np.uint8))
    speckle = np.asarray(coarse.resize((width, height), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(1)))
    texture = (speckle.astype(float) - 127) * 0.46 + rng.normal(0, 4, size=field.shape)
    wall_y, wall_x = np.gradient(gallbladder)
    wall = 85 * np.clip(7 * abs(wall_y * np.cos(angle) + wall_x * np.sin(angle)), 0, 1)
    near_field = 44 * np.exp(-((depth - 2) / 1.3) ** 2) + 25 * np.exp(-((depth - 8) / 2.9) ** 2)
    grayscale = 74 * tissue + 113 * liver + 11 * gallbladder
    grayscale += texture * (1 - 0.87 * gallbladder) + near_field + wall - 0.17 * depth
    grayscale = np.where(field, np.clip(grayscale, 2, 232), 0).astype(np.uint8)
    section = (tissue[..., None] * [39, 42, 50] + liver[..., None] * [217, 132, 108]
               + gallbladder[..., None] * [120, 221, 184])
    section = np.where(field[..., None], section, 0).astype(np.uint8)
    return {'gallbladder-grayscale.webp': Image.fromarray(grayscale).convert('RGB'),
            'gallbladder-section.webp': Image.fromarray(section)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--masks', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if Image.__version__ != '12.2.0' or features.version_module('webp') != '1.6.0' or np.__version__ != '2.3.5':
        parser.error('Use NumPy 2.3.5 and Pillow 12.2.0 with libwebp 1.6.0.')
    if args.output.exists() or args.output.is_symlink():
        parser.error('Choose a fresh output directory.')
    try:
        images = render(args.masks, json.loads((OWNER / 'abdomen-gallbladder.json').read_text()),
                        json.loads(WORKSHOP.read_text()))
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    args.output.mkdir()
    for filename, image in images.items():
        image.save(args.output / filename, format='WEBP', lossless=True, method=6)


if __name__ == '__main__':
    main()
