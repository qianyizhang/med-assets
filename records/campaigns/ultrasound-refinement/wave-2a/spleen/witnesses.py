"""Compose matched neutral clay, protected sections and verified browser captures."""

import argparse
import json
from pathlib import Path

import numpy as np
from geometry import LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG
from PIL import Image, ImageDraw, ImageFont, ImageOps

BACK = "#15191e"
INK = "#f0f3f6"
SUB = "#b4bec8"
CT = "#f5bd64"
PREVIOUS = "#c4acd7"
CANDIDATE = "#70dde0"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
CELL = (450, 317)
GAP = 16


def note(draw, xy, text, size=22, color=INK):
    draw.text(xy, text, fill=color, font=ImageFont.truetype(FONT, size))


def canvas(title, subtitle, columns, rows, cell=CELL):
    width, height = cell
    page = Image.new(
        "RGB", (width * columns + GAP * (columns + 1), 92 + rows * (height + 44)), BACK
    )
    draw = ImageDraw.Draw(page)
    note(draw, (GAP, 13), title, 30)
    note(draw, (GAP, 53), subtitle, 20, SUB)
    return page, draw


def place(page, draw, image, label, column, row, cell=CELL):
    x, y = GAP + column * (cell[0] + GAP), 100 + row * (cell[1] + 44)
    note(draw, (x, y), label)
    image.thumbnail(cell, Image.Resampling.LANCZOS)
    page.paste(image, (x + (cell[0] - image.width) // 2, y + 32))


def save(page, output, name):
    page.save(output / (name + ".webp"), "WEBP", quality=88, method=6)


def clay(organ, inputs, output, report):
    for filename, indices, views, subtitle in (
        (
            "previous-vs-r01",
            (0, 2),
            ("overview", "reverse", "detail"),
            "Exact packed exports · matching physical scale, camera and matte clay within each row",
        ),
        (
            "matched-surfaces",
            (0, 1, 2),
            ("overview", "reverse"),
            "All three surfaces share case position, orthographic framing and neutral light",
        ),
    ):
        page, draw = canvas(f"{organ.title()} · s1233 surfaces", subtitle, len(indices), len(views))
        for row, view in enumerate(views):
            for col, index in enumerate(indices):
                label = (
                    f"Previous · {report['previousSweep']['triangles']:,} tris",
                    "CT · unsmoothed half-label",
                    f"r01 · {report['export']['triangles']:,} tris",
                )[index]
                place(
                    page,
                    draw,
                    Image.open(inputs / f"{view}-{index}.png"),
                    f"{view.title()}  /  {label}",
                    col,
                    row,
                )
        save(page, output, filename)


def lanes(projected, lo, zoom, size):
    return (projected - lo) * [zoom, -zoom] + [size[0] / 2, size[1] / 2]


def sections(organ, reference, cuts, output, report):
    cell = (450, 395)
    diagnostic = report.get("pancreasExteriorDiagnostic")
    subtitle = (
        "Gold: raw CT   Lavender: previous   Cyan: r01   Green: CT filled exterior   Dotted: sector edge"
        if diagnostic
        else "Gold: CT half-label      Lavender: exact previous      Cyan: r01      Dotted: frame-12 sector footprint"
    )
    page, draw = canvas(
        f"{organ.title()} · protected scan planes",
        subtitle,
        3,
        1,
        cell,
    )
    with np.load(reference, allow_pickle=False) as ref, np.load(cuts, allow_pickle=False) as mesh:
        basis = np.array([ref["width"], ref["beam"]])
        origin = ref["origin"]
        all_segments = [ref[f"plane{i}"] for i in range(3)]
        frame = np.concatenate(all_segments).reshape(-1, 3)
        flat = np.einsum("vi,ji->vj", frame - origin, basis)
        low, high = flat.min(0), flat.max(0)
        midpoint = (low + high) / 2
        zoom = min((cell[0] - 50) / (high[0] - low[0]), (cell[1] - 52) / (high[1] - low[1]))
        for i, (segments, record) in enumerate(
            zip(all_segments, report["candidate"]["protectedPlanes"], strict=True)
        ):
            pane = Image.new("RGB", cell, "#0c1015")
            local = ImageDraw.Draw(pane)
            theta = np.linspace(
                -np.deg2rad(SECTOR_HALF_ANGLE_DEG), np.deg2rad(SECTOR_HALF_ANGLE_DEG), 96
            )
            depth = {"spleen": 133, "pancreas": 155}[organ]
            for radius in (LENS_RADIUS_MM, LENS_RADIUS_MM + depth):
                arc = np.column_stack(
                    (np.sin(theta) * radius, np.cos(theta) * radius - LENS_RADIUS_MM)
                )
                pixel = lanes(arc, midpoint, zoom, cell)
                for start, stop in zip(pixel[::3], pixel[2::3], strict=True):
                    local.line((tuple(start), tuple(stop)), fill="#59626d", width=1)
            for angle in (theta[0], theta[-1]):
                distance = np.linspace(LENS_RADIUS_MM, LENS_RADIUS_MM + depth, 90)
                line = np.column_stack(
                    (np.sin(angle) * distance, np.cos(angle) * distance - LENS_RADIUS_MM)
                )
                pixel = lanes(line, midpoint, zoom, cell)
                for start, stop in zip(pixel[::3], pixel[2::3], strict=True):
                    local.line((tuple(start), tuple(stop)), fill="#59626d", width=1)
            tracings = [(segments, CT, 6 if diagnostic else 5)]
            if diagnostic:
                tracings.append((mesh[f"filled_plane{i}"], "#83bf86", 3))
            tracings.extend(
                [
                    (mesh[f"previous_plane{i}"], PREVIOUS, 2),
                    (mesh[f"candidate_plane{i}"], CANDIDATE, 2),
                ]
            )
            for tracing, color, weight in tracings:
                projected = (tracing - origin) @ basis.T
                for start, stop in lanes(projected, midpoint, zoom, cell):
                    local.line((tuple(start), tuple(stop)), fill=color, width=weight)
            direction = max(
                (record[k] for k in ("referenceToMesh", "meshToReference")),
                key=lambda values: values["maxMm"],
            )
            x, y = lanes((direction["maxLocationRasMm"] - origin) @ basis.T, midpoint, zoom, cell)
            local.ellipse((x - 9, y - 9, x + 9, y + 9), outline=INK)
            note(
                local,
                (13, cell[1] - 55),
                f"Worst sampled distance {direction['maxMm']:.2f} mm",
                17,
                SUB,
            )
            if diagnostic:
                cut = diagnostic["delineation"]["protectedPlanes"][i]
                exterior = max(
                    (cut[k] for k in ("referenceToMesh", "meshToReference")),
                    key=lambda values: values["maxMm"],
                )
                ex, ey = lanes(
                    (exterior["maxLocationRasMm"] - origin) @ basis.T, midpoint, zoom, cell
                )
                local.rectangle((ex - 9, ey - 9, ex + 9, ey + 9), outline="#83bf86")
                note(
                    local,
                    (13, cell[1] - 79),
                    f"Exterior worst {exterior['maxMm']:.2f} mm",
                    17,
                    "#83bf86",
                )
            y_scale = cell[1] - 22
            local.line((14, y_scale, 14 + zoom * 10, y_scale), fill=INK, width=3)
            note(local, (20 + zoom * 10, y_scale - 10), "10 mm", 17, INK)
            place(page, draw, pane, f"{record['offsetMm']:+.1f} mm  /  Full plane", i, 0, cell)
    save(page, output, "protected-planes")


def captured(organ, captures, output):
    cell = (425, 318)
    page, draw = canvas(
        f"{organ.title()} · live s1233 sweep at frame 12",
        "Served mesh verified in the study player · grayscale and overlay bytes match across builds",
        3,
        2,
        cell,
    )
    for row, revision in enumerate(("Previous", "r01")):
        for col, (key, label) in enumerate(
            (
                ("player", f"{revision}  /  3D oblique"),
                ("axial", f"{revision}  /  3D axial"),
                (
                    ("scan" if row == 0 else "overlay"),
                    ("Shared grayscale" if row == 0 else "Shared tissue overlay"),
                ),
            )
        ):
            place(
                page,
                draw,
                ImageOps.exif_transpose(Image.open(captures / f"{key}-{row}.png")),
                label,
                col,
                row,
                cell,
            )
    save(page, output, "live-frame-12")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("frozen", "measured", "clay", "captures", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    data = json.loads((args.measured / "measurements.json").read_text())
    organ = data["frozen"]["organ"]
    args.output.mkdir(parents=True, exist_ok=True)
    clay(organ, args.clay, args.output, data)
    sections(
        organ, args.frozen / "reference.npz", args.measured / "sections.npz", args.output, data
    )
    captured(organ, args.captures, args.output)


if __name__ == "__main__":
    main()
