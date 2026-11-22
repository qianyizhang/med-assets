"""Make the two independently bound plates for each teaching task and measure pixel differences."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

HERE = Path(__file__).resolve().parent
LABELS = {
    "brain": ["Cerebral hemispheres", "Cerebellum and exposed stem", "Cerebellar surface in isolation"],
    "liver": ["Anterior capsule", "Posterior bare area and ligaments", "Bare-area margin in neutral light"],
    "muscle": ["Anterior muscle groups", "Posterior shoulders and back", "Pectoral and abdominal detail"],
    "spinal_cord": ["Representative levels", "Upper level 7 / dorsal swelling and ventral root"],
    "trachea": ["Proximal mouth and distal ends", "Open posterior bands", "Posterior C-band tips", "First distal cut face", "Opposite distal cut face"],
    "stomach": ["Exterior / front", "Authored section / front", "Exterior / oblique", "Authored section / oblique"],
}
STOMACH = ["front-exterior", "front-section", "oblique-exterior", "oblique-section"]


def bound_image(folder, info):
    path = folder / info["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
        raise ValueError(f"Frame identity mismatch in {path}")
    return Image.open(path).convert("RGBA")


def write_plate(path, frames, labels, title):
    size = frames[0].width
    cols = min(3, len(frames)) if len(frames) != 4 else 2
    rows = (len(frames) + cols - 1) // cols
    paper = Image.new("RGB", (size * cols, 46 + (size + 40) * rows), "#292b30")
    draw = ImageDraw.Draw(paper)
    draw.text((15, 10), title, font=ImageFont.load_default(size=22), fill="white")
    for i, (frame, label) in enumerate(zip(frames, labels, strict=True)):
        x = size * (i % cols)
        y = 46 + (size + 40) * (i // cols)
        paper.paste(frame, (x, y + 40), frame.getchannel("A"))
        draw.text((x + 15, y + 9), label, font=ImageFont.load_default(size=18), fill="#dce2ea")
    paper.save(path, format="WEBP", quality=90, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    settings = json.loads((HERE / "editions.json").read_text())
    measurements = {}
    for name, labels in LABELS.items():
        folder = args.frames / name
        if name == "stomach":
            views = json.loads((folder / "receipt.json").read_text())["views"]
            files = {v["file"]: v for v in views}
            frames = {side: [files[f"{prefix}-{stem}.png"] for stem in STOMACH]
                      for side, prefix in (("original", "control"), ("updated", "candidate"))}
        else:
            frames = json.loads((folder / "frames.json").read_text())["frames"]
        images = {side: [bound_image(folder, item) for item in bindings] for side, bindings in frames.items()}
        differences = []
        for i, (left, right) in enumerate(zip(images["original"], images["updated"], strict=True)):
            alpha = left.getchannel("A")
            mask = alpha.point(lambda v: 255 if v > 0 else 0)
            rgb_diff = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
            pixels = ImageStat.Stat(rgb_diff, mask)
            differences.append({
                "view": labels[i], "originalRawPngSha256": frames["original"][i]["sha256"],
                "updatedRawPngSha256": frames["updated"][i]["sha256"],
                "alphaSamplesChanged": sum(ImageChops.difference(alpha, right.getchannel("A")).histogram()[1:]),
                "foregroundMeanAbsoluteRgb8": round(sum(pixels.mean) / 3, 5),
                "foregroundMaxAbsoluteChannel8": max(high for _, high in pixels.extrema),
            })
        for side, group in images.items():
            write_plate(args.destination / f"{name}-{side}.webp", group, labels,
                        f"{side.capitalize()}  /  {settings[name]['family']}")
        measurements[name] = differences
    (args.destination / "pixels.json").write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
