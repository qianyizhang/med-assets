"""Measure the matched renders and make labeled comparison sheets."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, uniform_filter

VIEWS = {
    'whole': 'Whole exterior',
    'close': 'First fork · neutral close',
    'rotated-close': 'First fork · rotated underside',
    'opposite-close': 'First fork · opposite close',
    'reverse-whole': 'Whole exterior · reverse',
    'left-lobar-close': 'Accepted left lobar fairing · neutral close',
}
BACKGROUND = (27, 31, 37)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair(capture, view, geometry):
    for label in ('original', 'updated'):
        path = capture / view[label]['file']
        if sha(path) != view[label]['sha256'] or geometry[label]['sha256'] != view[label]['glbSha256']:
            raise ValueError(f'Image/export binding failed for {path}')
        with Image.open(path) as image:
            if image.mode != 'RGBA' or image.size != (1000, 850):
                raise ValueError(f'Expected a native 1000 × 850 RGBA view: {path}')
            yield image.copy()


def xy(index, shape):
    y, x = np.unravel_index(index, shape)
    return [int(x), int(y)]


def measure(original, updated):
    before, after = (np.asarray(image) for image in (original, updated))
    masks = [a[:, :, 3] >= 128 for a in (before, after)]
    before_mask, after_mask = masks
    common = before_mask & after_mask
    if not common.any():
        raise ValueError('Missing common foreground')
    difference = np.maximum(distance_transform_edt(~before_mask) * after_mask,
                            distance_transform_edt(~after_mask) * before_mask)
    opaque = (before[:, :, 3] == 255) & (after[:, :, 3] == 255)
    luma = np.abs((before[:, :, :3].astype(float) - after[:, :, :3]) @ [.2126, .7152, .0722])
    window = 9
    full_windows = uniform_filter(opaque.astype(float), size=window) > .9999
    patch = np.where(full_windows, uniform_filter(luma, size=window), 0)
    return {
        'foregroundPixels': [int(mask.sum()) for mask in masks],
        'foregroundXorPixels': int((before_mask ^ after_mask).sum()),
        'foregroundIoU': float(common.sum() / (before_mask | after_mask).sum()),
        'maxSilhouetteShiftPx': float(difference.max()),
        'worstSilhouetteXY': xy(difference.argmax(), difference.shape) if difference.any() else None,
        'p95OpaqueLumaDelta8bit': float(np.percentile(luma[opaque], 95)),
        'maxMeanOpaqueLumaDelta9pxPatch8bit': float(patch.max()),
        'worstLumaPatchXY': xy(patch.argmax(), patch.shape) if patch.any() else None,
    }


def sheet(images, title, path, detail=None):
    original, updated = images
    if detail:
        x, y = detail
        x = min(max(x - 48, 0), original.width - 96)
        y = min(max(y - 48, 0), original.height - 96)
        crop = (x, y, x + 96, y + 96)
        images = [image.crop(crop).resize((384, 384), Image.Resampling.NEAREST) for image in images]
    width, height = images[0].size
    canvas = Image.new('RGB', (width * 2 + 36, height + 94), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 12), title, font=ImageFont.load_default(size=24), fill='white')
    for offset, image, label in zip((12, width + 24), images, ('Original · r13', 'Updated · distal trial'), strict=True):
        draw.text((offset, 52), label, font=ImageFont.load_default(size=18), fill='white')
        canvas.paste(image, (offset, 80), image)
    canvas.save(path, lossless=True, method=6)


def locator(image, whole, views, path):
    preview = Image.new('RGB', (image.width, image.height + 66), BACKGROUND)
    preview.paste(image, (0, 0), image)
    draw = ImageDraw.Draw(preview)
    qw, qx, qy, qz = whole['quaternion']
    right = np.array([1 - 2 * (qy*qy + qz*qz), 2 * (qx*qy + qw*qz), 2 * (qx*qz - qw*qy)])
    up = np.array([2 * (qx*qy - qw*qz), 1 - 2 * (qx*qx + qz*qz), 2 * (qy*qz + qw*qx)])
    pixels_per_meter = image.width / whole['orthoScaleMeters']
    for number, name, color, label in (
        (1, 'close', '#ffda83', 'First fork · front, reverse and underside close views'),
        (2, 'left-lobar-close', '#a6ebe7', 'Left lobar fairing · neutral close view'),
    ):
        delta = np.array(views[name]['target']) - whole['target']
        x = image.width / 2 + pixels_per_meter * np.dot(right, delta)
        y = image.height / 2 - pixels_per_meter * np.dot(up, delta)
        draw.ellipse((x - 17, y - 17, x + 17, y + 17), outline=color, width=3)
        draw.text((x + 18, y - 24), str(number), font=ImageFont.load_default(size=22),
                  fill=color, stroke_width=2, stroke_fill=BACKGROUND)
        draw.text((24, image.height - 5 + (number - 1) * 28), f'{number}  {label}',
                  font=ImageFont.load_default(size=20), fill=color)
    preview.save(path, lossless=True, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    geometry = json.loads((args.capture / 'geometry.json').read_text())
    views = json.loads((args.capture / 'views.json').read_text())
    args.output.mkdir()
    metrics = {}
    for name, title in VIEWS.items():
        images = list(pair(args.capture, views[name], geometry))
        metrics[name] = measure(*images)
        path = args.output / f'{name}.webp'
        sheet(images, title, path)
        metrics[name]['sheetSha256'] = sha(path)
        if name == 'whole':
            path = args.output / 'locator.webp'
            locator(images[0], views[name], views, path)
            metrics[name]['locatorSha256'] = sha(path)
    name = max(metrics, key=lambda key: metrics[key]['maxSilhouetteShiftPx'])
    point = metrics[name]['worstSilhouetteXY']
    if point is not None:
        path = args.output / 'worst-silhouette.webp'
        sheet(list(pair(args.capture, views[name], geometry)),
              f'Maximum outline shift · {tuple(point)} · 4x crop', path, detail=point)
        metrics[name]['silhouetteDetailSha256'] = sha(path)
    name = max(metrics, key=lambda key: metrics[key]['maxMeanOpaqueLumaDelta9pxPatch8bit'])
    point = metrics[name]['worstLumaPatchXY']
    if point is not None:
        path = args.output / 'worst-shading.webp'
        sheet(list(pair(args.capture, views[name], geometry)),
              f'Maximum local shading change · {tuple(point)} · 4x crop', path, detail=point)
        metrics[name]['shadingDetailSha256'] = sha(path)
    (args.output / 'pixels.json').write_text(json.dumps(metrics, indent=2) + '\n')
    if any(row['maxSilhouetteShiftPx'] > 2 for row in metrics.values()):
        raise SystemExit('A foreground outline shifted more than two pixels')


if __name__ == '__main__':
    main()
