"""Compose captioned lymph-node plates and compare the matched clean imports."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[4]
FONT = ROOT / "experiments/dental-video-treatments/fonts/DejaVuSans.ttf"
PAPER = "#f5f2e9"
INK = "#17242c"
DARK = "#242830"
GOLD = "#f6df9b"
WIDTH = 1328
BORDER = 20
CROP = (0, 125, 650, 521)
PRIMARY = "primary"
REVERSE = "reverse"


def checked_image(scratch, view):
    path = scratch / view["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != view["sha256"]:
        raise ValueError(f"Wrong image bytes: {path}")
    with Image.open(path) as image:
        return image.convert("RGBA")


def framed(image, size, contour=None):
    panel = Image.new("RGBA", image.size, DARK)
    panel.alpha_composite(image)
    if contour is not None:
        alpha = contour.getchannel("A").point(lambda x: 255 if x >= 128 else 0)
        line = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(5)), alpha.filter(ImageFilter.MinFilter(5)))
        panel.paste(GOLD, (0, 0), line)
    return panel.crop(CROP).convert("RGB").resize(size, Image.Resampling.LANCZOS)


def wrapped(draw, message, font, width):
    lines = [""]
    for word in message.split():
        line = f"{lines[-1]} {word}".strip()
        if draw.textlength(line, font=font) > width:
            lines.append(word)
        else:
            lines[-1] = line
    return lines


def plate(title, rows, caption, notes, images):
    title_font = ImageFont.truetype(FONT, 41)
    label_font = ImageFont.truetype(FONT, 23)
    body = ImageFont.truetype(FONT, 23)
    canvas = Image.new("RGB", (WIDTH, 1220), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw.text((BORDER, 18), title, font=title_font, fill=INK)
    y = 78
    for row in rows:
        width = (WIDTH - BORDER * (len(row) + 1)) // len(row)
        height = round(width * (CROP[3] - CROP[1]) / (CROP[2] - CROP[0]))
        for i, (identifier, label, trace, pointers) in enumerate(row):
            x = BORDER + i * (width + BORDER)
            if draw.textlength(label, font=label_font) > width:
                raise ValueError(f"Panel caption is too wide: {label}")
            draw.text((x, y), label, font=label_font, fill=INK)
            image_top = y + 32
            canvas.paste(framed(images[identifier], (width, height), images.get(trace)), (x, image_top))
            for number, (px, py, tx, ty) in pointers.items():
                points = tuple(value for pos in ((px, py), (tx, ty))
                               for value in (x + pos[0] * width, image_top + pos[1] * height))
                sx, sy, dx, dy = points
                draw.line(points, fill=DARK, width=6)
                draw.line(points, fill=GOLD, width=2)
                draw.ellipse((dx - 4, dy - 4, dx + 4, dy + 4), fill=GOLD)
                draw.ellipse((sx - 14, sy - 14, sx + 14, sy + 14), fill=GOLD, outline=DARK, width=2)
                draw.text((sx, sy), number, font=body, fill=INK, anchor="mm")
        y += height + 48
    for paragraph in (*notes, caption):
        for line in wrapped(draw, paragraph, body, WIDTH - 2 * BORDER):
            draw.text((BORDER, y), line, font=body, fill=INK)
            y += 30
        y += 6
    if y > canvas.height:
        raise ValueError("Plate contents exceed the page")
    return canvas.crop((0, 0, WIDTH, y + 10))


def image_row(prefix, neutral=False, contour=False, pointers=False):
    finish = "neutral-" if neutral else ""
    capsule = f"candidate-{prefix}-{finish}capsule.png"
    regions = f"candidate-{prefix}-{finish}regions.png"
    angle = "First oblique" if prefix == PRIMARY else "Alternate oblique"
    labels = {"1": (.30, .19, .145, .43), "2": (.15, .78, .28, .59),
              "3": (.69, .85, .47, .65), "4": (.86, .20, .68, .42)} if pointers else {}
    first = {"1": labels["1"]} if labels else {}
    inner = {k: v for k, v in labels.items() if k != "1"}
    return (
        (capsule, f"{angle} · capsule", None, first),
        (regions, f"{angle} · named tissue regions", capsule if contour else None, inner),
    )


def check_matches(models, images):
    source, candidate = (models[key] for key in ("source", "candidate"))
    before = {shot["file"].removeprefix("source-"): shot for shot in source["views"]}
    after = {shot["file"].removeprefix("candidate-"): shot for shot in candidate["views"]}
    results = {}
    for view in ("primary-capsule.png", "primary-regions.png", "reverse-capsule.png", "reverse-regions.png"):
        a, b = before[view], after[view]
        for key in ("visible", "finish", "cameraM", "targetM", "orthoScaleM"):
            if a[key] != b[key]:
                raise ValueError(f"Mismatched source/candidate {key} for {view}")
        delta = ImageChops.difference(images[a["file"]], images[b["file"]])
        extrema = delta.getextrema()
        if any(high != 0 for _, high in extrema):
            raise ValueError(f"Selected source and candidate decoded pixels differ for {view}: {extrema}")
        results[view] = {"sameDecodedRGBA": True, "source": a["sha256"], "candidate": b["sha256"]}
    for name, transform in candidate["world_matrices"].items():
        if source["world_matrices"][name] != transform or source["triangles"][name] != candidate["triangles"][name]:
            raise ValueError(f"Clean import changed world transform or triangle count: {name}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    owner = json.loads((args.scratch / "render.json").read_text())
    models = owner["models"]
    images = {view["file"]: checked_image(args.scratch, view)
              for model in models.values() for view in model["views"]}
    comparisons = check_matches(models, images)
    labels = ("1  Capsule outline.   2  Blue follicles near the periphery.   3  Green paracortex.   4  Pale medulla.",)
    files = {
        "tissue-layers.webp": plate(
            "Lymph node capsule and named tissue regions",
            [image_row(PRIMARY, contour=True, pointers=True), image_row(REVERSE, contour=True)],
            "The gold line projects the capsule outline onto the same view. Atlas colors identify selections. The panels show spatial position and leave tissue contacts and flow unverified.",
            labels, images),
        "matched-source.webp": plate(
            "Vessel geometry omitted from the tissue study",
            [[("source-primary-all.png", "Original · all source meshes", None, {"1": (.37, .15, .48, .43)}),
              ("candidate-primary-capsule.png", "Derivative · capsule only", None, {"2": (.64, .28, .55, .39)}),
              ("candidate-primary-regions.png", "Derivative · tissue regions", "candidate-primary-capsule.png", {})]],
            "Same camera and scale. The capsule and tissue selections retain their original shapes, materials and positions.",
            ("1  Projections include vessel meshes and the unresolved source network omitted from the derivative.",
             "2  A source capsule aperture remains visible. The study leaves its identity unassigned."), images),
        "neutral-form.webp": plate(
            "Neutral inspection of the capsule and interior",
            [image_row(PRIMARY, neutral=True), image_row(REVERSE, neutral=True)],
            "The capsule apertures and the irregular medullary surface, lobules and deep clefts remain source form. Their exact anatomical detail is unverified.",
            (), images),
        "named-selections.webp": plate(
            "Recognize each named tissue region",
            [[("candidate-primary-follicles.png", "Follicles", None, {}),
              ("candidate-primary-paracortex.png", "Paracortex", None, {}),
              ("candidate-primary-medulla.png", "Medulla", None, {})]],
            "Each tissue is shown at the same camera and scale. Switch named groups to check its position against the capsule view and the other tissues.",
            (), images),
    }
    args.output.mkdir(parents=True, exist_ok=False)
    for name, page in files.items():
        path = args.output / name
        page.save(path, "WEBP", quality=94, method=6)
        comparisons[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "bytes": path.stat().st_size, "width": page.width, "height": page.height}
    (args.output / "comparison.json").write_text(json.dumps(comparisons, indent=2) + "\n")


if __name__ == "__main__":
    main()
