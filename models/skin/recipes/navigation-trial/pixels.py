"""Measure the rendered outline and assemble the matched skin review plates."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

ANGLES = {"ortho": "Anterior", "iso": "Isometric"}
REPO = Path(__file__).resolve().parents[4]
CROPS = {
    "ortho": {
        "Right wrist and hand": (237, 254, 283, 323),
        "Left wrist and hand": (395, 254, 442, 323),
        "Both ankles, toes and heels": (279, 474, 400, 532),
    },
    "iso": {
        "Right wrist and hand": (244, 218, 296, 299),
        "Left wrist and hand": (356, 278, 404, 362),
        "Both ankles, toes and heels": (273, 422, 386, 518),
    },
}
PHASES = {"original": "Original · r01", "updated": "Updated · navigation trial"}
BACKGROUND = (29, 34, 42)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pair(directory, receipt, key, size):
    for phase in PHASES:
        capture = receipt["captures"][phase]
        record = capture["images"][key]
        if capture["glbSha256"] != receipt[phase]["sha256"]:
            raise ValueError(f"GLB identity mismatch in {phase} capture")
        path = directory / record["file"]
        if digest(path) != record["sha256"]:
            raise ValueError(f"Capture hash mismatch: {path.name}")
        with Image.open(path) as image:
            if image.mode != "RGBA" or image.size != size:
                raise ValueError(f"Expected an RGBA capture at {size}: {path.name}")
            yield image.copy()


def mask_distance(pair):
    original, updated = (np.asarray(item.getchannel("A")) >= 128 for item in pair)
    if not (original & updated).any():
        raise ValueError("No common foreground in paired captures")
    distance = np.maximum(distance_transform_edt(~original) * updated,
                          distance_transform_edt(~updated) * original)
    return distance, original ^ updated


def outline(distance, changed, scale):
    y, x = np.unravel_index(distance.argmax(), distance.shape)
    return {"maxShiftDisplayPx": float(distance[y, x]) / scale,
            "changedSamples": int(changed.sum()),
            "worstXYDisplayPx": [x.item() / scale, y.item() / scale] if distance[y, x] else None}


def text(draw, xy, label, size, fill="white"):
    draw.text(xy, label, fill=fill, font=ImageFont.load_default(size=size))


def overview(pairs, path, width, height):
    page = Image.new("RGB", (width * 2 + 36, (height + 32) * 2 + 83), BACKGROUND)
    draw = ImageDraw.Draw(page)
    text(draw, (12, 10), "BP3D skin envelope · Pinned 680 px teaching views", 25)
    for col, label in enumerate(PHASES.values()):
        text(draw, (12 + col * (width + 12), 46), label, 18)
    for row, (angle, pair) in enumerate(pairs.items()):
        top = 82 + row * (height + 32)
        text(draw, (12, top), ANGLES[angle], 18)
        for col, item in enumerate(pair):
            x, y = 12 + col * (width + 12), top + 27
            page.paste(item, (x, y), item)
            if col == 0:
                for number, (left, upper, right, lower) in enumerate(CROPS[angle].values(), 1):
                    draw.rectangle((x + left, y + upper, x + right, y + lower), outline="#ffd487")
                    text(draw, (x + right + 4, y + upper), str(number), 14, "#ffd487")
    page.save(path, lossless=True, method=6)


def details(pairs, path, scale):
    widths = [max(box[2] - box[0] for box in column) * scale + 24
              for column in zip(*(crops.values() for crops in CROPS.values()), strict=True)]
    row_heights = [max((bounds[3] - bounds[1]) * scale for bounds in CROPS[angle].values())
                   for angle in pairs]
    page = Image.new("RGB", (sum(widths), 47 + sum(108 + 2 * h for h in row_heights)),
                     BACKGROUND)
    draw = ImageDraw.Draw(page)
    text(draw, (12, 10), "Wrist, finger, toe and heel contours · matched neutral crops at 4x", 24)
    top = 47
    for (angle, pair), height in zip(pairs.items(), row_heights, strict=True):
        text(draw, (12, top), ANGLES[angle], 18)
        left = 12
        for column, (region, bounds) in enumerate(CROPS[angle].items()):
            text(draw, (left, top + 24), f"{column + 1}  {region}", 17)
            for row, (image, label) in enumerate(zip(pair, PHASES.values(), strict=True)):
                y = top + 65 + row * (height + 29)
                text(draw, (left, y - 18), label, 14)
                crop = image.crop(tuple(side * scale for side in bounds))
                page.paste(crop, (left, y), crop)
            left += widths[column]
        top += 108 + 2 * height
    page.save(path, lossless=True, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipt_path = args.capture / "comparison.json"
    receipt = json.loads(receipt_path.read_text())
    width, height = receipt["displaySize"]
    scale = receipt["neutralScale"]
    display, neutral, measurements = {}, {}, {}
    for angle in ANGLES:
        display[angle] = tuple(read_pair(args.capture, receipt, f"display-{angle}", (width, height)))
        neutral[angle] = tuple(read_pair(args.capture, receipt, f"neutral-{angle}",
                                         (width * scale, height * scale)))
        distance, changed = mask_distance(neutral[angle])
        measurements[angle] = stats = outline(distance, changed, scale)
        stats["displayResolutionCheck"] = outline(*mask_distance(display[angle]), 1)
        row = receipt["captures"]["original"]["images"][f"display-{angle}"]
        stats["exactPinnedOriginalPngReplay"] = row["sha256"] == receipt["plates"][angle]["originalPngSha256"]
        plate = REPO / f"lessons/body-systems/display/skin-assembly-{angle}.webp"
        if digest(plate) != receipt["plates"][angle]["webpSha256"]:
            raise ValueError(f"Teaching plate hash mismatch: {plate.name}")
        with Image.open(plate) as pinned:
            _, pinned_difference = mask_distance((pinned, display[angle][0]))
        if pinned_difference.any():
            raise ValueError(f"Control foreground differs from the pinned {angle} teaching plate")
        stats["matchesPinnedTeachingMask"] = True
        stats["regions"] = {}
        for region, box in CROPS[angle].items():
            left, top, right, bottom = (side * scale for side in box)
            selection = np.s_[top:bottom, left:right]
            reading = outline(distance[selection], changed[selection], scale)
            point = reading["worstXYDisplayPx"]
            if point:
                reading["worstXYDisplayPx"] = [box[0] + point[0], box[1] + point[1]]
            reading["cropDisplayXYXY"] = box
            stats["regions"][region] = reading
    args.output.mkdir()
    overview_path = args.output / "overview.webp"
    details_path = args.output / "hands-and-feet.webp"
    overview(display, overview_path, width, height)
    details(neutral, details_path, scale)
    (args.output / "pixels.json").write_text(json.dumps({
        "comparisonSha256": digest(receipt_path),
        "evidence": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
                     for path in (overview_path, details_path)},
        "views": measurements,
    }, indent=2) + "\n")
    if max(stats["maxShiftDisplayPx"] for stats in measurements.values()) > 1:
        raise SystemExit("Outline shift exceeds one display pixel. See pixels.json.")


if __name__ == "__main__":
    main()
