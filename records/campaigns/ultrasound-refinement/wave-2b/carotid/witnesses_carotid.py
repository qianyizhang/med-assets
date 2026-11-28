"""Render the four matched evidence boards for either s1127 carotid packet."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from freeze_carotid import HERE, wave
from PIL import Image

sys.path.insert(0, str(HERE.parent / "aorta"))
from measure import mesh_in_ras  # noqa: E402
from witnesses import BG, MUTED, PREVIOUS, RAW, TEXT, TRIAL, fit, font, save, title  # noqa: E402


def clay_plate(side, clay, output, previous):
    first = "previous" if previous else "raw"
    heading = (
        "Common carotid before and after" if previous else "Raw half-label and common carotid r01"
    )
    canvas = Image.new("RGB", (1380, 1010), BG)
    draw = title(
        canvas,
        side.title() + " · " + heading,
        "Matched camera, scale and neutral lighting within each pair.",
    )
    for row, (name, scope) in enumerate(
        (
            (f"carotid-{side}", "Neck acquisition crop"),
            (f"carotid-{side}-full", "Complete source label · thyroid context"),
        )
    ):
        top = 77 + 458 * row
        draw.text((19, top), scope, fill=TEXT, font=font(22))
        for col, (view, label) in enumerate(
            (
                ("anterior", "Anterior oblique · overview"),
                ("detail", "Posterior oblique · trunk detail"),
            )
        ):
            x = 19 + 670 * col
            draw.text((x, top + 33), label, fill=MUTED, font=font(16))
            for k, (version, caption) in enumerate(
                (
                    (first, "Exact prior export" if previous else "Raw CT half-label"),
                    ("r01", "r01 packed exterior"),
                )
            ):
                left = x + k * 332
                draw.text((left, top + 57), caption, fill=TEXT, font=font(17))
                fit(canvas, clay / f"{name}-{view}-{version}.png", (left, top + 84, 323, 356))
    save(canvas, output, "previous-vs-r01.webp" if previous else "matched-surfaces.webp")


def planes_plate(side, brief, reference, measured, output):
    name = f"carotid-{side}"
    matrix = [
        [(name, i) for i in range(3)],
        [(name, i) for i in range(3, 6)],
        [(name, 6), (name, 7), (f"{name}-full", 1)],
    ]
    subheads = (
        "Saved transverse frame 12 · central and parallel cuts",
        "Saved longitudinal frame 48 · central and parallel cuts",
        "Inferior and superior acquisition cuts · final imaged full-label cap",
    )
    canvas = Image.new("RGB", (1440, 1120), BG)
    draw = title(
        canvas,
        f"{side.title()} carotid · protected contours",
        "The underlying CT, raw half-label and mesh cuts use the frozen physical sections.",
    )
    for i, (caption, color) in enumerate(
        (("Raw CT half-label", RAW), ("Exact prior export", PREVIOUS), ("r01", TRIAL))
    ):
        x = 19 + i * 185
        draw.line((x, 89, x + 24, 89), fill=color, width=4)
        draw.text((x + 31, 78), caption, fill=TEXT, font=font(16))
    meshes = {}
    for export, config in brief["exports"].items():
        path = Path(brief["baselineAssembly"]) / "stage" / config["prior"]["stage"]["path"]
        affine = np.array(brief["source"]["rasMmFromVoxel"])
        v, f = mesh_in_ras(path, affine)
        meshes[export] = v[f]
    for row, panels in enumerate(matrix):
        y0 = 111 + 333 * row
        draw.text((19, y0), subheads[row], fill=TEXT, font=font(22))
        for col, (export, index) in enumerate(panels):
            plane = brief["exports"][export]["planes"][index]
            origin, width, beam, normal = (
                np.array(plane[k]) for k in ("originRasMm", "width", "beam", "normal")
            )
            with np.load(reference / f"{export}-reference.npz", allow_pickle=False) as ref:
                ct, raw = ref[f"ct{index}"], ref[f"outline{index}"]
            with np.load(measured / f"{export}.npz", allow_pickle=False) as candidate:
                r01 = candidate[f"outline{index}"]
            prev = wave.cut(meshes[export], origin, normal)
            low, high = np.array(plane["bounds"])
            span = high - low
            scale = min(445 / span[0], 234 / span[1])
            dimensions = tuple(np.rint(span * scale).astype(int))
            x, y = 19 + col * 475, y0 + 60
            caption = plane.get(
                "name", f"Frame {plane.get('frame', '')} · {plane.get('offsetMm', 0):+g} mm"
            )
            draw.text((x, y - 24), caption, fill=MUTED, font=font(18))
            im = Image.fromarray(np.uint8(np.clip((ct + 140) * 0.60, 0, 255)))
            if "name" in plane:
                im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            canvas.paste(im.resize(dimensions, Image.Resampling.BILINEAR), (x, y))
            for outline, color, thickness in ((raw, RAW, 4), (prev, PREVIOUS, 2), (r01, TRIAL, 2)):
                relative = outline - origin
                projected = np.stack((wave.dot(relative, width), wave.dot(relative, beam)), axis=-1)
                if "name" in plane:
                    projected[..., 1] = low[1] + high[1] - projected[..., 1]
                for a, b in (projected - low) * scale:
                    draw.line((x + a[0], y + a[1], x + b[0], y + b[1]), fill=color, width=thickness)
            sx, sy = x + 8, y + dimensions[1] + 15
            draw.line((sx, sy, sx + 5 * scale, sy), fill=MUTED, width=2)
            draw.text((sx + 5 * scale + 6, sy - 8), "5 mm", fill=MUTED, font=font(13))
    save(canvas, output, "protected-planes.webp")


def live_plate(side, captures, output):
    canvas = Image.new("RGB", (1438, 1130), BG)
    draw = title(
        canvas,
        f"{side.title()} carotid · frozen acquisitions in Chrome",
        "The staged swap changes the carotid exterior. Probe poses, scans and overlays use the previous bytes.",
    )
    for col, label in enumerate(
        ("Previous oblique", "r01 oblique", "Simulated B-mode", "Label overlay")
    ):
        draw.text((19 + col * 352, 88), label, font=font(18), fill=MUTED)
    for row, (frame, label) in enumerate(
        ((12, "Frame 12 · transverse"), (48, "Frame 48 · longitudinal"))
    ):
        top = 123 + 500 * row
        draw.text((19, top), label, fill=TEXT, font=font(22))
        for col, (version, view) in enumerate(
            (
                ("previous", "scene"),
                ("candidate", "scene"),
                ("candidate", "scan"),
                ("candidate", "overlay"),
            )
        ):
            path = captures / f"carotid-{side}-{version}-{frame}-{view}.png"
            fit(canvas, path, (19 + col * 352, top + 30, 342, 266))
        draw.text((19, top + 306), "Axial orbit · exact prior and r01", fill=MUTED, font=font(16))
        for col, version in enumerate(("previous", "candidate")):
            path = captures / f"carotid-{side}-{version}-{frame}-axial.png"
            fit(canvas, path, (19 + col * 352, top + 334, 342, 140))
    save(canvas, output, "live-frame-12.webp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("side", choices=("left", "right"))
    parser.add_argument("frozen", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("measurements", type=Path)
    parser.add_argument("clay", type=Path)
    parser.add_argument("captures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    brief = json.loads(args.frozen.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    clay_plate(args.side, args.clay, args.output, True)
    clay_plate(args.side, args.clay, args.output, False)
    planes_plate(args.side, brief, args.reference, args.measurements, args.output)
    live_plate(args.side, args.captures, args.output)


if __name__ == "__main__":
    main()
