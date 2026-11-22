"""Compose the three current bilingual teaching plates from the clean-import views."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LATIN_FONT = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
CHINESE_FONT = Path('/System/Library/Fonts/STHeiti Medium.ttc')
INK = '#172b32'
BACKGROUND = '#f5f2ed'
DEEP_VIEW = ('Deep oblique · capsule and humerus hidden', '深部斜位 · 隐藏关节囊与肱骨')

# Each numbered leader stores the landmark and the badge in that 560 px crop.
STUDIES = {
    'elbow': (
        ('Right elbow capsule and ligaments', '右肘关节囊与韧带'),
        (
            ('anterior', ('Anterior', '前面'), (
                (1, (282, 247), (154, 213)),
                (2, (357, 179), (426, 149)),
                (3, (261, 348), (141, 389)),
                (4, (303, 359), (411, 390)),
            )),
            ('deep-oblique', DEEP_VIEW, (
                (5, (274, 287), (132, 240)),
                (3, (255, 361), (138, 389)),
                (4, (315, 361), (427, 389)),
            )),
        ),
        (
            ('Joint capsule', '关节囊'), ('Humerus', '肱骨'), ('Radius', '桡骨'),
            ('Ulna', '尺骨'), ('Annular ligament', '桡骨环状韧带'),
        ),
    ),
    'shoulder': (
        ('Right shoulder capsule and labrum', '右肩关节囊与关节盂唇'),
        (
            ('anterior', ('Anterior', '前面'), (
                (1, (257, 332), (139, 364)),
                (2, (200, 259), (110, 281)),
                (3, (402, 351), (493, 393)),
                (4, (462, 210), (485, 139)),
            )),
            ('deep-oblique', DEEP_VIEW, (
                (5, (278, 258), (143, 227)),
                (3, (350, 359), (438, 416)),
                (4, (475, 278), (479, 194)),
            )),
        ),
        (
            ('Joint capsule', '关节囊'), ('Humeral head', '肱骨头'), ('Scapula', '肩胛骨'),
            ('Clavicle', '锁骨'), ('Glenoid labrum', '关节盂唇'),
        ),
    ),
    'ulnar': (
        ('Right ulnar nerve at the elbow', '右尺神经与肘部骨标志'),
        (
            ('posteromedial', ('Posteromedial', '后内侧'), (
                (1, (199, 269), (125, 305)),
                (2, (318, 264), (419, 294)),
                (3, (220, 240), (120, 180)),
            )),
            ('medial', ('Medial', '内侧'), (
                (1, (283, 269), (125, 305)),
                (2, (339, 264), (419, 294)),
                (3, (310, 240), (120, 180)),
            )),
        ),
        (('Medial epicondyle', '肱骨内上髁'), ('Olecranon', '尺骨鹰嘴'), ('Ulnar nerve', '尺神经')),
    ),
}


def plate(study, renders, latin_font, chinese_font):
    title, views, legend = STUDIES[study]
    header = ImageFont.truetype(str(latin_font), 34)
    body = ImageFont.truetype(str(latin_font), 21)
    small = ImageFont.truetype(str(latin_font), 16)
    chinese_header = ImageFont.truetype(str(chinese_font), 26)
    chinese_body = ImageFont.truetype(str(chinese_font), 19)

    canvas = Image.new('RGB', (1168, 804), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 16), title[0], font=header, fill=INK)
    draw.text((20, 61), title[1], font=chinese_header, fill=INK)
    for column, (view, (english, chinese), leaders) in enumerate(views):
        x, y = 12 + 584 * column, 144
        draw.text((x, y - 51), english, font=body, fill=INK)
        draw.text((x, y - 26), chinese, font=chinese_body, fill=INK)
        path = renders / f'{study}-{view}.png'
        with Image.open(path) as image:
            if image.size != (560, 560):
                raise ValueError(f'Wrong landmark crop size: {path}')
            canvas.paste(image.convert('RGB'), (x, y))
        for number, landmark, badge in leaders:
            px, py = x + landmark[0], y + landmark[1]
            bx, by = x + badge[0], y + badge[1]
            draw.line((bx, by, px, py), fill=INK, width=3)
            draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill='white', outline=INK, width=2)
            draw.ellipse((bx - 13, by - 13, bx + 13, by + 13), fill=INK, outline='white', width=2)
            draw.text((bx, by), str(number), font=small, fill='white', anchor='mm')
    for number, (english, chinese) in enumerate(legend, 1):
        x = 12 + (number - 1) * (230 if len(legend) > 3 else 383)
        draw.text((x, 716), f'{number}  {english}', font=body, fill=INK)
        draw.text((x, 744), chinese, font=chinese_body, fill=INK)
    draw.text((12, 780), 'Z-Anatomy / BodyParts3D · CC BY-SA 4.0 · Illustrative colors', font=small, fill=INK)
    buffer = BytesIO()
    canvas.save(buffer, format='WEBP', quality=90, method=6)
    return buffer.getvalue()


def checked_outputs(renders, latin_font, chinese_font, verify):
    encoded = {
        f'{study}-teaching.webp': plate(study, renders, latin_font, chinese_font)
        for study in STUDIES
    }
    if verify:
        assessed = json.loads((HERE / 'campaign-assessments.json').read_text())['assessments']
        expected = {
            Path(view['path']).name: (view['bytes'], view['sha256'])
            for row in assessed for view in row['views']
            if view['path'] == row['teachingView']
        }
        actual = {name: (len(data), sha256(data).hexdigest()) for name, data in encoded.items()}
        for name in sorted(expected.keys() | actual.keys()):
            if expected.get(name) != actual.get(name):
                raise ValueError(f'Teaching plate identity mismatch: {name}')
    return encoded


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Directory from render.py')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--latin-font', type=Path, default=LATIN_FONT)
    parser.add_argument('--chinese-font', type=Path, default=CHINESE_FONT)
    parser.add_argument('--verify', action='store_true', help='Require the retained assessment identities')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f'Output directory must be new: {args.out}')
    outputs = checked_outputs(args.input, args.latin_font, args.chinese_font, args.verify)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items():
        (args.out / name).write_bytes(data)
        print(f'{sha256(data).hexdigest()}  {name}')
