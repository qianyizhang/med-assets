"""Compose annotated teaching plates from pinned campaign views."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONT = ROOT / "sources/fonts/dejavu/DejaVuSans.ttf"
WIDTH = 1328
GUTTER = 20
PAGE = "#f5f2e9"
INK = "#17242c"
ACCENT = "#f8dd85"


def get_view(root, spec, bindings):
    path = spec["image"]
    if path.startswith("@"):
        name = path[1:]
        candidate, expected = bindings[name]
    else:
        candidate = root / path
        expected = spec["sha256"]
    data = candidate.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Wrong image bytes: {candidate}")
    with Image.open(candidate) as decoded:
        image = decoded.convert("RGB")
    crop = spec.get("crop")
    if crop:
        left, top, right, bottom = crop
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise ValueError(f"Bad crop in {path}")
        image = image.crop(crop)
    return image


def wrap(draw, message, width, font):
    lines = [""]
    for word in message.split():
        trial = f"{lines[-1]} {word}".strip()
        if draw.textlength(trial, font=font) > width:
            lines.append(word)
        else:
            lines[-1] = trial
    return lines


def add_token(draw, center, label, size, font):
    x, y = center
    radius = size / 2
    draw.ellipse((x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3), fill=INK)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=ACCENT)
    draw.text((x, y), label, anchor="mm", fill=INK, font=font)


def compose(spec, root, bindings):
    panels = spec["panels"]
    width = (WIDTH - (len(panels) + 1) * GUTTER) // len(panels)
    height = min(width, 515)
    card = Image.new("RGB", (WIDTH, 930), PAGE)
    draw = ImageDraw.Draw(card)
    title = ImageFont.truetype(FONT, 41)
    subhead = ImageFont.truetype(FONT, 24)
    body = ImageFont.truetype(FONT, 24)
    token = ImageFont.truetype(FONT, 21)
    draw.text((GUTTER, 20), spec["title"], font=title, fill=INK)
    panel_top = 104
    for i, panel in enumerate(panels):
        left = GUTTER + i * (width + GUTTER)
        label_font = subhead
        if draw.textlength(panel["label"], font=label_font) > width:
            label_font = ImageFont.truetype(FONT, 20)
        if draw.textlength(panel["label"], font=label_font) > width:
            raise ValueError(f"Panel heading is too wide: {panel['label']}")
        draw.text((left, 73), panel["label"], font=label_font, fill=INK)
        image = get_view(root, panel, bindings)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        x = left + (width - image.width) // 2
        y = panel_top + (height - image.height) // 2
        draw.rectangle((left, panel_top, left + width, panel_top + height), fill="#303030")
        card.paste(image, (x, y))
        for number, proportions in panel.get("marks", {}).items():
            px, py, *tail = proportions
            tx, ty = tail or (px, py)
            if not all(0 <= c <= 100 for c in (px, py, tx, ty)):
                raise ValueError(f"Marker outside original image: {panel['image']}")
            tx = x + tx * image.width / 100
            ty = y + ty * image.height / 100
            px = x + px * image.width / 100
            py = y + py * image.height / 100
            if tail:
                draw.line((px, py, tx, ty), fill=INK, width=6)
                draw.line((px, py, tx, ty), fill=ACCENT, width=2)
                draw.ellipse((tx - 4, ty - 4, tx + 4, ty + 4), fill=ACCENT)
            add_token(draw, (px, py), number, 27, token)
    y = panel_top + height + 21
    for number, note in enumerate(spec["notes"], 1):
        add_token(draw, (GUTTER + 14, y + 13), str(number), 26, token)
        for line in wrap(draw, note, WIDTH - 2 * GUTTER - 45, body):
            draw.text((GUTTER + 43, y), line, font=body, fill=INK)
            y += 30
        y += 10
    for line in wrap(draw, spec["scope"], WIDTH - 2 * GUTTER, body):
        draw.text((GUTTER, y), line, font=body, fill=INK)
        y += 30
    if y + 17 > card.height:
        raise ValueError(f"Plate overflow: {spec['title']}")
    return card.crop((0, 0, WIDTH, y + 17))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--asset", action="append")
    args = parser.parse_args()
    receipt = json.loads((args.replay / "selection-render.json").read_text())
    bindings = {item["file"]: (args.replay / item["file"], item["sha256"])
                for data in receipt["assets"].values() for item in data["views"]}
    trials = json.loads((args.trials / "trial-render.json").read_text())
    for row in trials["assets"].values():
        for data in row.values():
            for item in data["views"]:
                bindings[item["file"]] = (args.trials / item["file"], item["sha256"])
    specs = json.loads((HERE / "plate-layouts.json").read_text())
    planned = {key: specs[key] for key in (args.asset or specs)}
    pages = {key: compose(spec, ROOT, bindings) for key, spec in planned.items()}
    args.output.mkdir(parents=True, exist_ok=False)
    for key, page in pages.items():
        page.save(args.output / f"{key}.webp", format="WEBP", quality=94, method=6)


if __name__ == "__main__":
    main()
