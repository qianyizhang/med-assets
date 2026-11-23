"""Compose views from the Blender receipt. Requires Pillow."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "sources/fonts/dejavu/DejaVuSans.ttf"
TITLES = {
    "main": "Imported whole view",
    "reverse": "Alternate direction · neutral",
    "detail": "Regional detail · neutral",
    "inspection": "Inspection · four structures hidden",
    "whole": "Capsule and vessels visible",
    "tissue": "Capsule and vessels hidden · neutral",
    "tinted": "Same view · source tissue meshes highlighted",
}
PADDING = 14
HEADER = 62
SIZE = 640


def compose(input_dir, row, names, destination, teaching=False):
    by_name = {view["file"].split("-", 1)[1].removesuffix(".png"): view for view in row["views"]}
    footer = 70 if teaching else 0
    height = HEADER + SIZE + PADDING + footer
    plate = Image.new("RGB", (len(names) * (SIZE + PADDING) + PADDING, height), "#f4f3ef")
    draw = ImageDraw.Draw(plate)
    font = ImageFont.truetype(FONT, size=25)
    small = ImageFont.truetype(FONT, size=21)
    offsets = {}
    for index, name in enumerate(names):
        view = by_name[name]
        file = input_dir / view["file"]
        data = file.read_bytes()
        if hashlib.sha256(data).hexdigest() != view["sha256"] or len(data) != view["bytes"]:
            raise ValueError(f"Wrong view bytes: {file}")
        offset = PADDING + index * (SIZE + PADDING)
        offsets[name] = offset
        title = TITLES[name]
        if name == "detail" and "inspection" in names:
            title = "Exterior · same camera as inspection"
        draw.text((offset, 16), title, font=font, fill="#202020")
        with Image.open(file) as decoded:
            if decoded.size != (SIZE, SIZE):
                raise ValueError(f"Wrong view dimensions: {file}")
            plate.paste(decoded.convert("RGB"), (offset, HEADER))
    if teaching:
        x = offsets["tinted"]
        # The arrow tips are on the colored mesh interiors in the pinned camera.
        for label, start, end in (
            ("Medulla", (300, 157), (277, 272)),
            ("Follicles", (60, 478), (191, 347)),
            ("Paracortex", (388, 501), (303, 379)),
        ):
            start_pos = (x + start[0], HEADER + start[1])
            end_pos = (x + end[0], HEADER + end[1])
            draw.line((start_pos, end_pos), width=3, fill="#ffffff")
            draw.ellipse((end_pos[0] - 4, end_pos[1] - 4, end_pos[0] + 4, end_pos[1] + 4), fill="#ffffff")
            draw.text(start_pos, label, font=font, fill="#ffffff", stroke_width=2, stroke_fill="#252525")
        draw.text((PADDING, HEADER + SIZE + 14),
                  "The same HRA lymph node in both panels. Colors identify source-named meshes.",
                  font=small, fill="#202020")
        draw.text((PADDING, HEADER + SIZE + 43),
                  "Hidden parts: capsule, afferent and efferent vessel meshes, and the disputed vascular network.",
                  font=small, fill="#202020")
    plate.save(destination, "WEBP", quality=91, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("render_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    rows = json.loads((args.render_dir / "render.json").read_text())["rows"]
    for row in rows:
        number = row["id"]
        names = ["main", "reverse"]
        if any(view["file"].endswith("-detail.png") for view in row["views"]) and number != "A10":
            names.append("detail")
        compose(args.render_dir, row, names, args.output / f"{number}-review.webp")
        if number == "A03":
            compose(args.render_dir, row, ["whole", "tinted"], args.output / "A03-lymph-node-layers.webp", True)
        if number == "A10":
            compose(args.render_dir, row, ["detail", "inspection"], args.output / "A10-knee-depth.webp")


if __name__ == "__main__":
    main()
