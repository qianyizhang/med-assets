"""Compose a compact bilingual lesson from unchanged V1 capture bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
INK, MUTED, PAPER = '#1c303b', '#526976', '#f5f7f8'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text(draw, xy, value, size=22, bold=False, zh=False, fill=INK):
    font = ImageFont.truetype(CJK if zh else BOLD if bold else REG, size)
    draw.text(xy, value, font=font, fill=fill)

def compose(renders, output):
    if output.exists():
        raise FileExistsError('New teaching directory required')
    bindings = json.loads((renders / 'bindings.json').read_text())
    views = {v['file']: v for v in bindings['views']}
    inputs = {'bindings.json': sha(renders / 'bindings.json')}
    plate = Image.new('RGB', (1900, 1130), PAPER)
    draw = ImageDraw.Draw(plate)
    text(draw, (36, 22), 'Right sciatic nerve: posterior hip locator', 36, bold=True)
    text(draw, (38, 72), '右侧坐骨神经：髋后方骨性定位', 28, zh=True)
    text(draw, (1200, 35), 'Native source coordinates · static study', 21, fill=MUTED)
    text(draw, (1200, 73), '保留来源坐标 · 颜色仅作区分', 22, zh=True, fill=MUTED)
    panels = [('whole-posterior.png', 'Whole subset', '来源范围', 36, 165, 430),
              ('hip-posterior.png', 'Posterior hip', '髋后面', 520, 165, 620),
              ('hip-oblique.png', 'Posterolateral detail', '后外侧细节', 1200, 165, 620)]
    labels = []
    for filename, en, zh, x, y, size in panels:
        text(draw, (x, 121), en, 23, bold=True)
        text(draw, (x + (360 if size == 620 else 270), 125), zh, 20, zh=True)
        path = renders / filename
        if sha(path) != views[filename]['sha256']:
            raise ValueError('Input image hash mismatch')
        inputs[filename] = sha(path)
        plate.paste(Image.open(path).convert('RGB').resize((size, size), Image.Resampling.LANCZOS), (x, y))
        pixels = views[filename]['anchorPixels']
        def project(key):
            return x + pixels[key][0] * size / 900, y + pixels[key][1] * size / 900
        if filename == 'whole-posterior.png':
            # Editorial region locator, not a registration or exact camera footprint.
            box = [x + q * size / 900 for q in (245, 650)]
            top, bottom = y + 50 * size / 900, y + 410 * size / 900
            draw.rectangle((box[0], top, box[1], bottom), outline=INK, width=3)
            px, py = project('distal')
            draw.ellipse((px-4, py-4, px+4, py+4), outline=INK, width=2)
            draw.line((x+166, py, px, py), fill=INK, width=2)
            text(draw, (x+7, py-13), 'Distal source end', 16, bold=True)
            text(draw, (x, 617), 'Box: hip region', 22, bold=True)
            text(draw, (x, 650), '方框：髋部观察区域', 22, zh=True)
            text(draw, (x, 699), 'Proximal strands are partial.', 21)
            text(draw, (x, 733), 'Ends mark the source extent.', 21)
            text(draw, (x, 771), '近端分支不全；末端为来源边界。', 20, zh=True)
        else:
            layout = {'nerve': (1, .13, .62), 'ischial': (2, .31, .90),
                      'trochanter': (3, .92, .50)}
            for key, (number, rx, ry) in layout.items():
                px, py = project(key)
                cx, cy = x + rx*size, y + ry*size
                assert x <= px <= x+size and y <= py <= y+size
                draw.line((cx, cy, px, py), fill=INK, width=2)
                draw.ellipse((px-3, py-3, px+3, py+3), fill=INK)
                draw.ellipse((cx-16, cy-16, cx+16, cy+16), fill='white', outline=INK, width=2)
                text(draw, (cx-7, cy-13), str(number), 20, bold=True)
                labels.append({'view': filename, 'number': number, 'anchor': key})
    for x, en, zh in [(38, '1  Sciatic nerve trunk', '坐骨神经主干'),
                      (650, '2  Ischial tuberosity region', '坐骨结节区'),
                      (1260, '3  Greater trochanter region', '大转子区')]:
        text(draw, (x, 838), en, 24, bold=True)
        text(draw, (x, 875), zh, 25, zh=True)
    draw.line((36, 936, 1820, 936), fill='#c5d0d5', width=2)
    text(draw, (38, 954), 'Use the bony landmarks to locate the retained sciatic course. This is a partial skeletal study.', 23)
    text(draw, (38, 992), '借助骨性标志辨认来源坐骨神经走行；本图仅显示部分骨骼。', 23, zh=True)
    text(draw, (38, 1034), 'Piriformis and ligaments omitted: source soft-tissue relationship unresolved.  梨状肌及韧带未显示，关系尚待确认。', 20, zh=True, fill=MUTED)
    text(draw, (38, 1085), 'Z-Anatomy · CC BY-SA 4.0 | BodyParts3D · Database Center for Life Science · historical CC BY-SA 2.1 Japan credit', 18, fill=MUTED)
    output.mkdir(parents=True)
    plate.save(output / 'teaching.png')
    ImageOps.grayscale(plate).save(output / 'teaching-grayscale.png')
    receipt = {'artifactSha256': bindings['artifactSha256'], 'inputs': inputs,
               'outputs': {p.name: sha(p) for p in output.glob('*.png')},
               'labels': labels, 'wholeLocatorRawPixels': [245, 50, 650, 410],
               'scope': 'V2 labels and editorial region locator; exact V1 GLB and raw captures reused. '
                        'Landmark vertices and first-visible checks are canonical in V1 bindings.'}
    (output / 'composition.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    compose(args.renders, args.out)
