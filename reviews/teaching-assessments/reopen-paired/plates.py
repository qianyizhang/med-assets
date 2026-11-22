"""Assemble checked original/edition renders and source-supported task sections."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
layout = runpy.run_path(str(HERE.parent / "target-form/plates.py"))
FONT = ROOT / "experiments/dental-video-treatments/fonts/DejaVuSans.ttf"
NAMES = {
    "anatomy-workshop-r1": (
        "Workshop thorax",
        ["Anterior selection", "Posterior selection"],
        "Find the heart between the two lungs, then follow the lower lobes above the liver.",
        "The coronal CT cuts pass within 0.5 mm of the largest measured inferior-quarter discrepancies on each side. The lower lobar contours turn along the dark lung bases. The surface rounds fine label steps.",
        "TotalSegmentator v2.0.1, case s1233. Each slice uses the native RAS frame and its own crop.",
    ),
    "heart": (
        "Heart shell and superior sweep",
        ["Anterior oblique", "Reverse oblique", "Superior oblique"],
        "Find the rounded ventricular mass below the superior sweep. Turn the shell to separate them in depth.",
        "The transverse and coronal cuts show the exported contour following the heart label beside a separately labeled aorta. Read the abrupt upper sweep as the extent of this segmented shell. The closed exterior provides no view of a vessel lumen.",
        "TotalSegmentator v2.0.1, case s1233. CT cuts use the native RAS frame and independent crops.",
    ),
    "diaphragm": (
        "Diaphragm domes and inferior extensions",
        ["Anterior", "Superior", "Inferior"],
        "Compare the higher right dome with the left in front view. Turn underneath to find the round opening and the paired descending contours.",
        "The center of the atlas caval section lies inside the projected hole, 1.53 mm from its centroid. At L1, the two descending contours flank the vertebral body. The overlays establish location. Their edges differ and cannot establish a sealed join or an attachment.",
        "Z-Anatomy and BodyParts3D. Same native frame; aperture detail and axial cut enlarged independently.",
    ),
    "lymph": (
        "Capsule and three tissue regions",
        ["Capsule", "Exposed tissues", "Medulla • reverse"],
        "Trace the capsule outline, then hide it to locate the follicles, paracortex and medulla.",
        "Two planes through the four HRA tissues show the large medullary territory amid the other regions. Individual clefts recur in the source surface. Tissue identity at those clefts and at the capsule aperture remains unresolved.",
        "HuBMAP, Browne and Schlehlein, 2022. Section colors identify source surfaces.",
    ),
    "nose_sinuses": (
        "Central and lateral airspaces",
        ["Front", "Oblique", "Reverse oblique"],
        "Follow the narrow central cast and distinguish the broad paired lateral recesses. Rotate to compare their depth.",
        "The lower section shows two broad side spaces around thin central channels. The second cut samples the more divided superior cast. The solid models where air was present. The uneven lower cutoff is a limit of the cast.",
        "NIH 3D 3DPX-002305, Nevit Dilmen. Section positions use the centered display frame with no inferred physical units.",
    ),
}


def checked_frame(folder, row):
    p = folder / row["file"]
    if hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError(f"Render binding failed for {p}")
    return Image.open(p).convert("RGBA")


def backdrop(im):
    im.thumbnail((500, 410), Image.Resampling.LANCZOS)
    p = Image.new("RGB", (520, 430), layout["BACK"])
    p.paste(im, ((520 - im.width) // 2, (430 - im.height) // 2), im)
    return p


def teaching(out, name, images, sections, notes):
    width, gap = 1088, 16
    font = {n: ImageFont.truetype(FONT, n) for n in (20, 22, 29, 34)}
    paper, ink = layout["PAPER"], layout["INK"]
    card = Image.new("RGB", (width, 1900), paper)
    d = ImageDraw.Draw(card)
    d.text((gap, 12), name, font=font[34], fill=ink)

    def paragraph(text, y, size):
        words = text.split()
        line = ""
        for word in words:
            draft = " ".join((line, word)).strip()
            if d.textlength(draft, font=font[size]) > width - 2 * gap:
                d.text((gap, y), line, font=font[size], fill=ink)
                line = word
                y += size + 8
            else:
                line = draft
        d.text((gap, y), line, font=font[size], fill=ink)
        return y + size + 14

    y = paragraph(notes[0], 62, 22)
    for j, (cap, im) in enumerate(images):
        x = gap + j * (520 + gap)
        d.text((x, y), cap, font=font[22], fill=ink)
        card.paste(backdrop(im), (x, y + 32))
    y += 478
    for j, im in enumerate(sections):
        card.paste(im, (gap + j * (520 + gap), y))
    y += 535
    y = paragraph(notes[1], y, 22)
    y = paragraph(notes[2], y, 20)
    card.crop((0, 0, width, y + 8)).save(out, "WEBP", quality=94, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("matched", "sections", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    render = json.loads((args.matched / "render.json").read_text())
    section_pins = json.loads((args.sections / "sections.json").read_text())["inputs"][
        "sectionsSha256"
    ]
    for name, pin in section_pins.items():
        if hashlib.sha256((args.sections / name).read_bytes()).hexdigest() != pin:
            raise ValueError("Registered section image differs from its source receipt")
    result = {}
    for key, (name, views, *notes) in NAMES.items():
        case = render[key]
        cols = {}
        for side in ("source", "edition"):
            cols[side] = [
                checked_frame(args.matched / key, r) for r in case[side]["views"]
            ]
        result[key] = []
        for i, (a, b) in enumerate(zip(cols["source"], cols["edition"])):
            diff = np.abs(np.asarray(a, dtype="int16") - np.asarray(b, dtype="int16"))
            result[key].append(
                {
                    "angle": views[i],
                    "rgbaDifferentPixels": int(np.any(diff, axis=2).sum()),
                    "maxChannel8bit": int(diff.max()),
                    "alphaDifferentPixels": int((diff[:, :, 3] != 0).sum()),
                }
            )
        rows = [
            [
                (f"{label} • {v}", layout["panel"](im.copy()))
                for v, im in zip(views, cols[side])
            ]
            for side, label in (("source", "Original"), ("edition", "Updated"))
        ]
        layout["board"](
            args.output / f"{key}-comparison.webp",
            name,
            rows,
            [
                "Matched views of the exact original and compact edition. The same camera, framing and broad studio highlight apply down each column.",
                notes[0],
            ],
        )
        main_views = [0, 2] if key == "diaphragm" else [0, 1]
        teaching(
            args.output / f"{key}-teaching.webp",
            name,
            [(views[i], cols["edition"][i].copy()) for i in main_views],
            [Image.open(args.sections / f"{key}-{i}.png") for i in range(2)],
            notes,
        )
    (args.output.parent / "pixels.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
