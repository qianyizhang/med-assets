"""Compose bilingual teaching plates from the bound clean-import renders."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PANELS = {
    "parotid": [
        ("parotid", "ortho", "Anterior · 前面观"),
        ("parotid", "iso", "Oblique · 斜位观"),
    ],
    "duct-course": [
        ("duct-course", "ortho", "Gland pairs and ducts · 腺体与导管"),
        ("duct-course", "iso", "Gross parotid course · 腮腺管大体走行"),
    ],
    "jaw-context": [
        ("jaw-context", "ortho", "Mandible and masseter · 下颌骨与咬肌"),
        ("oral-floor", "ortho", "Jaw and lower glands isolated · 下颌骨与口底腺体单独显示"),
    ],
}
DUCT_IN_CONTEXT = ("jaw-context", "ortho", "Duct over masseter · 腮腺管经过咬肌表面")


def hash_file(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def panel(renders, rows, role, angle, revision, width):
    expected = next(
        image for image in rows[role][revision]["images"] if image["file"].endswith(f"-{angle}.png")
    )
    path = renders / expected["file"]
    assert hash_file(path) == expected["sha256"], path
    model = Image.open(path).convert("RGBA")
    layer = Image.new("RGBA", model.size, "#222e39")
    layer.alpha_composite(model)
    return layer.convert("RGB").resize((width, width * model.height // model.width), Image.Resampling.LANCZOS)


def plate(renders, rows, views, output, font_file, *, compare):
    width = 468 if compare else 570
    pad = 14
    banner = 36 if compare else 0
    label_height = 38
    tile_height = width * 4 // 5
    block_height = label_height + tile_height + pad
    rows_count = 2 if compare else 1
    image = Image.new("RGB", (2 * width + 3 * pad, pad + banner + rows_count * block_height), "#14202b")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_file), 18)
    revisions = ("original", "updated") if compare else ("updated", "updated")
    for column, revision in enumerate(revisions):
        x = pad + column * (width + pad)
        if compare:
            title = "Original · 原导出" if revision == "original" else "Updated · 更新导出"
            draw.text((x, pad + 4), title, font=font, fill="#f4f7f9")
        for row, (role, angle, title) in enumerate(views if compare else (views[column],)):
            y = pad + banner + row * block_height
            draw.text((x, y + 8), title, font=font, fill="#edf3f5")
            image.paste(panel(renders, rows, role, angle, revision, width), (x, y + label_height))
    image.save(output, format="WEBP", quality=94, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("renders", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--font", type=Path, default=Path("/System/Library/Fonts/STHeiti Medium.ttc"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = {row["view"]: row for row in json.loads((args.renders / "renders.json").read_text())["views"]}
    for role, views in PANELS.items():
        plate(args.renders, rows, views, args.out / f"{role}-matched.webp", args.font, compare=True)
        teaching = (views[0], DUCT_IN_CONTEXT) if role == "duct-course" else views
        plate(args.renders, rows, teaching, args.out / f"{role}-poster.webp", args.font, compare=False)


if __name__ == "__main__":
    main()
