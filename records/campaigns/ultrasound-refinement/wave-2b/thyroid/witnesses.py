"""Compose bilateral thyroid clay, raw contour and running sweep witnesses."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SHARED = Path(__file__).resolve().parents[2] / "wave-2a/spleen/witnesses.py"
SPEC = importlib.util.spec_from_file_location("plates", SHARED)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SHARED}")
plates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plates)


def clay_surfaces(inputs, output, report, revision):
    labels = (
        f"Previous · {report['previousSweep']['triangles']:,} tris",
        "CT · unsmoothed half-label",
        f"{revision} · {report['export']['triangles']:,} tris",
    )
    for filename, indices, views in (
        (f"previous-vs-{revision}", (0, 2), ("overview", "reverse", "detail")),
        ("matched-surfaces", (0, 1, 2), ("overview", "reverse")),
    ):
        page, draw = plates.canvas(
            "Thyroid · s1127 surfaces",
            "Both lobes and their bridge · matching physical scale, camera and clay light",
            len(indices),
            len(views),
        )
        for row, view in enumerate(views):
            for col, index in enumerate(indices):
                plates.place(
                    page,
                    draw,
                    Image.open(inputs / f"{view}-{index}.png"),
                    f"{view.title()}  /  {labels[index]}",
                    col,
                    row,
                )
        plates.save(page, output, filename)


def contour_panel(cell, arrays, cuts, specs, profiles, revision):
    panels = []
    traces = []
    for spec in specs:
        name = spec["name"]
        basis = np.array([spec["width"], spec["beam"]]) if "width" in spec else np.eye(3)[1:]
        origin = np.array(spec["originRasMm"]) if "width" in spec else np.zeros(3)
        paths = [
            np.einsum("...i,ki->...k", seq - origin, basis)
            for seq in (arrays[name], cuts[f"{name}_previous"], cuts[f"{name}_candidate"])
        ]
        traces.append(paths)
    raw = np.concatenate([row[0].reshape(-1, 2) for row in traces])
    low, high = raw.min(0), raw.max(0)
    middle = (low + high) / 2
    zoom = min((cell[0] - 66) / (high[0] - low[0]), (cell[1] - 92) / (high[1] - low[1]))
    for spec, paths in zip(specs, traces, strict=True):
        pane = Image.new("RGB", cell, "#0c1015")
        draw = ImageDraw.Draw(pane)
        if "width" in spec:
            field = np.array([[-22, 0], [-22, 78], [22, 78], [22, 0], [-22, 0]])
            draw.line(
                [tuple(point) for point in plates.lanes(field, middle, zoom, cell)], fill="#58626c"
            )
        for path, color, weight in zip(
            paths, (plates.CT, plates.PREVIOUS, plates.CANDIDATE), (6, 3, 2), strict=True
        ):
            for start, end in plates.lanes(path, middle, zoom, cell):
                draw.line((tuple(start), tuple(end)), fill=color, width=weight)
        profile = profiles[spec["name"]]
        value = max(direction["maxMm"] for direction in profile["candidate"].values())
        prior = max(direction["maxMm"] for direction in profile["baseline"].values())
        label = f"Previous {prior:.2f} mm  /  {revision} {value:.2f} mm"
        plates.note(draw, (12, cell[1] - 49), label, 16, plates.SUB)
        draw.line((14, cell[1] - 20, 14 + 10 * zoom, cell[1] - 20), fill=plates.INK, width=3)
        plates.note(draw, (20 + 10 * zoom, cell[1] - 30), "10 mm", 16)
        panels.append(pane)
    return panels


def protected(reference, measured, output, receipt, revision):
    cell = (450, 265)
    legend = f"Gold · raw half-label     Lavender · previous     Cyan · {revision}     Values show worst sampled distance"
    profiles = {row["name"]: row for row in receipt["protectedPlanes"]}
    specs = receipt["frozen"]["protectedPlanes"]
    with (
        np.load(reference, allow_pickle=False) as arrays,
        np.load(measured / "sections.npz", allow_pickle=False) as cuts,
    ):
        page, draw = plates.canvas("Thyroid · long-axis scan cuts at frame 48", legend, 3, 2, cell)
        for row, side in enumerate(("right", "left")):
            selected = [
                item for item in specs if item.get("side") == side and item.get("frame") == 48
            ]
            for col, (pane, item) in enumerate(
                zip(
                    contour_panel(cell, arrays, cuts, selected, profiles, revision),
                    selected,
                    strict=True,
                )
            ):
                plates.place(
                    page,
                    draw,
                    pane,
                    f"{side.title()} lobe  /  {item['offsetMm']:+.1f} mm",
                    col,
                    row,
                    cell,
                )
        plates.save(page, output, "protected-planes")

        page, draw = plates.canvas("Thyroid · registered isthmus cuts", legend, 3, 2, cell)
        bridge = [item for item in specs if item["name"].startswith("isthmus")]
        entry = [item for item in specs if item["name"] == "entry"]
        panels = contour_panel(cell, arrays, cuts, bridge, profiles, revision) + contour_panel(
            cell, arrays, cuts, entry, profiles, revision
        )
        labels = [f"Sagittal  /  {item['offsetMm']:+.1f} mm" for item in bridge] + [
            "Transverse  /  entry"
        ]
        for i, (pane, label) in enumerate(zip(panels, labels, strict=True)):
            plates.place(page, draw, pane, label, i % 3, i // 3, cell)
        plates.save(page, output, "isthmus-cuts")


def captured(captures, output, frame, revision):
    cell = (430, 270)
    title = (
        "Thyroid · saved transverse views"
        if frame == 12
        else "Thyroid · longitudinal views selected in the player"
    )
    page, draw = plates.canvas(
        title,
        f"Frame {frame} · s1127 · exact mesh bytes checked · shared grayscale and tissue overlay",
        3,
        2,
        cell,
    )
    for row, side in enumerate(("right", "left")):
        for col, (version, media, label) in enumerate(
            (
                ("previous", "scene", "Previous"),
                ("candidate", "scene", revision),
                ("candidate", "overlay", "Shared overlay"),
            )
        ):
            image = Image.open(captures / f"{version}-{side}-{frame}-{media}.png")
            plates.place(page, draw, image, f"{side.title()}  /  {label}", col, row, cell)
    plates.save(page, output, f"live-frame-{frame}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "measured", "clay", "captures", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--revision", choices=("r02", "r03"), default="r03")
    args = parser.parse_args()
    report = json.loads((args.measured / "measurements.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    clay_surfaces(args.clay, args.output, report, args.revision)
    protected(args.reference, args.measured, args.output, report, args.revision)
    for frame in (12, 48):
        captured(args.captures, args.output, frame, args.revision)


if __name__ == "__main__":
    main()
