"""Build exact-source teaching and matched trial plates from the clean imports."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


STATES = {
    "complete": "Anterior · complete cutaway",
    "wall": "Anterior · isolate the wall",
    "branch": "Bifurcation detail · neutral material",
    "context": "Oblique · external bands",
}


def signature(path):
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def read(path, expected):
    if signature(path)["sha256"] != expected["sha256"]:
        raise ValueError(f"Wrong matched render {path}")
    return Image.open(path).convert("RGB")


def write(image, path):
    image.save(path, format="WEBP", quality=85, method=6)
    return {**signature(path), "width": image.width, "height": image.height}


def pixel_differences(before, after):
    difference = ImageChops.difference(before, after)
    return {"maxChannelDifference": max(high for _, high in difference.getextrema()),
            "changedPixels": sum(pixel != (0, 0, 0) for pixel in difference.getdata()),
            "pixels": before.width * before.height}


def panel(canvas, draw, image, x, y, size, label, font):
    draw.text((x, y), label, fill="#eaf0f3", font=font)
    canvas.paste(image.resize((size, size), Image.Resampling.LANCZOS), (x, y + 25))


def make_teaching(images, branch_guides, out):
    page = Image.new("RGB", (954, 518), "#172027")
    draw = ImageDraw.Draw(page)
    title = ImageFont.load_default(size=25)
    text = ImageFont.load_default(size=17)
    draw.text((18, 16), "Trace the exposed tracheal channel into the left main bronchus", fill="#f2f6f8", font=title)
    for index, name in enumerate(("wall", "branch", "context")):
        x = 18 + 310 * index
        panel(page, draw, images[name], x, 65, 298, STATES[name], text)
    x, y, size = 328, 90, 298
    # The labels follow One Breath's retained lateralized port coordinates.
    left = branch_guides["leftMain"]
    right = branch_guides["rightMain"]
    for point, caption, label, alignment in (
        (left, "Left main", (x + 279, y + 267), "ra"),
        (right, "Right main", (x + 14, y + 220), "la"),
    ):
        cx, cy = x + size * point[0], y + size * point[1]
        draw.line((cx, cy, cx, label[1] - 5), fill="#e9bf7a", width=2)
        draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill="#e9bf7a")
        draw.text(label, caption, font=text, fill="#ffdfaa", anchor=alignment)
    draw.text((18, 417), "At the fork, follow the branch marked Left main. The patient’s left appears on the right of the panel.",
              font=text, fill="#e0ecf0")
    draw.text((18, 450), "The anterior opening and inner wall are authored. The lateral view shows the retained illustrative bands.",
              font=text, fill="#e0ecf0")
    return write(page, out / "left-main-teaching.webp")


def make_comparison(before, after, out):
    page = Image.new("RGB", (728, 1145), "#172027")
    draw = ImageDraw.Draw(page)
    title = ImageFont.load_default(size=23)
    text = ImageFont.load_default(size=17)
    draw.text((18, 15), "Exact V7 and packed-normal size trial", fill="#f2f6f8", font=title)
    draw.text((18, 52), "V7 cutaway", fill="#f2f6f8", font=text)
    draw.text((373, 52), "Size trial", fill="#f2f6f8", font=text)
    for index, name in enumerate(("complete", "branch", "context")):
        y = 83 + 345 * index
        panel(page, draw, before[name], 18, y, 315, STATES[name], text)
        panel(page, draw, after[name], 373, y, 315, STATES[name], text)
    return write(page, out / "left-main-encoding-comparison.webp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("render_folder", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = json.loads((args.render_folder / "render.json").read_text())
    images = {}
    for tag, entries in report["views"].items():
        images[tag] = {entry["file"].removeprefix(f"{tag}-").removesuffix(".png"):
                       read(args.render_folder / entry["file"], entry) for entry in entries}
    branch, = [entry for entry in report["views"]["original"] if entry["file"] == "original-branch.png"]
    proof = {
        "teaching": make_teaching(images["original"], branch["projectedLessonGuides"], args.output),
        "comparison": make_comparison(images["original"], images["trial"], args.output),
        "pairedColourDifferences": {label: pixel_differences(images["original"][label], images["trial"][label])
                                   for label in STATES},
    }
    (args.output / "plates.json").write_text(json.dumps(proof, indent=2) + "\n")


if __name__ == "__main__":
    main()
