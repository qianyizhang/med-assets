"""Compose native render pixels; captions explicitly distinguish offline views from UI."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('renders', type=Path)
args = parser.parse_args()
root = args.renders
title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipts = []
for view, caption in [('posterior-oblique', 'Posterior oblique · whole context'), ('cartilage-detail', 'Posterior oblique · cartilage detail')]:
    left, right = (root / f'{state}-{view}.png' for state in ['baseline', 'cartilage'])
    a, b = Image.open(left).convert('RGB'), Image.open(right).convert('RGB')
    assert a.size == b.size == (900, 900)
    plate = Image.new('RGB', (1800, 1020), '#171b20')
    plate.paste(a, (0, 100)); plate.paste(b, (900, 100))
    draw = ImageDraw.Draw(plate)
    draw.text((22, 14), 'Original · all 33 source parts', font=title, fill='white')
    draw.text((922, 14), 'Updated · cartilage isolation (5 parts)', font=title, fill='white')
    draw.text((22, 55), caption + ' | Matched camera, scale, light and unchanged GLB', font=small, fill='#c2cbd3')
    draw.text((922, 55), 'Offline Cycles renders · not browser/UI screenshots', font=small, fill='#c2cbd3')
    path = root / f'comparison-{view}.png'; plate.save(path)
    receipts.append({'file': path.name, 'sha256': sha(path), 'inputs': [{'file': p.name, 'sha256': sha(p)} for p in [left, right]], 'pixelPlacement': [[0, 100], [900, 100]], 'resampling': 'none'})
    if view == 'cartilage-detail':
        gray = root / 'comparison-detail-grayscale.png'
        ImageOps.grayscale(plate).save(gray)
        receipts.append({'file': gray.name, 'sha256': sha(gray), 'input': path.name, 'operation': 'Pillow ImageOps.grayscale; no geometry change'})
for view in ['front', 'posterior-oblique']:
    before, reset = [Image.open(root / f'{state}-{view}.png').convert('RGB') for state in ['baseline', 'reset']]
    assert before.tobytes() == reset.tobytes(), 'Reset pixels differ from initial view'
(root / 'comparison-receipt.json').write_text(json.dumps({'resetPixelsEqual': True, 'compositions': receipts}, indent=2) + '\n')
print('PASS two native-pixel comparison plates, grayscale and pixel-identical reset')
