"""Compose the source and edition views from the matched clean imports."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAMES = {
    "adrenals": (
        "The two adrenal profiles against their kidneys",
        [
            "Posterior · gland profiles",
            "Reverse · neutral",
            "Left profile · enlarged",
            "Posterior · kidney context",
        ],
        "Match the crescent-shaped left gland and the more triangular right gland to the kidney on the same side.",
        [
            "The kidney panel adds the source atlas reference to the original gland-only export.",
            "This interpreted edition includes the exact atlas kidneys. The restrained surface shows gross profiles.",
        ],
    ),
    "pancreas": (
        "Trace the pancreas from the duodenal bend toward the spleen",
        [
            "Front oblique · gross region",
            "Reverse · neutral",
            "Head and adjacent body · enlarged",
        ],
        "In the first view, start at the head inside the bend at left and trace the body to the tail beside the spleen at right.",
        [
            "Five source regions are shown with the duct roles hidden. The close view isolates the pancreas.",
            "A single interpreted exterior spans the source regions. The duodenal and splenic context stays in the atlas frame.",
        ],
    ),
    "lymph": (
        "Follow the central collecting trace to its two source limits",
        [
            "Seven source routes",
            "Central trace · enlarged",
            "Oblique · same tracing task",
        ],
        "Follow the central trace from its lower end to its upper turn. The oblique view separates it from the side guides.",
        [
            "The source model uses faceted tubes. The terminal caps mark where its samples stop.",
            "Gold symbols mark the exact centers of both source caps. Line width and corner interpolation are diagram conventions.",
        ],
    ),
}


def draw(group, side, source, output, receipt):
    title, labels, task, notes = NAMES[group]
    cols = 2 if group == "adrenals" else 3
    pane = 460 if cols == 2 else 392
    rows = 2 if cols == 2 else 1
    sheet = Image.new(
        "RGB", (cols * (pane + 12) + 12, 110 + (pane + 36) * rows + 58), "#f5f3eb"
    )
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    body_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), title, fill="#253031", font=title_font)
    d.text((12, 50), task, fill="#343b3e", font=body_font)
    d.text(
        (12, 78),
        "Source study" if side == "before" else "Reviewed teaching edition",
        fill="#334f4c",
        font=body_font,
    )
    for i, view in enumerate(receipt[group][side]):
        image_path = source / view["file"]
        if hashlib.sha256(image_path.read_bytes()).hexdigest() != view["sha256"]:
            raise ValueError(f"Changed clean-import image: {image_path}")
        im = (
            Image.open(image_path)
            .convert("RGB")
            .resize((pane, pane), Image.Resampling.LANCZOS)
        )
        x = 12 + (i % cols) * (pane + 12)
        y = 110 + (i // cols) * (pane + 36)
        d.text((x, y), labels[i], fill="#343b3e", font=body_font)
        sheet.paste(im, (x, y + 24))
    d.text(
        (12, sheet.height - 46),
        notes[int(side == "after")],
        fill="#253031",
        font=body_font,
    )
    sheet.save(output / f"{group}-{side}.webp", quality=90, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = json.loads((args.source / "measurements.json").read_text())
    for group in NAMES:
        for side in ("before", "after"):
            draw(group, side, args.source, args.output, receipt)


if __name__ == "__main__":
    main()
