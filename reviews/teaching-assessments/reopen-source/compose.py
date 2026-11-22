"""Compose concise matched readouts from the retained camera recipes."""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FNT = ROOT / "experiments/dental-video-treatments/fonts/DejaVuSans.ttf"
BG = "#f2f1eb"
INK = "#253337"
M = 16
SIZE = 372


def board(inp, out, title, subtitle, rows, foot):
    im = Image.new("RGB", (M * 3 + 2 * SIZE, 160 + len(rows) * (SIZE + 35) + 68), BG)
    draw = ImageDraw.Draw(im)

    def label(x, y, text, size):
        draw.text((x, y), text, fill=INK, font=ImageFont.truetype(FNT, size))

    label(M, 14, title, 27)
    for i, line in enumerate(subtitle):
        label(M, 56 + i * 22, line, 16)
    y = 56 + len(subtitle) * 22 + 15
    for row in rows:
        for j, (file, caption) in enumerate(row):
            x = M + j * (SIZE + M)
            label(x, y, caption, 17)
            source = (
                Image.open(inp / (file + ".png"))
                .convert("RGBA")
                .resize((SIZE, SIZE), Image.Resampling.LANCZOS)
            )
            bg = Image.new("RGB", (SIZE, SIZE), "#35393c")
            bg.paste(source, mask=source.getchannel("A"))
            im.paste(bg, (x, y + 26))
        y += SIZE + 39
    for line in foot:
        label(M, y, line, 16)
        y += 22
    im.crop((0, 0, im.width, y + M)).save(out, quality=92, method=6)


def compose(inp, out):
    board(
        inp,
        out / "ovary-comparison.webp",
        "Ovary beside the fimbrial fringe",
        [
            "Matched 38–39 mm oblique fields under the same neutral studio light.",
            "The ovary exterior is interpreted. All eight tubal meshes retain their original shape.",
        ],
        [
            [
                (
                    f"ovary-{s}-alternate-{e}",
                    f"{'Original HRA' if e == 'original' else 'Interpreted exterior'} · source {s}",
                )
                for e in ("original", "interpreted")
            ]
            for s in ("L", "R")
        ],
        [
            "Look at the turn around the lower ovarian pole. The angular edges soften on each side.",
            "The upper contour beside the fimbrial tips retains the HRA relationship.",
        ],
    )
    board(
        inp,
        out / "ovary-teaching.webp",
        "Find the fimbrial end beside each ovary",
        [
            "Exact interpreted GLB with HRA materials. L/R follow the source labels.",
            "Pink finger-like tips lie across a visible gap from the pale ovary.",
        ],
        [
            [(f"ovary-teaching-{s}-{view}", f"{s} · {view} view") for s in ("L", "R")]
            for view in ("native", "alternate")
        ],
        [
            "The alternate views expose the gap on both sides. No tissue attachment is inferred.",
            "Only the ovarian exterior is interpreted. The tubal contours are unchanged.",
        ],
    )
    board(
        inp,
        out / "hypothalamus.webp",
        "Identify the paired envelopes and inferior stalk",
        [
            "Matched BP3D views. Compare the original target with the same atlas’s third ventricle.",
            "The four registered coronal sections establish where the lower ventricular form sits.",
        ],
        [
            [
                (
                    f"hypothalamus-{i}-{e}",
                    ("Original envelopes" if e == "original" else "Third ventricle added")
                    + (" · posterior" if i == 0 else " · side"),
                )
                for e in ("original", "ventricle")
            ]
            for i in (0, 1)
        ],
        [
            "The lower projection remains visible from the side. Teal is separate atlas context.",
            "The sections resolve the recess at this atlas scale. The source has no traced nuclei.",
        ],
    )
    board(
        inp,
        out / "parathyroid.webp",
        "Posterior localization with four source targets",
        [
            "Original gland shapes and a trial of four equally sized position symbols.",
            "Both use the same atlas thyroid, camera and original gland centers.",
        ],
        [
            [
                (
                    f"parathyroid-{i}-{e}",
                    ("Original" if e == "original" else "Position symbols")
                    + (" · posterior" if i == 0 else " · oblique"),
                )
                for e in ("original", "symbols")
            ]
            for i in (0, 1)
        ],
        [
            "The symbols conceal each gland’s extent and imply equal sizes. The projection persists.",
            "Use the source shapes for this four-position example. Their mirrored outlines are simplified.",
        ],
    )
    board(
        inp,
        out / "parathyroid-extents.webp",
        "Preserve upper and lower marker dimensions",
        [
            "Both columns use the same thyroid, gland centers and original orientation.",
            "The trial ellipsoids match each atlas gland’s spans on all three principal axes.",
        ],
        [
            [
                (
                    f"parathyroid-{i}-{e}",
                    ("Original gland" if e == "original" else "Extent-matched marker")
                    + (" · posterior" if i == 0 else " · oblique"),
                )
                for e in ("original", "oriented")
            ]
            for i in (0, 1)
        ],
        [
            "Upper glands span 4.70 mm, lower glands 4.45 mm on their long axes in both editions.",
            "The mirrored pairs and unassigned midline thyroid projection persist at this field.",
        ],
    )
    board(
        inp,
        out / "fdi31-bone-trial.webp",
        "Prepared incisor  |  Exposed bone projection",
        [
            "Balanced and the same 60,310 bone triangles projected toward interface-locked detail.",
            "The native-label tooth interface, acquisition edge and small islands were held fixed.",
        ],
        [
            [
                (
                    f"fdi-{i}-{e}",
                    ("Original" if e == "original" else "Projected bone")
                    + (" · whole" if i == 0 else " · 12 mm detail"),
                )
                for e in ("original", "projected")
            ]
            for i in (0, 2)
        ],
        [
            "478 exposed vertices moved by up to 0.084 mm. The rough bone margin remains.",
            "Interior section discrepancy at y = 8.56 mm changes from 0.373 to 0.372 mm.",
        ],
    )
    board(
        inp,
        out / "penis.webp",
        "Test the distal rim against its native atlas context",
        [
            "Original component export and the registered Z-Anatomy urethral curve, in teal.",
            "The two angles share the same scale and use the source object transforms.",
        ],
        [
            [
                (
                    f"penis-{i}-{e}",
                    ("Components only" if e == "original" else "Same-frame urethra added")
                    + (" · first angle" if i == 0 else " · reverse oblique"),
                )
                for e in ("original", "registered")
            ]
            for i in (0, 1)
        ],
        [
            "The visible spot persists on the glans alone. The teal curve crosses its surface.",
            "Its 12 terminal vertices are 8.26–8.84 mm from the three defective source edges.",
        ],
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    compose(a.input, a.output)
