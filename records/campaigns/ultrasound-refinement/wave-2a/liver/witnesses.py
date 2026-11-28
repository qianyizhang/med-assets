"""Lay out matched Clay, source-plane, and actual player evidence as four WebPs."""

import argparse
import json
from pathlib import Path

import numpy as np
from measure import AFFINE, load_helper
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parents[1]
INK = "#eef3f6"
MUTED = "#a9b9c8"
BG = "#17212b"
PANEL = "#202d38"
COLORS = {"reference": "#f4c973", "previous": "#b4a3d9", "candidate": "#64e4d9"}


def font(size):
    paths = (
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for path in paths:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def title(draw, top, sub):
    draw.text((18, 11), top, font=font(27), fill=INK)
    draw.text((18, 47), sub, font=font(16), fill=MUTED)


def save(canvas, output):
    canvas.save(output, format="WEBP", quality=89, method=6)
    if output.stat().st_size > 500_000:
        raise ValueError(f"Evidence exceeds 500,000 bytes: {output}")


def clay_plate(clay, output, baseline, metrics):
    previous = metrics["previousSweep"]
    candidate = metrics["export"]
    heading = (
        ("Exact delivered r01", "Refined r02") if baseline else ("CT half-label", "Refined r02")
    )
    first = "r01" if baseline else "half-label"
    canvas = Image.new("RGB", (1182, 1282), BG)
    draw = ImageDraw.Draw(canvas)
    title(
        draw,
        "s1233 liver exterior",
        "Matched neutral clay · identical orthographic camera, scale, material and light within each row",
    )
    for i, (label, tris) in enumerate(
        zip(
            heading,
            (
                previous["triangles"] if baseline else metrics["reference"]["triangles"],
                candidate["triangles"],
            ),
            strict=True,
        )
    ):
        draw.text((18 + 582 * i, 78), f"{label} · {tris:,} triangles", font=font(19), fill=INK)
    for row, (view, name) in enumerate(
        (
            ("anterior", "Anterior oblique"),
            ("inferior", "Inferior oblique · cleft side"),
            ("dome", "Dome detail · matched enlargement"),
        )
    ):
        top = 111 + 390 * row
        draw.text((18, top), name, font=font(16), fill=MUTED)
        for col, surface in enumerate((first, "r02")):
            x = 15 + 582 * col
            with Image.open(clay / f"{view}-{surface}.png") as image:
                canvas.paste(image, (x, top + 21))
    save(canvas, output)


def section_panel(canvas, box, segments, bounds, label, mark=None):
    left, top, width, height = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((left, top, left + width, top + height), radius=7, fill=PANEL)
    draw.text((left + 13, top + 9), label, fill=INK, font=font(17))
    low, high = np.asarray(bounds).T
    usable = np.array([width - 37, height - 75], dtype=float)
    center = np.array([left + width / 2, top + 27 + (height - 72) / 2])
    scale = min(usable / ((high - low) * 1.5))
    margin = (low + high) / 2

    def map_xy(vox):
        return tuple(center + (vox - margin) * np.array([1, -1]) * 1.5 * scale)

    for layer in ("reference", "previous", "candidate"):
        voxel = (segments[layer] - AFFINE[:3, 3]) / 1.5
        for pair in voxel:
            draw.line(
                [map_xy(point[:2]) for point in pair],
                fill=COLORS[layer],
                width=2 if layer != "reference" else 5,
            )
    if mark is not None:
        x, y = map_xy(np.array(mark))
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), outline="#ffffff", width=2)
    sx, sy = left + 17, top + height - 15
    draw.line((sx, sy, sx + 10 * scale, sy), fill=MUTED, width=2)
    draw.text((sx + 10 * scale + 6, sy - 7), "10 mm", fill=MUTED, font=font(12))
    ox, oy = left + width - 26, sy
    draw.line((ox - 16, oy, ox, oy, ox, oy - 16), fill=MUTED, width=1)
    draw.text((ox - 4, oy - 29), "A", fill=MUTED, font=font(11))
    draw.text((ox + 4, oy - 8), "R", fill=MUTED, font=font(11))


def protected_plate(geometry_dir, previous, candidate, output):
    helper = load_helper(CAMPAIGN / "wave-1/measure.py")
    geometry = load_helper(HERE / "measure.py")
    frozen = json.loads((HERE / "frozen.json").read_text())
    measurements = json.loads((geometry_dir / "measurements.json").read_text())
    with np.load(geometry_dir / "reference.npz", allow_pickle=False) as raw:
        triangles = {"reference": raw["vertices"][raw["faces"]]}
    for name, path in (("previous", previous), ("candidate", candidate)):
        vertices, faces = helper.mesh(path)
        triangles[name] = vertices[faces]
    canvas = Image.new("RGB", (1182, 742), BG)
    draw = ImageDraw.Draw(canvas)
    title(
        draw,
        "Inferior cleft and narrow source channels",
        "Axial cuts on the original 1.5 mm s1233 CT grid",
    )
    for i, (layer, label) in enumerate(
        (("reference", "CT half-label"), ("previous", "Exact r01"), ("candidate", "r02"))
    ):
        x = 18 + 159 * i
        draw.line((x, 85, x + 25, 85), fill=COLORS[layer], width=4)
        draw.text((x + 32, 75), label, font=font(15), fill=INK)
    sections = [
        (
            section["zVoxel"],
            frozen["protectedPlanes"]["cleftCropVoxelXY"],
            f"{section['offsetMm']:+g} mm   ·   z={section['zVoxel']}",
            None,
        )
        for section in measurements["protectedPlanes"]
    ]
    sections += [
        (
            236.5,
            [[145, 163], [141, 159]],
            "Channel A · prior trial's whole-surface maximum",
            (156.0, 151.0),
        ),
        (219.5, [[166, 183], [171, 195]], "Channel B · localized bridge", (171.0, 178.5)),
    ]
    boxes = [(15 + 389 * i, 107, 374, 308) for i in range(3)] + [
        (15, 433, 568, 286),
        (600, 433, 568, 286),
    ]
    for box, (z, bounds, label, mark) in zip(boxes, sections, strict=True):
        center = helper.ras(np.array([0, 0, z]))
        crop_ras = np.array(bounds) * 1.5 + AFFINE[:2, 3, None]
        clipped = {
            name: geometry.clipped(helper.cut(t, center, np.array([0, 0, 1])), crop_ras, (0, 1))
            for name, t in triangles.items()
        }
        section_panel(canvas, box, clipped, bounds, label, mark)
    save(canvas, output)


def player_plate(captures, output):
    canvas = Image.new("RGB", (1182, 742), BG)
    draw = ImageDraw.Draw(canvas)
    title(
        draw,
        "Oblique portal view · frame 12",
        "Live s1233 sweep · matching probe pose, scan, overlay and browser viewport",
    )
    x0 = 18
    for index, label in enumerate(("WebGL scene", "Simulated B-mode", "Tissue overlay")):
        draw.text((x0 + 389 * index, 83), label, font=font(18), fill=MUTED)
    for row, name in enumerate(("baseline", "candidate")):
        top = 116 + 307 * row
        draw.text(
            (18, top), "Exact delivered r01" if row == 0 else "Refined r02", font=font(17), fill=INK
        )
        for col, panel in enumerate(("scene", "scan", "overlay")):
            x = x0 + 389 * col
            with Image.open(captures / f"{name}-{panel}.png") as raw:
                picture = ImageOps.contain(raw.convert("RGB"), (374, 269), Image.Resampling.LANCZOS)
            canvas.paste(picture, (x + (374 - picture.width) // 2, top + 25))
    save(canvas, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("clay", type=Path)
    parser.add_argument("captures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    metrics = json.loads((args.geometry / "measurements.json").read_text())
    clay_plate(args.clay, args.output / "previous-vs-r02.webp", True, metrics)
    clay_plate(args.clay, args.output / "matched-surfaces.webp", False, metrics)
    protected_plate(
        args.geometry, args.previous, args.candidate, args.output / "protected-planes.webp"
    )
    player_plate(args.captures, args.output / "live-frame-12.webp")


if __name__ == "__main__":
    main()
