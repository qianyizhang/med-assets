#!/usr/bin/env python3
"""Build hash-checked matched plates with numbered badges at native panel scale."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from build import GROUPS, require, sha

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG, INK, MUTED = '#101b26', '#f0f5f7', '#b5c4d0'


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def read_run(folder):
    receipt = json.loads((folder / 'render.json').read_text())
    for row in receipt['views']:
        path = folder / row['file']
        require(path.name == row['file'], 'Image path must be a basename')
        require(path.stat().st_size == row['bytes'] and sha(path.read_bytes()) == row['sha256'],
                'Rendered image identity mismatch')
    return receipt


def panel(folder, row, numbered=False, grayscale=False, right_only=False):
    im = Image.open(folder / row['file']).convert('RGB')
    require(im.size == (800, 800), 'Expected native 800px image')
    if grayscale:
        im = ImageOps.grayscale(im).convert('RGB')
    if numbered:
        draw = ImageDraw.Draw(im)
        for anchor in row['anchors']:
            if right_only and anchor['number'] > 3:
                continue
            x, y = anchor['pixel']
            require(24 <= x <= 776 and 24 <= y <= 776, 'Badge would clip panel')
            draw.ellipse((x-20, y-20, x+20, y+20), fill=BG, outline=INK, width=2)
            draw.text((x, y), str(anchor['number']), font=font(23, True), fill=INK, anchor='mm')
    return im


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v1-renders', type=Path, required=True)
    parser.add_argument('--v2-renders', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    old, new = read_run(args.v1_renders), read_run(args.v2_renders)
    for key in ('renderer', 'engine', 'samples', 'seed', 'resolution', 'denoising',
                'viewTransform', 'look', 'exposure', 'gamma'):
        require(old[key] == new[key], 'Render conditions differ')
    require(old['build']['baselineSha256'] == new['build']['baselineSha256'], 'Baseline differs')
    base = {r['view']: r for r in old['views'] if r['variant'] == 'baseline'}
    current = {r['view']: r for r in new['views'] if r['variant'] == 'v2'}
    require(set(base) == set(current) == {'context', 'reverse', 'right-detail'}, 'Missing matched view')
    for key in base:
        for field in ('cameraLocation', 'target', 'orthoScaleM', 'visibleNodes', 'anchors'):
            require(base[key][field] == current[key][field], 'Unmatched camera/geometry/anchors')
    require({a['number'] for a in current['context']['anchors']} == {1, 2, 3, 4, 5},
            'Context must label all five lobes')
    args.output.mkdir(parents=True, exist_ok=False)
    receipts = []
    for name, views, gray in [('matched-context', ['context'], False),
                              ('matched-reverse-detail', ['reverse', 'right-detail'], False),
                              ('grayscale-context', ['context'], True)]:
        height = 130 + len(views)*840 + 194
        canvas = Image.new('RGB', (1600, height), BG)
        draw = ImageDraw.Draw(canvas)
        draw.text((26, 20), 'FIVE LUNG LOBES  /  teaching material study', font=font(31, True), fill=INK)
        draw.text((26, 65), 'Baseline: one pink material', font=font(24, True), fill=MUTED)
        draw.text((826, 65), 'V2: matte regions + numbered labels', font=font(24, True), fill=INK)
        for i, key in enumerate(views):
            y = 130 + i*840
            caption = {'context': 'Source frontal view; subject right is on image left',
                       'reverse': 'Reverse view; the right middle lobe is hidden by retained geometry',
                       'right-detail': 'Right lobe junction detail; cropped for inspection, no geometry cut'}[key]
            draw.text((26, y-29), caption, font=font(20), fill=MUTED)
            canvas.paste(panel(args.v1_renders, base[key], grayscale=gray), (0, y))
            canvas.paste(panel(args.v2_renders, current[key], True, gray, key == 'right-detail'), (800, y))
        y = 130 + len(views)*840
        for index, (_, label, _, _) in enumerate(GROUPS):
            x = 26 + (index % 3)*520
            yy = y + (index//3)*34
            draw.text((x, yy), f'{index+1}  {label}', font=font(22, True), fill=INK)
        draw.text((26, y+78), 'False colors show source-labeled groups, not natural tissue. Geometry, normals and frame unchanged.',
                  font=font(20), fill=MUTED)
        draw.text((26, y+108), 'Draft offline study: no complete airway, motion, clinical approval or live viewer validation.',
                  font=font(20), fill=MUTED)
        draw.text((26, y+138), 'Browne & Schlehlein / HRA female lung v1.3 / CC BY 4.0. Material and label adaptation, 2026-10-28.',
                  font=font(19), fill=MUTED)
        path = args.output / (name + '.jpg')
        canvas.save(path, quality=86, subsampling=0, optimize=True)
        receipts.append({'file': path.name, 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
                         'views': views, 'grayscale': gray, 'jpegQuality': 86, 'dimensions': list(canvas.size)})
    (args.output / 'comparison.json').write_text(json.dumps({
        'baselineSha256': old['build']['baselineSha256'],
        'candidateSha256': new['build']['candidateSha256'], 'plates': receipts,
        'note': 'Native 800px panels; annotations added, then lossy JPEG compression. Not runtime screenshots.'}, indent=2)+'\n')


if __name__ == '__main__':
    main()
