#!/usr/bin/env python3
"""Bind actual SVG exports and verify matched pixels outside the editorial cue.

Requires Pillow and Inkscape. Outputs are local evidence, never uploaded here.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageOps

from build import ROOT, SPEC, build, sha, verify_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_inputs(ROOT)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"sourceModel": SPEC["model"], "sourceImage": SPEC["image"], "files": [], "pairs": [],
        "scope": "Native SVG export/reload and pixel binding only; no browser/WebGL or clinical approval"}
    receipt["inkscape"] = subprocess.check_output(["inkscape", "--version"], text=True).strip()
    # Portable copies embed the same exact PNG once; linked copies are the
    # committed teaching artifact. Export both independently and compare pixels.
    build(ROOT, out / "portable", embed=True)
    with tempfile.TemporaryDirectory(prefix="brain-cut-replay-") as temp:
        replay = Path(temp) / "portable"
        build(ROOT, replay, embed=True)
        for p in (out / "portable").iterdir():
            if p.read_bytes() != (replay / p.name).read_bytes():
                raise ValueError("Non-deterministic portable replay")
    receipt["byteIdenticalReplay"] = True
    for view in SPEC["views"]:
        for mode in ("teaching", "comparison"):
            name = f"{view}-{mode}"
            portable = out / "portable" / (name + ".svg")
            linked = ROOT / "lessons/brain-source-cut/sheets" / (name + ".svg")
            for variant, svg in [("portable", portable), ("linked", linked)]:
                png = out / f"{name}-{variant}.png"
                proc = subprocess.run(["inkscape", str(svg), "--export-filename=" + str(png)],
                                      check=True, capture_output=True, text=True)
                (out / f"{name}-{variant}.log").write_text(proc.stderr)
                receipt["files"].append({"file": png.name, "sha256": sha(png.read_bytes()),
                    "svgSha256": sha(svg.read_bytes()), "bytes": png.stat().st_size,
                    "dimensions": list(Image.open(png).size)})
            a = Image.open(out / f"{name}-portable.png").convert("RGB")
            b = Image.open(out / f"{name}-linked.png").convert("RGB")
            if ImageChops.difference(a, b).getbbox() is not None:
                raise ValueError("Linked and portable SVG pixels differ")
            if mode == "comparison":
                for kind, y, h in [("overview", 162, 672), ("detail", 909, 571)]:
                    left = a.crop((24, y, 696, y + h))
                    right = a.crop((744, y, 1416, y + h))
                    diff = ImageChops.difference(left, right)
                    bounds = diff.getbbox()
                    crop = SPEC["views"][view][kind]
                    scale = 672 / crop[2]
                    points = SPEC["views"][view]["bracket"] + [SPEC["views"][view]["badge"]]
                    xs = [(p[0] - crop[0]) * scale for p in points]
                    ys = [(p[1] - crop[1]) * scale for p in points]
                    allowed = [min(xs) - 17, min(ys) - 17, max(xs) + 17, max(ys) + 17]
                    if not bounds or not (allowed[0] <= bounds[0] <= bounds[2] <= allowed[2] and
                                          allowed[1] <= bounds[1] <= bounds[3] <= allowed[3]):
                        raise ValueError(f"Unexpected pixel changes in {view}/{kind}: {bounds}")
                    receipt["pairs"].append({"view": view, "crop": kind, "differenceBounds": bounds,
                        "onlyLocalizedCueChanged": True, "pairScale": scale})
                ImageOps.grayscale(a).save(out / f"{name}-grayscale.png")
            else:
                pdf = out / f"{name}.pdf"
                subprocess.run(["inkscape", str(portable), "--export-text-to-path",
                                "--export-filename=" + str(pdf)], check=True, capture_output=True)
                receipt["files"].append({"file": pdf.name, "sha256": sha(pdf.read_bytes()),
                    "bytes": pdf.stat().st_size, "svgSha256": sha(portable.read_bytes())})
    receipt["linkedPortablePixelsIdentical"] = True
    receipt["modelBytesUnchangedAfterExport"] = sha((ROOT / SPEC["model"]["file"]).read_bytes()) == SPEC["model"]["sha256"]
    (out / "visual-binding.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
