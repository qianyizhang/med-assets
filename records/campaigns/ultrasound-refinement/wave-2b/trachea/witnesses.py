"""Compose the matched s1127 tracheal surface, section and live-reader witnesses."""

import argparse
import json
import runpy
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
STYLE = runpy.run_path(str(HERE.parent / "ivc/witnesses.py"))
canvas, note, place, save = (STYLE[key] for key in ("canvas", "note", "place", "save"))
NAMES = {"trachea": "Full label", "thyroid": "Thyroid crop", "carotid": "Carotid crop"}


def clay(renders, output):
    cell = (306, 360)
    for previous in (True, False):
        name = "previous-vs-r01" if previous else "matched-surfaces"
        first = "previous" if previous else "raw"
        roles = ("thyroid", "carotid") if previous else ("trachea", "thyroid", "carotid")
        title = (
            "Tracheal exterior · previous and r01"
            if previous
            else "Tracheal air column · half-label and r01"
        )
        page, draw = canvas(
            title,
            "Neutral clay at matched scale and orientation within each pair.",
            4,
            len(roles),
            cell,
        )
        for row, scope in enumerate(roles):
            for col, (view, version, label) in enumerate(
                (
                    ("anterior", first, "Prior" if previous else "CT"),
                    ("anterior", "r01", "r01"),
                    ("detail", first, "Prior detail" if previous else "CT detail"),
                    ("detail", "r01", "r01 detail"),
                )
            ):
                path = renders / f"{scope}-{view}-{version}.png"
                place(page, draw, Image.open(path), f"{NAMES[scope]} · {label}", col, row, cell)
        save(page, output, name)


def decode(path, affine):
    receipt = path.read_bytes()
    count, triangles = struct.unpack_from("<2I", receipt)
    points = np.frombuffer(receipt, "<f4", count * 3, 8).reshape(-1, 3)
    faces = np.frombuffer(receipt, "<u4", triangles * 3, 8 + count * 12).reshape(-1, 3)
    xyz = np.einsum("vi,ji->vj", points, affine[:3, :3]) + affine[:3, 3]
    return xyz[faces]


def planes(frozen, reference, measured, output):
    cell = (446, 315)
    page, draw = canvas(
        "Tracheal exterior · protected contours",
        "Gold · raw CT half-label     Lavender · exact prior crop     Cyan · r01",
        3,
        2,
        cell,
    )
    schemes = STYLE["STYLES"]
    prior = Path(frozen["baselineAssembly"]) / "stage"
    affine = np.asarray(frozen["source"]["rasMmFromVoxel"])
    helper = runpy.run_path(str(HERE.parent / "carotid/freeze_carotid.py"))["wave"]
    panels = (
        ("thyroid", 3, "Transverse frame 0 · saved cut"),
        ("thyroid", 7, "Right frame 12 · +1.5 mm"),
        ("thyroid", 14, "Left frame 48 · −1.5 mm"),
        ("trachea", 2, "Full label · two distal branches"),
        ("thyroid", 0, "Thyroid crop · inferior cut"),
        ("carotid", 0, "Carotid crop · inferior cut"),
    )
    for col, (scope, index, caption) in enumerate(panels):
        data = frozen["exports"][scope]
        plane = data["planes"][index]
        origin, normal = (np.asarray(plane[key]) for key in ("originRasMm", "normal"))
        basis = np.asarray([plane["width"], plane["beam"]])
        with np.load(reference / f"{scope}-reference.npz", allow_pickle=False) as raw:
            ct, outline = raw[f"ct{index}"], raw[f"outline{index}"]
        with np.load(measured / f"final-{scope}.npz", allow_pickle=False) as mesh:
            candidate = mesh[f"outline{index}"]
        low, high = np.asarray(plane["bounds"])
        width, height = high - low
        zoom = min((cell[0] - 22) / width, (cell[1] - 52) / height)
        size = round(width * zoom), round(height * zoom)
        panel = Image.new("RGB", cell, schemes["BACK"])
        draw_panel = ImageDraw.Draw(panel)
        offset = np.array([(cell[0] - size[0]) / 2, 6])
        img = Image.fromarray(np.clip((ct + 720) * 0.30, 0, 255).astype(np.uint8))
        panel.paste(img.resize(size, Image.Resampling.BILINEAR), tuple(offset.astype(int)))
        lines = [(outline, schemes["CT"], 5)]
        if "prior" in data:
            previous = decode(prior / data["prior"]["stage"]["path"], affine)
            lines.append((helper.cut(previous, origin, normal), schemes["PREVIOUS"], 2))
        lines.append((candidate, schemes["CANDIDATE"], 2))
        for contour, color, weight in lines:
            xy = np.einsum("...i,ji->...j", contour - origin, basis)
            for a, b in (xy - low) * zoom + offset:
                draw_panel.line((tuple(a), tuple(b)), fill=color, width=weight)
        y = size[1] + 24
        draw_panel.line((offset[0], y, offset[0] + zoom * 5, y), fill=schemes["INK"], width=3)
        note(draw_panel, (offset[0] + zoom * 5 + 8, y - 8), "5 mm", 16)
        place(page, draw, panel, caption, col % 3, col // 3, cell)
    save(page, output, "protected-planes")


def live(captures, output):
    cell = (340, 315)
    page, draw = canvas(
        "Trachea beneath the thyroid · s1127 in Chrome",
        "Exact mesh and acquisition responses checked in the standalone sweep. Frame 0 is the chapter companion.",
        4,
        2,
        cell,
    )
    for row, frame in enumerate((0, 12)):
        for col, (version, image, label) in enumerate(
            (
                ("previous", "scene", "Prior 3D"),
                ("candidate", "scene", "r01 3D"),
                ("candidate", "scan", "Simulated scan"),
                ("candidate", "overlay", "Tissue overlay"),
            )
        ):
            path = captures / f"thyroid-right-{version}-{frame}-{image}.png"
            place(page, draw, Image.open(path), f"{frame} · {label}", col, row, cell)
    save(page, output, "live-frame-12")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "measured", "renders", "captures", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    frozen = json.loads((HERE / "reference.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    clay(args.renders, args.output)
    planes(frozen, args.reference, args.measured, args.output)
    live(args.captures, args.output)


if __name__ == "__main__":
    main()
