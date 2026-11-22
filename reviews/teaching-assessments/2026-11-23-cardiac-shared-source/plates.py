"""Compose the matched views from the exact-file render receipt."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROWS = {
    "static": (
        ("overview", "Whole heart · end diastole"),
        ("detail", "Aortic arch and pulmonary vessels · anterior"),
        ("reverse", "Aortic arch and pulmonary vessels · posterior, neutral"),
    ),
    "motion": (
        ("rest", "Reference pose · 0.000 s"),
        ("peak", "Peak sampled shortening · 0.333 s"),
        ("reverse", "Peak pose · reverse, neutral"),
    ),
}
STEMS = {"static": "great-vessels", "motion": "wall-motion"}
TITLES = {
    "static": "Distinguish the pulmonary trunk from the aortic arch",
    "motion": "Compare the moving ventricular wall with the fixed aorta",
}
CAPTIONS = {
    "static": "The pulmonary trunk lies in front of the arch in this procedural model. Vessel joins are schematic.",
    "motion": "Follow the lower ventricular tip. The aorta stays fixed through the authored cycle.",
}
REVISIONS = ("Original", "Updated")
BACKGROUND = "#172027"
TEXT = "#f0f4f6"
LABEL = "#c9d3da"


def write(image, path):
    image.save(path, format="WEBP", quality=86, method=6)
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "width": image.width,
        "height": image.height,
    }


def fonts():
    return {key: ImageFont.load_default(size=size) for key, size in
            (("title", 24), ("header", 20), ("row", 17), ("caption", 16))}


def matched(task, inputs, folder, out, sizes):
    images = {}
    for revision in REVISIONS:
        for row in inputs["views"][revision.lower()]:
            path = folder / row["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"Image identity changed for {path.name}")
            images[path.stem] = Image.open(path).convert("RGB")

    gap, margin, cell = 14, 24, 340
    row_height = cell + 40
    canvas = Image.new("RGB", (margin * 2 + 2 * cell + gap, 100 + row_height * len(ROWS[task]) + 44), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 21), TITLES[task], font=sizes["title"], fill=TEXT)
    for column, revision in enumerate(REVISIONS):
        x = margin + column * (cell + gap)
        draw.text((x, 64), revision, font=sizes["header"], fill=TEXT)
    for index, (key, title) in enumerate(ROWS[task]):
        y = 99 + index * row_height
        draw.text((margin, y), title, font=sizes["row"], fill=LABEL)
        for column, revision in enumerate(REVISIONS):
            x = margin + column * (cell + gap)
            source = images[f"{task}-{revision.lower()}-{key}"]
            canvas.paste(source.resize((cell, cell), Image.Resampling.LANCZOS), (x, y + 26))
    draw.text((margin, canvas.height - 33), CAPTIONS[task], font=sizes["caption"], fill=LABEL)
    stem = STEMS[task]
    plate = write(canvas, out / f"{stem}.webp")

    if task == "static":
        poster = images["static-updated-overview"]
    else:
        poster = Image.new("RGB", (660, 353), BACKGROUND)
        draw = ImageDraw.Draw(poster)
        for column, (key, label) in enumerate((("rest", "Reference pose"), ("peak", "Peak sampled shortening"))):
            x = column * 330
            image = images[f"motion-updated-{key}"]
            poster.paste(image.resize((330, 330), Image.Resampling.LANCZOS), (x, 0))
            draw.text((x + 16, 333), label, font=sizes["caption"], fill=LABEL)
    return {"match": plate, "poster": write(poster, out / f"{stem}-poster.webp")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("renders", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = json.loads((args.renders / "checks.json").read_text())
    sizes = fonts()
    rows = {task: matched(task, inputs["render"][task], args.renders, args.output, sizes) for task in STEMS}
    (args.output / "plates.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
