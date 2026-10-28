#!/usr/bin/env python3
"""Verify four native frames and compose labeled comparisons without resizing."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import BASELINE_SHA256, KEEP, OMIT, require

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--review', type=Path, required=True)
args = parser.parse_args()
receipt = json.loads((args.review / 'reimport-render-receipt.json').read_text())
build_receipt = json.loads((args.review.parent / 'build-receipt.json').read_text())
require(receipt['baselineSha256'] == BASELINE_SHA256, 'Wrong baseline hash')
require(receipt['candidateSha256'] == build_receipt['candidate']['sha256'], 'Wrong candidate hash')
require(receipt['resolution'] == [1000, 1000] and len(receipt['views']) == 4, 'Expected four native frames')
rows = {(v['variant'], v['view']): v for v in receipt['views']}
require(set(rows) == {(v, p) for v in ('baseline', 'candidate') for p in ('context', 'detail')}, 'Wrong frame identities')
images = {}
for key, row in rows.items():
    name = f'{key[0]}-{key[1]}.png'
    require(row['file'] == name, 'Unexpected frame path')
    raw = (args.review / name).read_bytes()
    require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Frame hash/size mismatch')
    require(row['visibleNodes'] == sorted(KEEP + (OMIT if key[0] == 'baseline' else ())), 'Wrong node visibility')
    image = Image.open(args.review / name).convert('RGB')
    require(image.size == (1000, 1000), 'Frame dimensions mismatch')
    require(sum(lo != hi for lo, hi in image.getextrema()) == 3, 'Blank frame')
    images[key] = image
for view in ('context', 'detail'):
    for field in ('cameraLocation', 'target', 'orthoScaleM'):
        require(rows['baseline', view][field] == rows['candidate', view][field], 'Unmatched camera')

font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 24)
title_font = ImageFont.truetype(font_path, 32)
outputs = []
for view in ('context', 'detail'):
    plate = Image.new('RGB', (2000, 1230), '#17202a')
    draw = ImageDraw.Draw(plate)
    draw.text((24, 16), f'Eye order study / {view} / DRAFT', font=title_font, fill='white')
    draw.text((24, 64), 'Baseline: 7 diagnostic meshes', font=font, fill='white')
    draw.text((1024, 64), 'Derivative: 3 retained meshes', font=font, fill='white')
    for col, variant in enumerate(('baseline', 'candidate')):
        image = images[variant, view]
        plate.paste(image, (col * 1000, 110))
        require(plate.crop((col * 1000, 110, (col + 1) * 1000, 1110)).tobytes() == image.tobytes(),
                'Native pixels changed during composition')
    lines = ['Cornea in front; iris surrounds pupil opening; opaque blue disk is lens. Illustrative materials.',
             'Four ciliary/zonular meshes are omitted from export. Missing support is editorial, not normal anatomy.',
             'No attachment, corneal shape/thickness, optics, accommodation, normal-atlas or clinical validity.']
    for i, line in enumerate(lines):
        draw.text((24, 1120 + i * 33), line, font=font, fill='#eedcaa')
    path = args.review / f'comparison-{view}.png'
    require(not path.exists(), 'Comparison already exists')
    plate.save(path)
    outputs.append(path)
    if view == 'context':
        path = args.review / 'comparison-context-grayscale.png'
        require(not path.exists(), 'Grayscale comparison already exists')
        plate.convert('L').save(path)
        outputs.append(path)
manifest = {'baselineSha256': receipt['baselineSha256'], 'candidateSha256': receipt['candidateSha256'],
            'nativePixelsPreservedInColorPlates': True,
            'grayscaleScope': 'Readability diagnostic only; not accessibility or anatomy certification',
            'outputs': [{'file': p.name, 'bytes': p.stat().st_size,
                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in outputs]}
(args.review / 'comparison-receipt.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('PASS native identities, matched cameras, exact node inventory and color-panel pixel preservation')
