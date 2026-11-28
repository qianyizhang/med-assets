"""Compose compact review plates from Blender renders and browser captures."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BG = "#101820"
INK = "#edf3f7"
MUTED = "#bacbd6"
CT = "#ffd166"
MESH = "#6ee4ff"


def label(image, xy, text, size=19, color=INK):
    ImageDraw.Draw(image).text(
        xy, text, fill=color, font=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    )


def thumbnail(image, path, x, y, width, height):
    panel = Image.open(path).convert("RGB")
    panel.thumbnail((width, height), Image.Resampling.LANCZOS)
    image.paste(panel, (x + (width - panel.width) // 2, y + (height - panel.height) // 2))


def save(image, output, name):
    image.save(output / name, "WEBP", quality=89, method=6)


def surfaces(work, output, measurements):
    sheet = Image.new("RGB", (1304, 699), BG)
    label(sheet, (16, 14), "Right kidney exterior at matched physical scale", 27)
    label(
        sheet,
        (16, 48),
        "Neutral clay · overview and reverse oblique · isolated surfaces centered for comparison",
        18,
        MUTED,
    )
    titles = (
        "Schematic · 107 mm chord",
        f"CT half-label · {measurements['raw']['triangles']:,} triangles",
        f"Refined r01 · {measurements['export']['triangles']:,} triangles",
    )
    for j, (name, heading) in enumerate(
        (("overview", "Overview"), ("reverse", "Reverse oblique · medial recess"))
    ):
        y = 84 + j * 303
        label(sheet, (16, y), heading, 21)
        for i, title in enumerate(titles):
            x = 16 + i * 429
            width = 414
            thumbnail(sheet, work / "clay" / f"{name}-{i}.png", x, y + 34, width, 235)
            label(sheet, (x, y + 273), title, 17, MUTED)
    save(sheet, output, "matched-surfaces.webp")


def sections(work, ref_path, output, measurements):
    receipt = json.loads((HERE.parent / "wave-1/reference.json").read_text())
    width, beam = (np.array(receipt["widths"][key]) for key in ("lateral", "beam"))
    figure = Image.new("RGB", (1328, 422), BG)
    label(figure, (16, 12), "CT and refined kidney in three protected planes", 27)
    label(figure, (16, 49), "CT half-label", 19, CT)
    label(figure, (156, 49), "Refined exterior", 19, MESH)
    panel_w, panel_h = 424, 254
    left, top, right = -66, 54, 62
    pitch = (right - left) / panel_w
    bottom = top + pitch * panel_h
    with (
        np.load(ref_path, allow_pickle=False) as reference,
        np.load(work / "sections.npz") as candidate,
    ):
        for i, (plane, check) in enumerate(
            zip(receipt["planeSections"], measurements["planes"], strict=True)
        ):
            x = 16 + i * 433
            origin = np.array(plane["originRasMm"])
            ct = np.clip((reference[f"ct{i}"].astype(float) + 130) / 330, 0, 1)
            panel = (
                Image.fromarray(np.uint8(12 + 134 * ct))
                .convert("RGB")
                .resize(
                    (panel_w, panel_h),
                    Image.Resampling.LANCZOS,
                    box=((left + 70) * 4, (top - 35) * 4, (right + 70) * 4, (bottom - 35) * 4),
                )
            )

            def pixels(points, origin=origin):
                rel = points - origin
                return np.stack(
                    (
                        (np.einsum("...i,i->...", rel, width) - left) / pitch,
                        (np.einsum("...i,i->...", rel, beam) - top) / pitch,
                    ),
                    axis=-1,
                )

            draw = ImageDraw.Draw(panel)
            for contour, color in (
                (reference[f"outline{i}"], CT),
                (candidate[f"section{i}"], MESH),
            ):
                for a, b in pixels(contour):
                    draw.line((*a, *b), fill=color, width=2)
            if i == 1:
                a, b = pixels(candidate["poles1"])
                draw.line((*a, *b), fill=INK, width=1)
                for px, py in (a, b):
                    draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=INK)
                label(panel, (151, 175), "Medial hilar recess", 17)
            figure.paste(panel, (x, 78))
            name = (
                "Frame 12"
                if not check["offsetMm"]
                else f"{check['offsetMm']:+.1f} mm from frame 12"
            )
            label(figure, (x, 344), name, 21)
            worst = max(v["maxMm"] for v in check["distances"].values())
            chord = check["refinedChordMm"]
            label(
                figure,
                (x, 376),
                f"Max contour error {worst:.2f} mm · chord {chord:.1f} mm",
                17,
                MUTED,
            )
    save(figure, output, "protected-planes.webp")


def live(work, output):
    sheet = Image.new("RGB", (1324, 748), BG)
    label(sheet, (16, 12), "Saved long-axis frame in the abdominal survey", 27)
    label(
        sheet,
        (16, 48),
        "Live player · 3D probe and scan plane, B-mode and registered tissue overlay",
        18,
        MUTED,
    )
    for row, (state, heading) in enumerate(
        (
            ("before", "Before · survey schematic · 107 mm"),
            ("after", "After · s1233 teaching exemplar · 103.3 mm across the medial hilar recess"),
        )
    ):
        y = 85 + row * 326
        label(sheet, (16, y), heading, 21)
        for col, (capture, title) in enumerate(
            (("contact", "3D contact"), ("scan", "B-mode"), ("overlay", "Tissue overlay"))
        ):
            x = 16 + col * 433
            label(sheet, (x, y + 34), title, 16, MUTED)
            thumbnail(sheet, work / "captures" / f"{state}-{capture}.png", x, y + 61, 422, 246)
    save(sheet, output, "live-frame-12.webp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    measurements = json.loads((args.work / "measurements.json").read_text())
    surfaces(args.work, args.output, measurements)
    sections(args.work, args.reference, args.output, measurements)
    live(args.work, args.output)


if __name__ == "__main__":
    main()
