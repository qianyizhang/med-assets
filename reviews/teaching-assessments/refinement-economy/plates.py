"""Bind compact matched evidence to one verified trial run."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def identity_file(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data)}


def open_frames(source, bindings):
    result = []
    for frame in bindings:
        path = source / frame["file"]
        if identity_file(path)["sha256"] != frame["sha256"]:
            raise ValueError(f"Raw capture digest mismatch for {path}")
        result.append(Image.open(path).convert("RGBA"))
    return result


def silhouette(control, candidate):
    """Chebyshev distance of foreground masks sampled at the native render size."""
    left, right = (im.getchannel("A").point(lambda x: 255 if x >= 128 else 0)
                   for im in (control, candidate))
    for distance in range(7):
        a, b = (im.filter(ImageFilter.MaxFilter(2 * distance + 1)) for im in (left, right))
        if (not ImageChops.subtract(left, b).getbbox()
                and not ImageChops.subtract(right, a).getbbox()):
            return distance
    return ">6"


def plate(path, images, label):
    width, height = images[0].size
    banner = 40
    paper = Image.new("RGB", (width * len(images), height + banner), (35, 37, 40))
    font = ImageFont.load_default(size=17)
    draw = ImageDraw.Draw(paper)
    for i, image in enumerate(images):
        paper.paste(image, (width * i, banner), image.getchannel("A"))
    draw.text((17, 11), f"{label} / View 1", fill="#eeeeee", font=font)
    draw.text((width + 17, 11), f"{label} / View 2", fill="#eeeeee", font=font)
    draw.line((width, 0, width, height + banner), fill="#484b50")
    paper.save(path, format="WEBP", quality=86, method=6)


def failure_plate(path, image, row):
    """Show the actual protected-surface result with its original diagnostic view."""
    width, height = image.size
    banner = 40
    paper = Image.new("RGB", (width * 2, height + banner), (35, 37, 40))
    paper.paste(image, (0, banner), image.getchannel("A"))
    draw = ImageDraw.Draw(paper)
    title, font = ImageFont.load_default(size=18), ImageFont.load_default(size=17)
    draw.text((17, 11), "Original / Protected detail", fill="#eeeeee", font=title)
    draw.text((width + 17, 11), "Failed trial / Geometry receipt", fill="#eeeeee", font=title)
    draw.line((width, 0, width, height + banner), fill="#484b50")
    x, y = width + 25, 106
    draw.text((x, y), "No lighter GLB passed the protected-surface check.", fill="#f4f1ea", font=font)
    y += 47
    draw.text((x, y), "Selected primitive", fill="#f4f1ea", font=font)
    draw.text((x + 285, y), "Triangles removed", fill="#f4f1ea", font=font)
    draw.text((x + 449, y), "Vertices locked", fill="#f4f1ea", font=font)
    y += 42
    for part in row["parts"]:
        nice_name = (part["name"].replace("VH_F_cartilage_of_", "").replace("_bronchus", " bronchus")
                     .replace("_", " ").replace(" | source surface", ""))
        before = part["beforeTriangles"]
        removed = before - part["attempts"][-1]["triangles"]
        draw.text((x, y), nice_name, fill="#d5d9df", font=font)
        draw.text((x + 285, y), f"{removed:,} / {before:,}", fill="#d5d9df", font=font)
        draw.text((x + 449, y), f"{part['lockedVertices']:,} / {part['vertices']:,}", fill="#d5d9df", font=font)
        y += 39
    y += 25
    if row["name"] == "lung_left":
        part, = row["parts"]
        attempted = part["attempts"][1]
        removed = part["beforeTriangles"] - attempted["triangles"]
        px = attempted["worstSamplePixels"]
        draw.text((x, y), f"The intermediate pass removed {removed:,} triangles.", fill="#d5d9df", font=font)
        y += 34
        draw.text((x, y), f"Displacement reached {px:.2f} px against a 0.73 px limit.", fill="#d5d9df", font=font)
        y += 34
    draw.text((x, y), "Minimum reduction per part at this zoom was 4%.", fill="#d5d9df", font=font)
    draw.text((x, y + 34), "Index seams, boundaries and neighboring faces were held.", fill="#d5d9df", font=font)
    paper.save(path, format="WEBP", quality=86, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = []
    source = args.run.resolve()
    folder = args.out.resolve()
    if not source.is_relative_to(ROOT / ".artifacts") or not folder.is_relative_to(ROOT):
        parser.error("Use a repository trial run and in-repository evidence directory")
    folder.mkdir(parents=True, exist_ok=False)
    for row in json.loads((source / "index.json").read_text()):
        name = row["name"]
        if "error" in row:
            raise ValueError(f"Unresolved recipe failure for {name}")
        bindings = row["bindings"]
        left = open_frames(source / name, bindings["control"])
        right = None
        if row["candidate"]:
            for a, b in zip(bindings["control"], bindings["candidate"], strict=True):
                if any(a[key] != b[key] for key in ("camera", "location", "rotation", "clip", "ortho")):
                    raise ValueError(f"Comparison cameras differ for {name}")
            right = open_frames(source / name, bindings["candidate"])
            row["silhouetteShiftPx"] = [silhouette(a, b) for a, b in zip(left, right, strict=True)]
        before = folder / f"{name}-original.webp"
        plate(before, left, "Original")
        row["beforeView"] = identity_file(before)
        if right:
            rejected = row.get("rejectedPreview", False)
            suffix, label = ("rejected", "Rejected trial") if rejected else ("trial", "Trial")
            after = folder / f"{name}-{suffix}.webp"
            plate(after, right, label)
            row["afterView"] = identity_file(after)
        elif row["parts"] and all(part.get("attempts") for part in row["parts"]):
            after = folder / f"{name}-failed-diagnostic.webp"
            failure_plate(after, left[-1], row)
            row["afterView"] = identity_file(after)
            row["afterViewStatus"] = "failed-trial-diagnostic"
        result.append(row)
    # Store the comprehensive per-part measurements separately from the campaign rows.
    (folder.parent / "measurements.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
