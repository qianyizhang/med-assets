#!/usr/bin/env python3
"""Export actual teaching SVGs and check source pixels, localized changes and replay."""
import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw

from build import BADGES, build, verify_inputs
from source import require, sha

NS = {"s": "http://www.w3.org/2000/svg"}
HREF = "{http://www.w3.org/1999/xlink}href"


def export(svg, png):
    result = subprocess.run(["inkscape", str(svg), "--export-type=png", "--export-filename=" + str(png)],
                            text=True, capture_output=True)
    require(result.returncode == 0 and png.is_file(), "Inkscape export failed: " + result.stderr)


def check(source, renders, plates, output):
    record, _ = verify_inputs(source, renders)
    output.mkdir(parents=True, exist_ok=False)
    require(shutil.which("inkscape"), "Inkscape is required")
    rows = []
    svg_files = ["arch-locators.svg", "overview-comparison.svg", "junction-comparison.svg"]
    for name in svg_files:
        root = ET.fromstring((plates / name).read_bytes())
        for im in root.findall(".//s:image", NS):
            view = next(v for v in record["views"] if im.attrib["id"] == "image-" + v["view"])
            embedded = base64.b64decode(im.attrib[HREF].removeprefix("data:image/png;base64,"), validate=True)
            require(sha(embedded) == view["sha256"], "Embedded raster differs from exact render")
        png = output / name.replace(".svg", ".png")
        export(plates / name, png)
        require(Image.open(png).size == (1920, 1440), "Unexpected exported size")
        rows.append({"file": png.name, "sha256": sha(png.read_bytes()), "bytes": png.stat().st_size})
    comparisons = []
    for view in record["views"]:
        im = Image.open(output / (view["view"] + "-comparison.png")).convert("RGB")
        original = im.crop((40, 160, 940, 1060))
        updated = im.crop((980, 160, 1880, 1060))
        source_pixels = Image.open(renders / view["file"]).convert("RGB")
        require(ImageChops.difference(original, source_pixels).getbbox() is None,
                "Original panel resampled or changed the retained raster")
        difference = ImageChops.difference(original, updated)
        mask = Image.new("L", (900, 900), 0)
        draw = ImageDraw.Draw(mask)
        changes_by_number = []
        for anchor in view["anchors"]:
            px, py = anchor["pixel"]
            bx, by = BADGES[view["view"]][anchor["number"]]
            draw.line([(bx, by), (px, py)], fill=255, width=11)
            draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=255)
            draw.ellipse((bx - 25, by - 25, bx + 25, by + 25), fill=255)
            changed = difference.crop((bx - 24, by - 24, bx + 24, by + 24)).getbbox()
            require(changed is not None, "Missing rendered numeric badge")
            changes_by_number.append(anchor["number"])
        outside = ImageChops.multiply(difference, ImageChops.invert(mask).convert("RGB"))
        require(outside.getbbox() is None, "Changes outside the editorial locator mask")
        require(difference.getbbox() is not None, "Updated panel has no locators")
        comparisons.append({"view": view["view"], "originalPixelsEqualRender": True,
                            "changesConfinedToEditorialMask": True, "visibleNumericBadges": changes_by_number,
                            "changedPixelCount": sum(p != (0, 0, 0) for p in difference.getdata())})
    teaching = Image.open(output / "arch-locators.png")
    teaching.convert("L").save(output / "arch-locators-grayscale.png")
    gray = output / "arch-locators-grayscale.png"
    rows.append({"file": gray.name, "sha256": sha(gray.read_bytes()), "bytes": gray.stat().st_size})
    replay = output / "composition-replay"
    build(source, renders, replay)
    replay_files = svg_files + ["build.json"]
    require(all((plates / f).read_bytes() == (replay / f).read_bytes() for f in replay_files),
            "Composition replay changed bytes")
    result = {"sourceSha256": record["sha256"], "sourceRenderReceiptSha256": sha((renders / "render.json").read_bytes()),
              "nativeRenderer": subprocess.check_output(["inkscape", "--version"], text=True).strip(),
              "comparisons": comparisons, "compositionReplayByteIdentical": replay_files,
              "outputs": rows, "scope": "Actual native SVG exports and static binding. Grayscale exported for visual inspection; no browser or clinical approval."}
    (output / "visual-binding.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "renders", "plates", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(check(a.source, a.renders, a.plates, a.output), indent=2))
