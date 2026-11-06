"""Annotate the exact retained issue 102 grayscale comparison for review."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SOURCE_SHA = '72368e51985346e760beafb9c60983215b5617c24a6fe379e02c99c66bf4e321'
COLORS = ['A93664', 'F2D38C', '276D8A', 'D1905A', '596878']

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--params', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if hashlib.sha256(a.comparison.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Wrong reviewed comparison')
    if a.output.exists():
        raise FileExistsError('Refuse to overwrite a review image')
    image = Image.open(a.comparison).convert('RGB')
    if image.size != (1600, 1120):
        raise ValueError('Unexpected comparison size')
    params = json.loads(a.params.read_text())
    radii = [params[k] for k in ('lumen_radius_m', 'mucosa_outer_radius_m',
        'submucosa_outer_radius_m', 'circular_muscle_outer_radius_m',
        'longitudinal_muscle_outer_radius_m', 'adventitia_outer_radius_m')]
    if not all(0 < x < y for x, y in zip(radii, radii[1:])):
        raise ValueError('Invalid compartment radii')
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    d = ImageDraw.Draw(image)
    d.text((1110, 24), 'GRAYSCALE REVIEW | 1–5 = regions', font=small, fill='#ffffff')
    for left in (20, 820):
        center = (left + 380, 108 + 418)
        for k, (inner, outer, angle) in enumerate(zip(radii[:-1], radii[1:], (150,120,90,60,30)), 1):
            theta = math.radians(angle)
            # The rendered top-view outer radius is 300 pixels in this fixed comparison.
            radius = 300 * (inner + outer) / (2 * radii[-1])
            x = center[0] + radius * math.cos(theta)
            y = center[1] - radius * math.sin(theta)
            if k == 5:
                tx, ty = x, y
                x += 39; y -= 23
                d.line((tx, ty, x, y), fill='#ffffff', width=2)
                d.ellipse((tx-3,ty-3,tx+3,ty+3), fill='#101923', outline='white')
            d.ellipse((x-17,y-17,x+17,y+17), fill='#101923', outline='white', width=2)
            d.text((x,y-1),str(k),anchor='mm',font=font,fill='white')
    # Swatches on a grayscale comparison must show grayscale values too.
    for k, color in enumerate(COLORS):
        x = 28 + (k % 3) * 510
        y = 1007 + (k // 3) * 37
        gray = Image.new('RGB', (1,1), '#'+color).convert('L').getpixel((0,0))
        d.rectangle((x,y,x+20,y+20), fill=(gray,gray,gray))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(a.output)
    print(json.dumps({'inputSha256':SOURCE_SHA, 'outputSha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),
                      'scope':'Grayscale comparison labels only; original render pixels unchanged away from annotations.'}))

if __name__ == '__main__': main()
