"""Compose the matched s1127 shoulder comparison. Keep revision names off the plate."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clay", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paper, ink, quiet = "#19242d", "#f5f6f7", "#b8c7d2"
    width, height = 420, 287
    sheet = Image.new("RGB", (width * 3 + 32, 1038), paper)
    font = ImageFont.load_default(size=24)
    small = ImageFont.load_default(size=18)
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 10), "Which left thyroid shoulder has the most continuous surface?", fill=ink, font=font)
    draw.text((12, 45), "Follow the outline and the highlight around the upper lobe. The box marks the close-up.", fill=quiet, font=small)
    # Indices from the renderer are r03=0, raw reference=1, r04=2, r01=3.
    for col, (letter, index) in enumerate(zip("ABC", (3, 2, 0), strict=True)):
        x = 8 + col * (width + 8)
        draw.text((x, 74), letter, fill=ink, font=font)
        for row, (view, label) in enumerate((
            ("overview", "Front overview"), ("shoulder", "Front close-up"),
            ("shoulder-side", "Side close-up"),
        )):
            y = 105 + row * (height + 23)
            draw.text((x + 2, y), label, fill=quiet, font=small)
            with Image.open(args.clay / f"{view}-{index}.png") as frame:
                image = frame.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            if view == "overview":
                marker = ImageDraw.Draw(image)
                marker.rectangle((247, 48, 327, 137), outline="#ebc874", width=2)
            sheet.paste(image, (x, y + 22))
    sheet.save(args.output, "WEBP", quality=94, method=6)


if __name__ == "__main__":
    main()
