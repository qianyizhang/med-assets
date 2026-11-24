"""Add a soft tissue window to the registered pose renders."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    folder = parser.parse_args().output
    internal = np.asarray(Image.open(folder / 'internal.png').convert('RGBA'), dtype=float)
    y, x = np.mgrid[:internal.shape[0], :internal.shape[1]]
    window = np.exp(-(((x-300)/195)**2 + ((y-199)/155)**2)**2)
    visible = internal[..., 3]/255 * window
    tint = internal[..., :3]
    frames = json.loads((folder / 'sweep.js').read_text().removeprefix('const sweep = ').strip()[:-1])
    sources = [folder / 'media' / f'base-{i:02}.webp' for i in range(len(frames))]
    if any(not path.is_file() for path in sources):
        parser.error('Render every probe pose before compositing.')
    sectors = json.loads((folder / 'projected-field.json').read_text())
    for path, sector in zip(sources, sectors, strict=True):
        skin = np.asarray(Image.open(path).convert('RGB'), dtype=float)
        # The warm skin material separates the surface from the neutral housing.
        skin_mask = np.clip((skin[..., 0]-skin[..., 2]-8)/19, 0, 1)
        weight = (.90 * visible * gaussian_filter(skin_mask, .65))[..., None]
        result = tint * weight + skin*(1-weight)
        image = Image.fromarray(result.astype('u1'))
        drawing = ImageDraw.Draw(image, 'RGBA')
        points = [tuple(point) for point in sector]
        drawing.polygon(points, fill=(114, 239, 219, 35))
        drawing.line(points + [points[0]], fill=(152, 251, 228, 160), width=1)
        image.save(path.with_name(path.name.replace('base-', 'pose-')), quality=93)


if __name__ == '__main__':
    main()
