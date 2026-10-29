#!/usr/bin/env python3
"""Build bilingual source-cut teaching SVGs from the retained, hash-pinned pixels.

No renderer, downloads, mesh edits, or model export. Published SVGs reference the
existing contact; --embed writes portable local copies for review/printing.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import struct
from xml.sax.saxutils import escape, quoteattr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = json.loads((HERE / "presentation.json").read_text())
INK, MUTED, GOLD = "#f1f3f5", "#b9c4d0", "#ffe09a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_inputs(root):
    result = {}
    for key in ("model", "image"):
        row = SPEC[key]
        data = (root / row["file"]).read_bytes()
        if len(data) != row["bytes"] or sha(data) != row["sha256"]:
            raise ValueError(f"{key} identity mismatch; hydrate the exact retained file")
        result[key] = data
    data = result["model"]
    magic, version, size, length, kind = struct.unpack_from("<4sIIII", data)
    if (magic, version, size, kind) != (b"glTF", 2, len(data), 0x4E4F534A):
        raise ValueError("Invalid retained GLB container")
    doc = json.loads(data[20:20 + length])
    if len(doc["meshes"]) != SPEC["model"]["meshes"]:
        raise ValueError("Expected all 49 retained meshes")
    medulla = [n["name"] for n in doc["nodes"] if n.get("name", "").startswith("medulla oblongata |")]
    if set(medulla) != {"medulla oblongata | FJ1769", "medulla oblongata | FJ1831"}:
        raise ValueError("Expected both retained medulla nodes")
    png = result["image"]
    if png[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack_from(">II", png, 16) != (2100, 1586):
        raise ValueError("Unexpected source image dimensions")
    return result


def text(x, y, value, size=22, color=INK, weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(value)}</text>'


def frame(width, height, title, description, content, href):
    metadata = escape(json.dumps({"sourceModel": SPEC["model"], "sourceImage": SPEC["image"],
        "kind": "static editorial teaching presentation", "geometryEdited": False,
        "runtime": "unverified", "clinicalApproval": "not claimed"}, separators=(",", ":")))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<metadata>{metadata}</metadata>
<defs><image id="source" x="0" y="0" width="2100" height="1586" xlink:href={quoteattr(href)}/></defs>
<rect width="100%" height="100%" fill="#101820"/>
<g font-family="DejaVu Sans, Noto Sans CJK SC, sans-serif">{content}</g>
</svg>\n'''


def cue(view, crop, width):
    # Source-image coordinates: bracket spans the visible terminal edge, not a
    # neighboring midline gap. All marks remain a separate unfilled SVG layer.
    row = SPEC["views"][view]
    scale = width / crop[2]
    points = " ".join(f"{x},{y}" for x, y in row["bracket"])
    ax, ay = row["anchor"]
    bx, by = row["badge"]
    r = 13 / scale
    return f'''<g data-editorial="source-cut" fill="none" stroke-linejoin="round">
<polyline points="{points}" stroke="#101820" stroke-width="{6 / scale}"/>
<polyline points="{points}" stroke="{GOLD}" stroke-width="{2.5 / scale}" stroke-dasharray="{5 / scale} {3 / scale}"/>
<path d="M {ax},{ay} L {bx-r},{by}" stroke="{GOLD}" stroke-width="{1.5 / scale}"/>
<circle cx="{bx}" cy="{by}" r="{r}" fill="#101820" stroke="{GOLD}" stroke-width="{1.5 / scale}"/>
<text x="{bx}" y="{by + 4 / scale}" text-anchor="middle" stroke="none" fill="{GOLD}" font-size="{12 / scale}" font-weight="700">1</text>
</g>'''


def panel(view, kind, x, y, width, updated):
    crop = SPEC["views"][view][kind]
    height = width * crop[3] / crop[2]
    overlay = cue(view, crop, width) if updated else ""
    identity = f"{view}-{kind}-{'updated' if updated else 'original'}"
    scale = width / crop[2]
    # Explicit outer-coordinate clipping is portable across SVG viewers and
    # Inkscape; nested SVG overflow alone was not honored in the v1 export.
    return f'''<defs><clipPath id="clip-{identity}"><rect x="{x}" y="{y}" width="{width}" height="{height}"/></clipPath></defs>
<g clip-path="url(#clip-{identity})" data-view="{view}" data-crop="{kind}" data-variant="{'updated' if updated else 'original'}">
<g transform="translate({x} {y}) scale({scale}) translate({-crop[0]} {-crop[1]})">
<use xlink:href="#source"/>{overlay}</g></g>'''


def label(x, y, title, subtitle):
    return text(x, y, title, 23, GOLD, 700) + text(x, y + 34, subtitle, 19, MUTED)


def teaching(href, view):
    row = SPEC["views"][view]
    c = text(32, 38, "BODYPARTS3D 4.0   /   TEACHING VIEW · 教学视图", 17, MUTED)
    c += text(32, 98, "Where the source model ends · 源模型到此截断", 38, INK, 700)
    c += text(32, 140, "The flat edge is a source cut. The continuation into the spinal cord is not represented.", 23)
    c += text(32, 176, "平坦下缘是源模型截断处；与脊髓相续的部分未在本模型中呈现。", 23)
    c += text(32, 227, f"OVERVIEW / 全貌    {row['en']} · {row['zh']}", 19, MUTED, 700)
    c += text(792, 227, "DETAIL / 局部    Same image, enlarged · 同图放大", 19, MUTED, 700)
    c += panel(view, "overview", 24, 252, 700, True)
    c += panel(view, "detail", 780, 252, 636, True)
    c += label(792, 843, "1   Source cut / 源模型截断", "Editorial bracket, not tissue / 编辑括号，非组织")
    c += text(792, 919, "The source surface remains visible.", 21)
    c += text(792, 951, "保留原有表面，不补画缺失的解剖结构。", 21)
    c += label(32, 1000, "1   Source cut / 源模型截断", "Editorial bracket, not tissue / 编辑括号，非组织")
    c += text(32, 1104, "49 retained atlas parts · Unchanged source pixels · Display material · No clinical approval", 19, MUTED)
    c += text(32, 1136, "保留图谱 49 个部件 · 原图像素未改 · 展示用材质 · 不代表临床认可", 19, MUTED)
    c += text(32, 1188, "BodyParts3D / Anatomography, © DBCLS · CC BY 4.0 · Editorial presentation added 2026-10-29", 17, MUTED)
    return frame(1440, 1224, f"Source cut teaching view — {view} / 源模型截断教学图",
        "Matched overview and enlarged crop of the retained brain render. Dashed brackets mark the source truncation. No anatomy was added.", c, href)


def comparison(href, view):
    c = text(32, 39, "SOURCE CUT / 源模型截断    ·    MATCHED COMPARISON / 匹配对照", 20, MUTED, 700)
    c += text(32, 91, "Original / 原图", 32, INK, 700) + text(752, 91, "Updated / 添加标记", 32, INK, 700)
    c += text(32, 130, "Same exact source pixels, crop and display scale in each pair / 每对使用同一原图、裁剪与显示比例", 21, MUTED)
    for updated, x in [(False, 24), (True, 744)]:
        c += panel(view, "overview", x, 162, 672, updated)
        c += text(x + 8, 870, "Overview / 全貌", 22, MUTED, 700)
        c += panel(view, "detail", x, 909, 672, updated)
        c += text(x + 8, 1520, "Detail / 局部 · enlarged retained pixels / 原图放大", 21, MUTED)
    c += label(752, 1574, "1   Source cut / 源模型截断", "Editorial bracket, not tissue / 编辑括号，非组织")
    c += text(32, 1668, "The spinal continuation is omitted. No geometry is added or changed. / 未呈现脊髓相续部分；未增改几何。", 21)
    c += text(32, 1710, "BodyParts3D / Anatomography, © DBCLS · CC BY 4.0 · Static editorial presentation · No clinical approval", 17, MUTED)
    return frame(1440, 1748, f"Original and updated brain source-cut presentation — {view}",
        "Two matched pairs: whole brain and detail. Only the right column adds editorial brackets. Both use the identical retained source image.", c, href)


def build(root, output, embed=False):
    inputs = verify_inputs(root)
    output.mkdir(parents=True, exist_ok=False)
    href = ("data:image/png;base64," + base64.b64encode(inputs["image"]).decode()) if embed else os.path.relpath(
        root / SPEC["image"]["file"], output)
    rows = []
    for view in SPEC["views"]:
        for mode, render in [("teaching", teaching), ("comparison", comparison)]:
            name = f"{view}-{mode}.svg"
            payload = render(href, view).encode()
            (output / name).write_bytes(payload)
            rows.append({"file": name, "sha256": sha(payload), "bytes": len(payload)})
    receipt = {"model": SPEC["model"], "image": SPEC["image"], "views": SPEC["views"],
        "embeddedImage": embed, "outputs": rows, "renderer": "SVG composition; no 3-D rerender",
        "modelBytesUnchanged": sha((root / SPEC["model"]["file"]).read_bytes()) == SPEC["model"]["sha256"]}
    (output / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True, help="New output directory")
    p.add_argument("--embed", action="store_true", help="Portable local SVGs; do not publish without authority")
    args = p.parse_args()
    receipt = build(args.root.resolve(), args.output.resolve(), args.embed)
    print(json.dumps({"outputs": receipt["outputs"], "modelBytesUnchanged": receipt["modelBytesUnchanged"]}, indent=2))


if __name__ == "__main__":
    main()
