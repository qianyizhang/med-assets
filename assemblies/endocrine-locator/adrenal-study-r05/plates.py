"""Compose exact adrenal review figures from the bound PNGs and specimen photograph."""

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from scipy import ndimage as ndi

PAPER, INK, MUTED = "#F6F3EB", "#252A27", "#505951"
TEAL, ORANGE, GRAY = "#12645F", "#B24F25", "#858581"
SPECIMEN_SHA = "42a2ac7c8719f821e60d5cf57e00cbb924cdc99bd13c4073bff6fb73c4368877"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def font(size, serif=False, bold=False):
    mac = Path("/System/Library/Fonts/Supplemental")
    family = "Georgia" if serif else "Arial"
    candidates = [
        str(mac / (family + (" Bold" if bold else "") + ".ttf")),
        "DejaVuSerif.ttf" if serif else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def canvas(size, title, sub):
    image = Image.new("RGB", size, PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((48, 27), title, fill=INK, font=font(42, serif=True))
    draw.text((50, 89), sub, fill=MUTED, font=font(20))
    draw.line((48, 135, size[0] - 48, 135), fill="#A9ABA0", width=1)
    return image, draw


def place(image, src, box, crop, *, gray=False):
    width, height = crop[2] - crop[0], crop[3] - crop[1]
    x, y, w, h = box
    scale = min(w / width, h / height)
    target = src.crop(crop).resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    origin = (x + (w - target.width) // 2, y + (h - target.height) // 2)
    if gray:
        target = Image.merge("RGBA", (*([ImageOps.grayscale(target)] * 3), target.getchannel("A")))
    image.paste(target, origin, target if target.mode == "RGBA" else None)
    return origin, scale


def pair(review, names):
    images = [Image.open(review / (name + ".png")).convert("RGBA") for name in names]
    alpha = ImageChops.lighter(images[0].getchannel("A"), images[1].getchannel("A"))
    return images, alpha.getbbox()


def project(point_mm, view, pose):
    img = next(i for i in view["images"] if i["file"].endswith("-" + pose + ".png"))
    direction = np.array(img["direction"])
    right = np.array([-direction[1], direction[0], 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(direction, right)
    relative = np.array(point_mm) / 1000 - img["camera"]
    ppm = 800 / view["orthographicScale"]
    return np.array([400 + relative @ right * ppm, 320 - relative @ up * ppm])


def side_labels(draw, coordinates, origin, crop, scale):
    for label, point, sign in zip(("L", "R"), coordinates, (-1, 1), strict=True):
        end = np.array(origin) + (point - crop[:2]) * scale
        start = end + (sign * 43, -23)
        draw.line((tuple(start), tuple(end)), fill=INK, width=2)
        draw.ellipse((end[0] - 3, end[1] - 3, end[0] + 3, end[1] + 3), fill=INK)
        draw.text(
            (start[0] + sign * 6, start[1] - 1),
            label,
            fill=INK,
            font=font(19, bold=True),
            anchor="rm" if sign < 0 else "lm",
        )


def overview(review, output, views, geometry):
    image, draw = canvas(
        (1320, 1018),
        "Adrenal glands in their scan frame",
        "Find each gland above and medial to its kidney, then inspect the right inferior rim.",
    )
    draw.text((56, 154), "Original  ·  r04", font=font(28, serif=True), fill=INK)
    draw.text((685, 154), "Updated  ·  r05", font=font(28, serif=True), fill=INK)
    draw.text((53, 212), "Five-part assembly from behind, 20° left and 30° above", font=font(19), fill=MUTED)
    for suffix, top, height in (("", 254, 284), ("-tissue", 641, 278)):
        names = [kind + suffix + "-ortho" for kind in ("original", "updated")]
        panels, crop = pair(review, names)
        for i, (kind, panel) in enumerate(zip(("original", "updated"), panels, strict=True)):
            origin, scale = place(image, panel, (70 + 630 * i, top, 550, height), crop)
            if not suffix:
                coords = [
                    project(
                        geometry["parts"]["adrenal-gland-" + side]["components"][0][
                            "before" if i == 0 else "after"
                        ]["areaCentroidMm"],
                        views[kind],
                        "ortho",
                    )
                    for side in ("left", "right")
                ]
                side_labels(draw, coords, origin, crop, scale)
    draw.line((50, 569, 1270, 569), fill="#B9BBAD")
    draw.text((53, 593), "Right gland, anterolateral close-up", font=font(23, bold=True), fill=INK)
    draw.text(
        (56, 953),
        "One light and camera rig per pair. The gland colors are illustrative.",
        fill=MUTED,
        font=font(18),
    )
    image.save(output / "comparison.jpg", quality=94, subsampling=0)


def specimen_plate(review, photo_path, output):
    image, draw = canvas(
        (1320, 610),
        "The turn of the capsule",
        "Compare the broad face, curled lower margin and size of the reflected highlights.",
    )
    for x, label in ((49, "Gross specimen"), (673, "Reimported teaching exterior")):
        draw.text((x, 159), label, font=font(25, serif=True), fill=INK)
    with Image.open(photo_path) as photo:
        place(image, photo, (50, 208, 598, 287), (1440, 50, 2225, 735))
    with Image.open(review / "updated-tissue-ortho.png") as model:
        place(image, model, (680, 208, 580, 287), model.getbbox())
    draw.text((51, 515), "Right posterior surface, different individual.", fill=INK, font=font(18))
    draw.text((51, 547), "Mikael Häggström, MD · autopsy photograph · CC0", fill=MUTED, font=font(17))
    draw.text((672, 515), "Right anterolateral surface, s1233.", fill=INK, font=font(18))
    draw.text(
        (672, 547), "The traced case defines its contour. The finish is interpreted.", fill=MUTED, font=font(17)
    )
    image.save(output / "specimen-comparison.jpg", quality=94, subsampling=0)


def grayscale(review, output, views, geometry):
    image, draw = canvas(
        (1320, 606),
        "Locate both glands in grayscale",
        "The posterior-oblique view separates the left gland from the pancreatic silhouette.",
    )
    for i, (key, label) in enumerate(
        (("updated", "Teaching view"), ("updated-posterior", "Straight posterior"))
    ):
        draw.text((55 + 640 * i, 158), label, font=font(24, serif=True), fill=INK)
        with Image.open(review / (key + "-ortho.png")) as src:
            crop = src.getbbox()
            origin, scale = place(image, src, (78 + 640 * i, 215, 510, 316), crop, gray=True)
        coords = [
            project(
                geometry["parts"]["adrenal-gland-" + side]["caseReference"]["after"]["areaCentroidMm"],
                views[key],
                "ortho",
            )
            for side in ("left", "right")
        ]
        side_labels(draw, coords, origin, crop, scale)
    draw.text(
        (50, 555),
        "L and R mark patient sides. Both panels retain the kidneys and pancreas at native scale.",
        font=font(18),
        fill=MUTED,
    )
    image.save(output / "grayscale.png")


def sections(output, geometry):
    image, draw = canvas(
        (1320, 554),
        "Three sections through the case",
        "Transverse intersections of the actual triangles. Patient left points rightward and posterior points up.",
    )
    for i, (section, title) in enumerate(
        zip(
            geometry["sections"],
            ("Left distal limb", "Right inferior cleft", "Right terminal plate"),
            strict=True,
        )
    ):
        x = 52 + 430 * i
        draw.text((x, 158), title, fill=INK, font=font(24, serif=True))
        draw.text((x, 199), f"z = {section['zMm']:g} mm", fill=MUTED, font=font(17))
        contours = section["contoursXYMm"]
        all_points = np.concatenate([ring for rings in contours.values() for ring in rings])
        mid = (all_points.min(0) + all_points.max(0)) / 2
        scale = min(345 / max(np.ptp(all_points[:, 0]), 1), 166 / max(np.ptp(all_points[:, 1]), 1))
        for version, color, width in (("r02", GRAY, 5), ("r04", ORANGE, 3), ("r05", TEAL, 3)):
            for ring in contours[version]:
                xy = (np.array(ring) - mid) * np.array([scale, -scale]) + [x + 177, 327]
                draw.line([tuple(point) for point in np.concatenate([xy, xy[:1]])], fill=color, width=width)
        draw.line((x, 447, x + 2 * scale, 447), fill=INK, width=3)
        draw.text((x + 2 * scale + 7, 437), "2 mm", font=font(16), fill=INK)
    for x, text, color in (
        (50, "Traced case · r02", GRAY),
        (377, "Previous exterior · r04", ORANGE),
        (760, "Updated exterior · r05", TEAL),
    ):
        draw.line((x, 515, x + 40, 515), fill=color, width=4)
        draw.text((x + 50, 502), text, fill=INK, font=font(19))
    image.save(output / "case-sections.png")


def silhouette(review):
    results = {}
    for angle in ("ortho", "iso"):
        names = [f"{label}-right-{angle}" for label in ("updated", "lighter")]
        masks = [np.array(Image.open(review / (name + ".png")).getchannel("A")) >= 128 for name in names]
        edges = [m ^ ndi.binary_erosion(m) for m in masks]
        pair_metrics = []
        for a, b in (edges, edges[::-1]):
            field = ndi.distance_transform_edt(~b)
            samples = field[a]
            worst = np.unravel_index(np.argmax(np.where(a, field, -1)), a.shape)
            pair_metrics.append(
                {
                    "maxPx": float(samples.max()),
                    "p95Px": float(np.percentile(samples, 95)),
                    "worstPixelXY": [int(worst[1]), int(worst[0])],
                }
            )
        results[angle] = {
            "images": [name + ".png" for name in names],
            "directed": pair_metrics,
            "changedSilhouettePixels": int(np.count_nonzero(masks[0] ^ masks[1])),
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("review", "specimen", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    review = args.review
    geometry = json.loads((review / "geometry.json").read_text())
    media = review / "renders" if (review / "renders").is_dir() else review
    renders = json.loads((media / "renders.json").read_text())
    if sha(args.specimen) != SPECIMEN_SHA or sha(review / "geometry.json") != renders["geometrySha256"]:
        raise ValueError("Review geometry or gross specimen identity mismatch")
    for entry in renders["views"]:
        for img in entry["images"]:
            if sha(media / img["file"]) != img["sha256"]:
                raise ValueError("Poster identity mismatch: " + img["file"])
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output.parent) as work:
        out = Path(work) / "figures"
        out.mkdir()
        views = {v["id"]: v for v in renders["views"]}
        overview(media, out, views, geometry)
        specimen_plate(media, args.specimen, out)
        grayscale(media, out, views, geometry)
        sections(out, geometry)
        receipt = {
            "recipeSha256": sha(Path(__file__)),
            "geometrySha256": sha(review / "geometry.json"),
            "rendersSha256": sha(media / "renders.json"),
            "specimenSha256": SPECIMEN_SHA,
            "specimenSource": "https://commons.wikimedia.org/wiki/File:Adrenal_glands.jpg",
            "silhouetteThresholdAlpha": 128,
            "rightGlandSilhouette": silhouette(media),
            "figures": {p.name: sha(p) for p in sorted(out.iterdir())},
        }
        (out / "figures.json").write_text(json.dumps(receipt, indent=2) + "\n")
        out.rename(args.output)


if __name__ == "__main__":
    main()
