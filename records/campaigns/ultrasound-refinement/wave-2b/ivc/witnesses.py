"""Compose the matched IVC renders, protected sections and saved sweep capture."""

import argparse
import json
import runpy
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
STYLES = runpy.run_path(str(HERE.parents[1] / "wave-2a/spleen/witnesses.py"))
canvas, note, place, save = (STYLES[name] for name in ("canvas", "note", "place", "save"))


def clay(renders, output, report):
    cell = (350, 530)
    proof = (
        ("anterior", "Front oblique"),
        ("reverse", "Reverse oblique"),
        ("shoulder", "Shoulder detail"),
    )
    page, draw = canvas(
        "Inferior vena cava · previous sweep and r01",
        "The vertical abdominal course remains visible in both packed meshes.",
        3,
        2,
        cell,
    )
    for row, source in enumerate((0, 2)):
        label = "Previous" if row == 0 else "r01"
        for col, (view, name) in enumerate(proof):
            place(
                page,
                draw,
                Image.open(renders / f"{view}-{source}.png"),
                f"{label} · {name}",
                col,
                row,
                cell,
            )
    save(page, output, "previous-vs-r01")

    page, draw = canvas(
        "s1233 · matched neutral-clay surfaces",
        "Same view, physical scale and lighting within each row.",
        3,
        2,
        cell,
    )
    counts = (
        report["frozen"]["previousSweep"]["triangles"],
        report["exports"]["abdominal"]["export"]["triangles"],
    )
    labels = (
        f"Previous · {counts[0]:,} triangles",
        "Raw CT half-label",
        f"r01 · {counts[1]:,} triangles",
    )
    for row, (view, _) in enumerate(proof[:2]):
        for col, label in enumerate(labels):
            place(page, draw, Image.open(renders / f"{view}-{col}.png"), label, col, row, cell)
    save(page, output, "matched-surfaces")


def panes(reference, measured, output, report):
    cell = (450, 350)
    page, draw = canvas(
        "Inferior vena cava · protected cuts",
        "Gold · raw CT half-label     Lavender · previous       Cyan · r01       Circle · worst sampled gap",
        3,
        2,
        cell,
    )
    frozen = report["frozen"]
    scope = "abdominal"
    pose = frozen["pose"]
    metrics = report["exports"][scope]["candidate"]["protectedPlanes"]
    inventory = frozen["rawInventories"][scope]["planes"]
    with (
        np.load(reference / f"{scope}.npz") as raw,
        np.load(measured / f"{scope}-sections.npz") as mesh,
    ):
        for slot, i in enumerate((0, 1, 2, 3, 5, 6)):
            key = f"plane{i}"
            center = np.asarray(inventory[i]["originRasMm"])
            basis = np.asarray([pose["width"], pose["beam"]] if i < 3 else [[1, 0, 0], [0, 1, 0]])
            cut = raw[key]
            # Use the same long-axis scale and framing in each of the three parallel views.
            bounds = np.concatenate([raw[f"plane{j}"] for j in range(3)]) if i < 3 else cut
            flattened = np.einsum("vi,ji->vj", bounds.reshape(-1, 3) - center, basis)
            lower, upper = flattened.min(0), flattened.max(0)
            average = (upper + lower) / 2
            zoom = min(
                (cell[0] - 52) / (upper[0] - lower[0]), (cell[1] - 114) / (upper[1] - lower[1])
            )

            def pixels(points, center=center, basis=basis, average=average, zoom=zoom):
                uv = np.einsum("...i,ji->...j", points - center, basis)
                return (uv - average) * [zoom, -zoom] + [cell[0] / 2, cell[1] / 2 - 18]

            panel = Image.new("RGB", cell, "#0c1015")
            local = ImageDraw.Draw(panel)
            for segments, color, weight in (
                (cut, STYLES["CT"], 5),
                (mesh[f"previous_{key}"], STYLES["PREVIOUS"], 2),
                (mesh[key], STYLES["CANDIDATE"], 2),
            ):
                for a, b in pixels(segments):
                    local.line((tuple(a), tuple(b)), fill=color, width=weight)
            row = metrics[i]
            worst = max(
                (row["referenceToMesh"], row["meshToReference"]), key=lambda value: value["maxMm"]
            )
            x, y = pixels(np.asarray(worst["maxLocationRasMm"]))
            local.ellipse((x - 7, y - 7, x + 7, y + 7), outline=STYLES["INK"])
            note(local, (13, cell[1] - 50), f"Worst gap {worst['maxMm']:.2f} mm", 17, STYLES["SUB"])
            bar_y = cell[1] - 18
            local.line((14, bar_y, 14 + zoom * 10, bar_y), fill=STYLES["INK"], width=3)
            note(local, (20 + zoom * 10, bar_y - 10), "10 mm", 16)
            titles = (
                "Parallel cut −1.5 mm",
                "Frame 12 · saved cut",
                "Parallel cut +1.5 mm",
                "Inferior extension · axial",
                "Superior flare · axial",
                "Abdominal cutoff · axial",
            )
            place(page, draw, panel, titles[slot], slot % 3, slot // 3, cell)
    save(page, output, "protected-planes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("frozen", "measured", "renders", "captures", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = json.loads((args.measured / "measurements.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    clay(args.renders, args.output, report)
    panes(args.frozen, args.measured, args.output, report)
    if args.captures.is_dir():
        STYLES["captured"]("Inferior vena cava", args.captures, args.output, "r01")


if __name__ == "__main__":
    main()
