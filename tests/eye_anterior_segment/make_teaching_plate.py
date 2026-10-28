#!/usr/bin/env python3
"""Caption the checked three-structure render without changing its pixels."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from verify_detail_review import check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
receipt = check(args.output)
source = args.output / 'anterior-order-three-structures.png'
plate_path = args.output / 'teaching-order.png'
gray_path = args.output / 'teaching-order-grayscale.png'
manifest_path = args.output / 'teaching-plate-manifest.json'
if any(p.exists() for p in [plate_path, gray_path, manifest_path]):
    raise ValueError('Refuse to overwrite teaching evidence')
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 22)
title_font = ImageFont.truetype(font_path, 28)
caption_lines = [
    'Cornea: translucent blue, in front. Iris: brown, around the pupil opening.',
    'Lens: opaque pale blue, behind iris; also visible THROUGH the pupil.',
    'Ciliary/zonular geometry omitted. Layer hiding is not a physical section.',
    'Illustrative materials. Order only: no shape, attachment, optical or clinical claim.',
]
with Image.open(source) as image:
    raw = image.convert('RGB')
plate = Image.new('RGB', (1000, 1220), (25, 29, 35))
plate.paste(raw, (0, 65))
draw = ImageDraw.Draw(plate)
draw.text((24, 17), 'Right anterior eye: broad order only', font=title_font, fill='white')
for i, text in enumerate(caption_lines):
    if draw.textbbox((0, 0), text, font=font)[2] > 952:
        raise ValueError('Caption does not fit')
    draw.text((24, 1080 + i * 32), text, font=font, fill=(244, 227, 187))
plate.save(plate_path)
plate.convert('L').save(gray_path)
# The teaching panel must retain every decoded RGB pixel from the checked render.
if Image.open(plate_path).crop((0, 65, 1000, 1065)).tobytes() != raw.tobytes():
    raise ValueError('Caption step changed the render pixels')
manifest = {'artifactSha256': receipt['artifact']['sha256'],
            'sourceRender': {'file': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
            'caption': caption_lines, 'title': 'Right anterior eye: broad order only',
            'renderPixelsUnchanged': True, 'font': 'DejaVuSans.ttf',
            'files': [{'file': p.name, 'bytes': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [plate_path, gray_path]],
            'scope': 'Captioned order-only teaching view plus grayscale readability diagnostic; not anatomy approval.'}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('PASS captioned teaching plate: render pixels unchanged; explicit pupil/lens distinction and exclusions.')
