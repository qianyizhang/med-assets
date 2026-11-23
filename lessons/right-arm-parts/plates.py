"""Encode the four unlabeled practice views and two labeled answer plates."""

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
DELIVERY = Path(__file__).resolve().parents[2] / 'sites/anatomy-gallery/app/src/content/gallery/part-images'
INK = '#19303a'
PAPER = '#f5f2ed'
WIDTH = 640
HEIGHT = 480
GUTTER = 10
HEADER = 48

PRACTICE = ('elbow-capsule', 'elbow-nerve', 'shoulder-glenoid', 'shoulder-cuff')
EPICONDYLE = ('Medial epicondyle', 'medial_epicondyle', (14, 298))
OLECRANON = ('Olecranon', 'olecranon', (491, 160))
# Answer leaders join the rendered landmark pixel and an offset label origin.
ANSWERS = {
    'elbow': (
        ('elbow-capsule', 'Capsule · posteromedial', (
            EPICONDYLE, OLECRANON, ('Joint capsule', (392, 263), (423, 318)),
        )),
        ('elbow-nerve', 'Nerve · posteromedial', (
            EPICONDYLE, OLECRANON, ('Ulnar nerve', 'nerve', (38, 128)),
        )),
    ),
    'shoulder': (
        ('shoulder-glenoid', 'Socket · posterolateral', (
            ('Glenoid', (421, 192), (494, 116)),
            ('Labrum', (433, 211), (492, 261)),
        )),
        ('shoulder-posterior', 'Cuff · posterior', (
            ('Supraspinatus', '1', (109, 52)),
            ('Scapular spine', 'S', (14, 110)),
            ('Infraspinatus', '2', (18, 359)),
            ('Teres minor', '3', (420, 379)),
        )),
        ('shoulder-anterior', 'Cuff · anterior', (
            ('Subscapularis', '4', (361, 425)),
        )),
    ),
}


def load_view(renders, name):
    with Image.open(renders / f'{name}.png') as image:
        if image.size != (WIDTH, HEIGHT):
            raise ValueError(f'Unexpected dimensions for {name}: {image.size}')
        return image.convert('RGB')


def annotate(draw, label, point, origin, font):
    x, y = origin
    left, top, right, bottom = draw.textbbox((x, y), label, font=font, anchor='lt')
    box = left - 7, top - 6, right + 7, bottom + 6
    px, py = point
    edge = min(max(px, box[0]), box[2]), min(max(py, box[1]), box[3])
    draw.line((point, edge), fill=PAPER, width=6)
    draw.line((point, edge), fill=INK, width=3)
    draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=PAPER, outline=INK, width=2)
    draw.rounded_rectangle(box, radius=6, fill=PAPER, outline=INK, width=2)
    draw.text((x, y), label, fill=INK, font=font, anchor='lt')


def answer(views, renders, projected, font):
    width = WIDTH * len(views) + GUTTER * (len(views) - 1)
    result = Image.new('RGB', (width, HEIGHT + HEADER), PAPER)
    header = ImageDraw.Draw(result)
    for index, (key, title, labels) in enumerate(views):
        offset = index * (WIDTH + GUTTER)
        header.text((offset + 15, 12), title, fill=INK, font=font, anchor='lt')
        picture = load_view(renders, key)
        draw = ImageDraw.Draw(picture)
        anchors = projected['elbow-nerve' if key == 'elbow-capsule' else key]
        for label, landmark, origin in labels:
            point = anchors[landmark] if isinstance(landmark, str) else landmark
            annotate(draw, label, point, origin, font)
        result.paste(picture, (offset, HEADER))
    return result


def encode(renders, out, font_path, *, verify=False):
    font = ImageFont.truetype(str(font_path), 29)
    projected = json.loads((renders / 'projections.json').read_text())
    images = {key: load_view(renders, key) for key in PRACTICE}
    images.update({f'{key}-answer': answer(views, renders, projected, font) for key, views in ANSWERS.items()})
    outputs = {}
    for key, image in images.items():
        buffer = BytesIO()
        image.save(buffer, format='WEBP', quality=90, method=6)
        name = f'arm-{key}.webp'
        data = buffer.getvalue()
        if verify and data != (DELIVERY / name).read_bytes():
            raise ValueError(f'Plate differs from the retained Gallery delivery: {name}')
        outputs[name] = data
    out.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (out / name).write_bytes(data)
        print(f'{hashlib.sha256(data).hexdigest()}  {len(data):7}  {name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--font', type=Path, default=FONT)
    parser.add_argument('--verify', action='store_true', help='Compare all six plates to the retained Gallery files')
    arguments = parser.parse_args()
    encode(arguments.renders, arguments.out, arguments.font, verify=arguments.verify)
