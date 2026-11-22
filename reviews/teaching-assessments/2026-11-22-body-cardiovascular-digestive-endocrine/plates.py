"""Build compact inspection plates from the pinned fresh render receipt."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def identity(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(input_dir, output, views, headings):
    columns = []
    for view in views:
        path = input_dir / view["file"]
        if identity(path) != view["sha256"] or path.stat().st_size != view["bytes"]:
            raise ValueError(f"View identity mismatch: {path}")
        with Image.open(path) as decoded:
            columns.append(decoded.convert("RGB"))

    font = ImageFont.truetype(
        "experiments/dental-video-treatments/fonts/DejaVuSans.ttf", size=26
    )
    width, height = columns[0].size
    gap = 14
    plate = Image.new("RGB", (len(columns) * (width + gap) + gap, height + 66), "#f3f2ef")
    draw = ImageDraw.Draw(plate)
    for index, (column, label) in enumerate(zip(columns, headings, strict=True)):
        x = gap + index * (width + gap)
        draw.text((x, 13), label, font=font, fill="#222222")
        plate.paste(column, (x, 54))
    plate.save(output, lossless=True, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = json.loads((args.input / "render.json").read_text())["rows"]
    args.output.mkdir(exist_ok=False)
    for row in rows:
        number = row["id"]
        compose(args.input, args.output / f"{number}-paired.webp", row["views"][:2],
                ("Import overview", "Alternate view · neutral"))
        if number in {"12", "17"}:
            compose(args.input, args.output / f"{number}-isolation.webp", row["views"][2:5],
                    ("All parts visible", "Source exterior alone", "Authored teaching parts alone"))
        if number == "01":
            compose(args.input, args.output / "01-heart-lung.webp", row["views"][2:3],
                    ("Workshop thorax crop",))
        if number == "06":
            compose(args.input, args.output / "06-motion.webp", [row["views"][0], row["views"][2]],
                    ("Frame 1", "Frame 11"))


if __name__ == "__main__":
    main()
