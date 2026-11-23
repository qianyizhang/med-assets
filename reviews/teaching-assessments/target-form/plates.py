"""Compose the matched, hash-bound task plates from TAQ-016 replay outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / "refinement-form/compose-plates.py"
FONT = ROOT / "sources/fonts/dejavu/DejaVuSans.ttf"
PAPER, INK, BACK = "#f5f2e9", "#17242c", "#292a2b"
GAP, SIZE = 18, 410


def checked(folder, frame):
    path = folder / frame["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != frame["sha256"]:
        raise ValueError(f"Unexpected replay image: {path}")
    with Image.open(path) as image:
        return image.convert("RGBA")


def panel(image, mark=None):
    image.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (SIZE, SIZE), BACK)
    x = (SIZE - image.width) // 2
    y = (SIZE - image.height) // 2
    card.paste(image, (x, y), image)
    if mark:
        draw = ImageDraw.Draw(card)
        dot = "#f8dd85"
        for target, tail, *label in mark:
            px, py = target[0] * image.width + x, target[1] * image.height + y
            tx, ty = tail[0] * image.width + x, tail[1] * image.height + y
            draw.line((tx, ty, px, py), fill=INK, width=6)
            draw.line((tx, ty, px, py), fill=dot, width=2)
            draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=dot)
            if label:
                marker_font = ImageFont.truetype(FONT, 17)
                draw.text((tx, ty - 7), label[0], fill=dot, font=marker_font,
                          stroke_width=2, stroke_fill=INK)
    return card


def board(out, title, rows, notes):
    fonts = {size: ImageFont.truetype(FONT, size) for size in (24, 27, 39)}
    wrap = runpy.run_path(str(PRIOR))["wrap"]
    cols = max(len(row) for row in rows)
    width = GAP * (cols + 1) + SIZE * cols
    card = Image.new("RGB", (width, 93 + 453 * len(rows) + 300), PAPER)
    draw = ImageDraw.Draw(card)
    draw.text((GAP, 16), title, font=fonts[39], fill=INK)
    y = 76
    for row in rows:
        for index, (label, shot) in enumerate(row):
            x = GAP + index * (GAP + SIZE)
            if draw.textlength(label, font=fonts[24]) > SIZE:
                raise ValueError(f"Panel title overflows: {label}")
            draw.text((x, y), label, font=fonts[24], fill=INK)
            card.paste(shot, (x, y + 32))
        y += 456
    for note in notes:
        for line in wrap(draw, note, width - GAP * 2, fonts[27]):
            draw.text((GAP, y), line, font=fonts[27], fill=INK)
            y += 33
        y += 8
    card.crop((0, 0, width, y + 12)).save(out, format="WEBP", quality=95, method=6)


def paired_matched(folder, destination):
    records = json.loads((folder / "render.json").read_text())["assets"]

    def load(key, kind, frame, markers=None):
        image = next(ref for ref in records[key][kind] if ref["view"] == frame)
        return panel(checked(folder, image), markers)

    old = "original"
    new = "updated"
    bronchial = "bronchial"
    close = ["close", "rotated-close", "opposite-close"]
    angles = ["Front", "Lower oblique", "Opposite"]
    board(destination / "bronchial-comparison.webp", "First bronchial fork under neutral light",
          [[(f"{angle} · {revision}", load(bronchial, kind, view))
            for angle, view in zip(angles, close, strict=True)] for kind, revision in ((old, "r14"), (new, "r15"))],
          ["The hard collar and angular underside soften in the same 45 mm close-up. The trunk still divides into two distinct branches.",
           "Fairing changes the authored exterior around the first fork. Distal surfaces and all terminal caps retain their r14 geometry."])
    board(destination / "bronchial-first-fork-teaching.webp", "Follow the trunk into both main branches",
          [[("Whole schematic", load(bronchial, new, "whole")),
            ("First fork · front", load(bronchial, new, "close",
              [((.50, .42), (.70, .32), "Trunk"), ((.36, .67), (.04, .56), "Main branch"), ((.68, .68), (.72, .59), "Main branch")])),
            ("First fork · opposite", load(bronchial, new, "opposite-close"))]],
          ["Start from the trunk above the first split. Follow either arm of the Y before the next branches divide farther out.",
           "The close views share a 45 mm field. This solid schematic teaches the exterior branch pattern."])
    ovary = "ovary"
    trials, teaching = [], []
    for side, name in (("L", "Source-left"), ("R", "Source-right")):
        alt = f"{side}-alternate"
        tips_gap_edge = (
            [((.565, .245), (.70, .13), "Fimbria"), ((.585, .276), (.73, .25), "Gap"),
             ((.605, .295), (.76, .37), "Coarse edge")]
            if side == "L" else
            [((.665, .30), (.75, .21), "Fimbria"), ((.56, .264), (.71, .36), "Gap"),
             ((.39, .866), (.57, .82), "Flat end")]
        )
        trials.append([
            (f"{name} · original neutral", load(ovary, old, f"{alt}-neutral", tips_gap_edge[2:])),
            (f"{name} · matte neutral", load(ovary, new, f"{alt}-neutral", tips_gap_edge[2:])),
            (f"{name} · matte colors", load(ovary, new, alt)),
        ])
        teaching.append([
            (f"{name} · native", load(ovary, old, f"{side}-native")),
            (f"{name} · oblique", load(ovary, old, alt, tips_gap_edge[:2])),
        ])
    board(destination / "ovary-matte-trial.webp", "Matched ovarian finish trial",
          trials, ["The more matte finish reduces glare. The angular source edges and flattened right end still read at the same close-up.",
                   "Both alternatives leave the ovarian contours, fimbriae and separation exact. The original HRA export serves this task."])
    board(destination / "ovary-source-teaching.webp", "Find the fimbriae beside each ovary",
          teaching, ["Use each oblique to pick out the fingers of the fimbrial fringe beside the pale ovary. Point to the gap visible in this model.",
                     "Camera pairs keep their own scale. L/R follow source labels. These source contours teach the gross relationship."])


def paired_economy(folder, conservative, destination):
    for key, directory, title, names, note in (
        ("vagina_hra", folder, "Vaginal exterior and its pelvic neighbors",
         ("Side overview", "Side focus", "Opposite focus"),
         "The preserved cervix lies above the vaginal exterior, with bladder parts anterior and the rectum posterior."),
        ("anatomy-workshop-r1", folder, "The Workshop heart, lung lobes and liver",
         ("Full Workshop", "Anterior focus", "Posterior focus"),
         "The shape trial reduces five evaluated lobe meshes in a disposable snapshot. The native Workshop needs its editable scene and alternate configurations."),
        ("diaphragm", conservative, "Protected diaphragm dome comparison",
         ("Anterior", "Superior", "Inferior"),
         "The narrower trial preserves the two dome crests and center band, but the worst sampled deflection exceeds the review tolerance. Retain the atlas surface."),
        ("nose_sinuses", conservative, "Protected nasal cast comparison",
         ("Front", "Oblique", "Reverse oblique"),
         "The contraction trial preserves the central channel band. A sampled lateral position still moves beyond the review tolerance. Retain the exact cast."),
        ("heart", conservative, "Protected s1233 heart shell comparison",
         ("Front oblique", "Reverse", "Upper oblique"),
         "The trial preserves the superior band. A shell sample near the ventricular margin shifts beyond the tolerance. Retain the exact display shell."),
    ):
        asset_folder = directory / key
        receipt = json.loads((asset_folder / "result.json").read_text())
        replica = "trial" if key == "anatomy-workshop-r1" else "candidate"
        option = "r03 focus" if key == "vagina_hra" else "trial"
        rows = []
        for variant, label in (("control", "original"), (replica, option)):
            markers = (None, None, None)
            if key == "vagina_hra" and variant == "candidate":
                markers = (None,
                           [((.49, .48), (.32, .40), "Cervix"), ((.47, .69), (.51, .79), "Vaginal exterior"),
                            ((.22, .53), (.12, .40), "Bladder"), ((.80, .27), (.73, .11), "Rectum")],
                           None)
            rows.append([(f"{name} · {label}", panel(checked(asset_folder, frame), marks))
                         for name, frame, marks in zip(names, receipt["bindings"][variant], markers, strict=True)])
        board(destination / f"{key}-comparison.webp", title, rows, [note])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matched", type=Path)
    parser.add_argument("economy", type=Path)
    parser.add_argument("conservative", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paired_matched(args.matched, args.output)
    paired_economy(args.economy, args.conservative, args.output)


if __name__ == "__main__":
    main()
