"""Build unlabelled fallback layers and their numbered answer plates."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


LAYERS = ("jaw", "floor", "masseter", "duct")
# Pixel locations inspected against 960 by 720 renders from the bound camera.
ANSWERS = {
    "location": ("floor", (
        (1, (69, 229), (172, 211)),
        (1, (895, 269), (799, 236)),
        (2, (258, 423), (333, 435)),
        (2, (719, 466), (629, 455)),
        (3, (377, 643), (412, 569)),
        (3, (587, 643), (523, 572)),
    )),
    "duct-course": ("masseter", (
        (1, (865, 183), (706, 221)),
        (2, (269, 223), (492, 295)),
        (3, (832, 513), (529, 439)),
    )),
}


def base_image(path):
    with Image.open(path) as render:
        plate = Image.new("RGBA", render.size, "#23303c")
        plate.alpha_composite(render.convert("RGBA"))
    return plate.convert("RGB")


def add_number(plate, number, label, feature):
    draw = ImageDraw.Draw(plate)
    ink, light = "#102231", "#f8f8f6"
    draw.line((label, feature), fill=ink, width=8)
    draw.line((label, feature), fill=light, width=3)
    x, y = feature
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=light, outline=ink, width=2)
    x, y = label
    draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=ink, outline=light, width=3)
    draw.text(label, str(number), font=ImageFont.load_default(size=29), fill=light, anchor="mm")


def save(plate, output, name):
    plate.save(output / f"salivary-{name}.webp", format="WEBP", quality=91, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for layer in LAYERS:
        save(base_image(args.renders / f"{layer}.png"), args.out, layer)
    for task, (layer, markers) in ANSWERS.items():
        plate = base_image(args.renders / f"{layer}.png")
        for marker in markers:
            add_number(plate, *marker)
        save(plate, args.out, task + "-answer")


if __name__ == "__main__":
    main()
