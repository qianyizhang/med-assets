"""Lay out matched aorta witnesses for independent scene and geometry review."""

import argparse
import json
from pathlib import Path

import numpy as np
from freeze import HERE, wave
from PIL import Image, ImageDraw, ImageFont, ImageOps

BG = "#17212b"
TEXT = "#eef3f6"
MUTED = "#adbfcd"
RAW = "#ffd377"
TRIAL = "#4ee9da"
PREVIOUS = "#b4a3d9"

NAMES = {
    "aorta": "Complete s1233 label",
    "aorta-abdomen": "Abdominal sweep crop",
    "aorta-screening": "Screening sweep crop",
}


def font(size):
    path = Path("/System/Library/Fonts/Helvetica.ttc")
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default(size)


def title(image, heading, context):
    draw = ImageDraw.Draw(image)
    draw.text((19, 12), heading, fill=TEXT, font=font(30))
    draw.text((19, 49), context, fill=MUTED, font=font(17))
    return draw


def fit(image, path, bounds):
    x, y, width, height = bounds
    with Image.open(path) as source:
        view = ImageOps.contain(source.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
    image.paste(view, (x + (width - view.width) // 2, y + (height - view.height) // 2))


def save(image, output, name):
    image.save(output / name, format="WEBP", quality=89, method=6)


def comparison(clay, output, previous):
    first = "previous" if previous else "raw"
    exports = list(NAMES)[1:] if previous else list(NAMES)
    image = Image.new("RGB", (1608, 76 + 470 * len(exports)), BG)
    heading = (
        "Aortic sweep exteriors before and after" if previous else "Source label and Aorta r01"
    )
    draw = title(
        image,
        heading,
        "Same orthographic camera and scale within each pair. The closer view uses reverse lighting.",
    )
    for row, export in enumerate(exports):
        top = 77 + 470 * row
        draw.text((19, top), NAMES[export], fill=TEXT, font=font(22))
        for i, (view, label) in enumerate(
            (
                ("anterior", "Anterior oblique · overview"),
                (
                    "detail",
                    "Posterior oblique · arch detail"
                    if export == "aorta"
                    else "Posterior oblique · lower trunk detail",
                ),
            )
        ):
            x = 19 + 795 * i
            draw.text((x, top + 29), label, fill=MUTED, font=font(16))
            for j, (version, caption) in enumerate(
                (
                    (first, "Exact prior export" if previous else "Raw CT half-label"),
                    ("r01", "Ultrasound r01"),
                )
            ):
                left = x + j * 385
                draw.text((left, top + 58), caption, fill=TEXT, font=font(17))
                fit(image, clay / f"{export}-{view}-{version}.png", (left, top + 82, 373, 377))
    save(image, output, "previous-vs-r01.webp" if previous else "matched-surfaces.webp")


def protected(frozen, reference, replay, output):
    matrix = [
        [("aorta-abdomen", 0), ("aorta-abdomen", 1), ("aorta-abdomen", 2)],
        [("aorta-screening", i) for i in (1, 4, 7)],
        [("aorta-abdomen", 4), ("aorta-screening", 10), ("aorta", 3)],
    ]
    header = [
        "Abdominal long-axis field and its adjacent planes",
        "Screening short-axis fields at proximal, mid and distal stations",
        "Artificial caps and a source-defined arch transition",
    ]
    column_width, row_height = 492, 343
    image = Image.new("RGB", (1508, 111 + row_height * len(matrix)), BG)
    draw = title(
        image,
        "Protected aortic contours on the CT reference",
        "CT is shown at each physical section. The crop rims mark boundaries of the displayed mesh.",
    )
    for i, (label, color) in enumerate(
        (("Raw 0.5 CT label", RAW), ("Exact prior sweep", PREVIOUS), ("Ultrasound r01", TRIAL))
    ):
        x = 19 + i * 204
        draw.line((x, 87, x + 24, 87), fill=color, width=4)
        draw.text((x + 31, 76), label, fill=TEXT, font=font(16))
    for row, sections in enumerate(matrix):
        top = 108 + row * row_height
        draw.text((19, top), header[row], fill=TEXT, font=font(21))
        for col, (export, i) in enumerate(sections):
            plane = frozen["exports"][export]["planes"][i]
            with (
                np.load(reference / f"{export}-reference.npz", allow_pickle=False) as ref,
                np.load(replay / f"{export}.npz", allow_pickle=False) as trial,
            ):
                source = ref[f"ct{i}"]
                outlines = [(ref[f"outline{i}"], RAW, 4), (trial[f"outline{i}"], TRIAL, 2)]
                if export != "aorta":
                    stem = frozen["exports"][export]["prior"]["stage"]["path"]
                    previous = Path(frozen["baselineAssembly"]) / "stage" / stem
                    vertices, faces = wave.mesh(previous)
                    cut = wave.cut(
                        vertices[faces], np.array(plane["originRasMm"]), np.array(plane["normal"])
                    )
                    outlines.insert(1, (cut, PREVIOUS, 2))
                x, y = 19 + col * column_width, top + 58
                name = (
                    plane["name"]
                    if "name" in plane
                    else f"Frame {plane['frame']} · {plane['offsetMm']:+g} mm"
                )
                draw.text((x, y - 22), name, fill=MUTED, font=font(17))
                lower, upper = np.array(plane["bounds"])
                span = upper - lower
                scale = min((column_width - 21) / span[0], 246 / span[1])
                size = tuple(np.rint(span * scale).astype(int))
                grey = np.uint8(np.clip((source + 140) * 0.60, 0, 255))
                picture = Image.fromarray(grey).resize(size, Image.Resampling.BILINEAR)
                image.paste(picture, (x, y))
                origin, width, beam = (
                    np.array(plane[key]) for key in ("originRasMm", "width", "beam")
                )
                for segments, color, thickness in outlines:
                    relative = segments - origin
                    projected = np.stack(
                        (wave.dot(relative, width), wave.dot(relative, beam)), axis=-1
                    )
                    for a, b in (projected - lower) * scale:
                        draw.line(
                            (x + a[0], y + a[1], x + b[0], y + b[1]), fill=color, width=thickness
                        )
                scale_x, scale_y = x + 10, y + size[1] + 13
                draw.line((scale_x, scale_y, scale_x + 10 * scale, scale_y), fill=MUTED, width=2)
                draw.text(
                    (scale_x + 10 * scale + 8, scale_y - 8), "10 mm", fill=MUTED, font=font(13)
                )
    save(image, output, "protected-planes.webp")


def live(captures, output):
    canvas = Image.new("RGB", (1510, 1250), BG)
    draw = title(
        canvas,
        "Saved frame 12 in the two running sweeps",
        "WebGL crop swap at the frozen pose. The simulated scan and registered overlay are identical in both versions.",
    )
    for i, title_text in enumerate(
        ("Previous oblique scene", "r01 oblique scene", "Simulated B-mode", "Label overlay")
    ):
        draw.text((21 + 367 * i, 89), title_text, font=font(18), fill=MUTED)
    for row, (sweep, label) in enumerate(
        (
            ("aorta", "Abdominal aorta · long axis"),
            ("aortic-screening", "Aortic screening · proximal transverse station"),
        )
    ):
        top = 124 + row * 552
        draw.text((21, top), label, font=font(21), fill=TEXT)
        for col, stem in enumerate(
            ("previous-scene", "candidate-scene", "candidate-scan", "candidate-overlay")
        ):
            fit(canvas, captures / f"{sweep}-{stem}.png", (19 + col * 367, top + 29, 355, 299))
        draw.text(
            (21, top + 336), "Axial orbit · previous export and r01", font=font(16), fill=MUTED
        )
        for col, side in enumerate(("previous", "candidate")):
            fit(
                canvas,
                captures / f"{sweep}-{side}-axial.png",
                (19 + col * 367, top + 358, 355, 168),
            )
    save(canvas, output, "live-frame-12.webp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("replay", type=Path)
    parser.add_argument("clay", type=Path)
    parser.add_argument("captures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    frozen = json.loads((HERE / "frozen.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    comparison(args.clay, args.output, True)
    comparison(args.clay, args.output, False)
    protected(frozen, args.reference, args.replay, args.output)
    live(args.captures, args.output)


if __name__ == "__main__":
    main()
