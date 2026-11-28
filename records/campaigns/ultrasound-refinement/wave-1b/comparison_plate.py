"""Pair exact-delivery clay renders and saved frame-12 player captures."""

import argparse
from pathlib import Path

from PIL import Image
from witnesses import BG, INK, MUTED, label, save, thumbnail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    plate = Image.new("RGB", (1112, 1090), BG)
    label(plate, (18, 12), "Right kidney  |  comparison of delivered surfaces", 27, INK)
    label(plate, (166, 66), "Previous sweep  ·  23,156 triangles", 20)
    label(plate, (644, 66), "r01  ·  4,800 triangles", 20)
    rows = [
        ("Overview", "clay/overview", 235),
        ("Medial recess", "clay/reverse", 235),
        ("Inferior surface", "clay/inferior", 235),
        ("Sweep frame 12", "player", 232),
    ]
    top = 103
    for caption, name, height in rows:
        label(plate, (12, top + height // 2), caption, 16, MUTED)
        for index in range(2):
            thumbnail(
                plate, args.captures / f"{name}-{index}.png", 150 + index * 478, top, 464, height
            )
        top += height + 10
    save(plate, args.output, "previous-vs-r01.webp")


if __name__ == "__main__":
    main()
