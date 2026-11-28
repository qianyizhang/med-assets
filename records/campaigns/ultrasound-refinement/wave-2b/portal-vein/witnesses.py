"""Compose matched surfaces, protected scan cuts and verified browser captures."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from geometry import LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG
from PIL import Image, ImageDraw

SHARED = Path(__file__).resolve().parents[2] / "wave-2a/spleen/witnesses.py"
SPEC = importlib.util.spec_from_file_location("plates", SHARED)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SHARED}")
plates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plates)


def sections(reference, cuts, output, report, revision):
    cell = (450, 375)
    page, draw = plates.canvas(
        "Portal and splenic vein · protected scan planes",
        f"Gold · raw half-label     Lavender · previous     Cyan · {revision}     Dotted · imaged sector footprint",
        3,
        1,
        cell,
    )
    with np.load(reference, allow_pickle=False) as ref, np.load(cuts, allow_pickle=False) as mesh:
        basis = np.array([ref["width"], ref["beam"]])
        origin = ref["origin"]
        raw = [ref[f"plane{i}"] for i in range(3)]
        flat = np.einsum("...i,ki->...k", np.concatenate(raw).reshape(-1, 3) - origin, basis)
        low, high = flat.min(0), flat.max(0)
        middle = (low + high) / 2
        zoom = min((cell[0] - 76) / (high[0] - low[0]), (cell[1] - 80) / (high[1] - low[1]))
        theta = np.linspace(
            -np.deg2rad(SECTOR_HALF_ANGLE_DEG), np.deg2rad(SECTOR_HALF_ANGLE_DEG), 96
        )

        for i, record in enumerate(report["candidate"]["protectedPlanes"]):
            pane = Image.new("RGB", cell, "#0c1015")
            local = ImageDraw.Draw(pane)
            depth = 155
            for radius in (LENS_RADIUS_MM, LENS_RADIUS_MM + depth):
                arc = np.column_stack(
                    (np.sin(theta) * radius, np.cos(theta) * radius - LENS_RADIUS_MM)
                )
                coords = plates.lanes(arc, middle, zoom, cell)
                for start, end in zip(coords[::3], coords[2::3], strict=True):
                    local.line((tuple(start), tuple(end)), fill="#59626d")
            for angle in (theta[0], theta[-1]):
                radii = np.linspace(LENS_RADIUS_MM, LENS_RADIUS_MM + depth, 90)
                line = np.column_stack(
                    (np.sin(angle) * radii, np.cos(angle) * radii - LENS_RADIUS_MM)
                )
                coords = plates.lanes(line, middle, zoom, cell)
                for start, end in zip(coords[::3], coords[2::3], strict=True):
                    local.line((tuple(start), tuple(end)), fill="#59626d")
            for tracing, color, weight in (
                (raw[i], plates.CT, 5),
                (mesh[f"previous_plane{i}"], plates.PREVIOUS, 2),
                (mesh[f"candidate_plane{i}"], plates.CANDIDATE, 2),
            ):
                projected = np.einsum("...i,ki->...k", tracing - origin, basis)
                for start, end in plates.lanes(projected, middle, zoom, cell):
                    local.line((tuple(start), tuple(end)), fill=color, width=weight)
            worst = max(
                (record[k] for k in ("referenceToMesh", "meshToReference")),
                key=lambda m: m["maxMm"],
            )
            point = np.einsum("i,ki->k", worst["maxLocationRasMm"] - origin, basis)
            x, y = plates.lanes(point, middle, zoom, cell)
            local.ellipse((x - 8, y - 8, x + 8, y + 8), outline=plates.INK)
            plates.note(
                local, (13, cell[1] - 58), f"Worst sampled distance {worst['maxMm']:.2f} mm", 17
            )
            local.line((14, cell[1] - 21, 14 + 10 * zoom, cell[1] - 21), fill=plates.INK, width=3)
            plates.note(local, (20 + 10 * zoom, cell[1] - 31), "10 mm", 17)
            plates.place(
                page, draw, pane, f"{record['offsetMm']:+.1f} mm  /  Full plane", i, 0, cell
            )
    plates.save(page, output, "protected-planes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "measured", "clay", "captures", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--revision", choices=("r01", "r02"), default="r02")
    args = parser.parse_args()
    report = json.loads((args.measured / "measurements.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    plates.clay("portal and splenic vein", args.clay, args.output, report, args.revision)
    sections(args.reference, args.measured / "sections.npz", args.output, report, args.revision)
    plates.captured("portal and splenic vein", args.captures, args.output, args.revision)


if __name__ == "__main__":
    main()
