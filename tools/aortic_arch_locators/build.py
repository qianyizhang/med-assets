#!/usr/bin/env python3
"""Compose private arch locator SVGs; source pixels and geometry stay unchanged."""
import argparse
import base64
import json
import math
from pathlib import Path
import struct
from xml.sax.saxutils import escape, quoteattr

if __package__:
    from .source import GROUPS, inventory, require, sha
else:
    from source import GROUPS, inventory, require, sha

INK, MUTED, CUE, BG = "#f4f2eb", "#bac5ca", "#ffe2a3", "#101b22"
BADGES = {
    "overview": {1: (318, 240), 2: (585, 85), 3: (635, 205), 4: (278, 96)},
    "junction": {1: (200, 475), 2: (690, 150), 3: (780, 465), 4: (105, 235)},
}


def validate_mapping(record, source_record):
    """Fail closed on a stale camera, swapped label or unbound projection receipt."""
    for key in ("sha256", "bytes", "binaryChunkSha256", "nodes", "groups", "laterality"):
        require(record[key] == source_record[key], f"Render source inventory mismatch: {key}")
    require(record["sourceBytesAndImportedGeometryUnchanged"] is True, "Unchanged geometry not recorded")
    require([v["view"] for v in record["views"]] == ["overview", "junction"], "Unexpected views")
    for view in record["views"]:
        require(view["resolution"] == [900, 900], "Unexpected image dimensions")
        require(view["file"] == view["view"] + ".png", "Unexpected image filename")
        scale = view["orthoScaleM"]
        cam = view["cameraBlenderM"]
        matrix = view["cameraWorldMatrix"]
        require(len(view["anchors"]) == 4, "Expected four source group anchors")
        # This recipe's camera looks along Blender +Y, with +X on screen right.
        expected = ((1, 0, 0), (0, 0, -1), (0, 1, 0))
        require(all(abs(matrix[r][c] - expected[r][c]) < 1e-5 for r in range(3) for c in range(3)),
                "Unreviewed camera orientation")
        require(all(abs(matrix[r][3] - cam[r]) < 1e-7 for r in range(3)), "Camera matrix/position differs")
        require(scale > 0 and math.isfinite(scale), "Invalid orthographic scale")
        for group, anchor in zip(GROUPS, view["anchors"]):
            require(anchor["number"] == group["number"] and anchor["sourceNode"] == group["node"]
                    and anchor["sourceNames"] == group["sourceNames"], "Swapped source-to-callout mapping")
            require(anchor["rayHitExactSourceNode"] is True, "Anchor lacks exact node ray hit")
            p = anchor["pixel"]
            require(len(p) == 2 and all(math.isfinite(a) and 0 <= a < 900 for a in p), "Anchor outside image")
            require(all(abs(a - b) < .01 for a, b in zip(p, anchor["projectedHitPixel"])), "Projection mismatch")
            x, y, _ = anchor["hitSourceM"]
            computed = (450 + (x - cam[0]) * 900 / scale, 450 - (y - cam[2]) * 900 / scale)
            require(all(abs(a - b) < .01 for a, b in zip(p, computed)), "Source/camera projection mismatch")
            node = next(n for n in record["nodes"] if n["nodeName"] == anchor["sourceNode"])
            require(0 <= anchor["rayHitPolygon"] < node["triangles"], "Ray hit polygon outside source mesh")
        require(view["anchors"][2]["pixel"][0] > view["anchors"][3]["pixel"][0], "Left/right swapped on screen")


def verify_inputs(source, renders):
    source_record = inventory(source.read_bytes())
    record = json.loads((renders / "render.json").read_text())
    validate_mapping(record, source_record)
    images = {}
    for view in record["views"]:
        raw = (renders / view["file"]).read_bytes()
        require(len(raw) == view["bytes"] and sha(raw) == view["sha256"], "Render image identity mismatch")
        require(raw[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack_from(">II", raw, 16) == (900, 900),
                "Unexpected source PNG dimensions")
        images[view["view"]] = "data:image/png;base64," + base64.b64encode(raw).decode()
    return record, images


def text(x, y, value, size=23, color=INK, weight=400, **attrs):
    extra = " ".join(f"{k.replace('_', '-')}={quoteattr(str(v))}" for k, v in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>{escape(value)}</text>'


def overlay(view):
    c = '<g data-editorial="numbered-source-locators" fill="none">'
    for anchor in view["anchors"]:
        n = anchor["number"]
        px, py = anchor["pixel"]
        bx, by = BADGES[view["view"]][n]
        c += f'<g data-number="{n}" data-source-node={quoteattr(anchor["sourceNode"])}>'
        # A small open ring retains the surface at the verified endpoint. All
        # identifiers and lines are plainly graphic, never a vessel substitute.
        c += f'<path d="M {bx},{by} L {px},{py}" stroke="{BG}" stroke-width="5"/>'
        c += f'<path d="M {bx},{by} L {px},{py}" stroke="{CUE}" stroke-width="2"/>'
        c += f'<circle cx="{px}" cy="{py}" r="5" stroke="{BG}" stroke-width="4"/>'
        c += f'<circle cx="{px}" cy="{py}" r="5" stroke="{CUE}" stroke-width="1.5"/>'
        c += f'<circle cx="{bx}" cy="{by}" r="20" fill="{BG}" stroke="{CUE}" stroke-width="2"/>'
        c += text(bx, by + 8, str(n), 24, CUE, 700, text_anchor="middle") + '</g>'
    return c + '</g>'


def panel(view, x, y, updated):
    variant = "updated" if updated else "original"
    return (f'<g transform="translate({x} {y})" data-view="{view["view"]}" data-variant="{variant}">'
            f'<use xlink:href="#image-{view["view"]}"/>' + (overlay(view) if updated else "") + '</g>')


def legend():
    c = ""
    for group, (x, y) in zip(GROUPS, [(66, 1134), (1020, 1134), (1020, 1230), (66, 1230)]):
        c += f'<circle cx="{x}" cy="{y - 8}" r="20" fill="{BG}" stroke="{CUE}" stroke-width="2"/>'
        c += text(x, y, str(group["number"]), 24, CUE, 700, text_anchor="middle")
        c += text(x + 36, y - 9, group["en"], 25, INK, 700)
        c += text(x + 36, y + 25, group["zh"], 25, INK)
        if group["number"] == 1:
            c += text(x + 36, y + 53, "One joined source group / 源文件中的一个合并组", 18, MUTED)
    return c


def footer():
    c = text(40, 1313, "Numbered leaders are editorial. Open intersections and cropped ends remain unchanged.", 21, MUTED)
    c += text(40, 1345, "编号引线为编辑标记；保留源模型未融合的交接与截断端。", 21, MUTED)
    c += text(40, 1387, "Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0 · New renders and labels, 2026-10-29", 18, MUTED)
    c += text(40, 1415, "BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan (historical credit)", 18, MUTED)
    return c


def frame(title, description, content, images, record):
    defs = "".join(f'<image id="image-{name}" width="900" height="900" xlink:href={quoteattr(href)}/>'
                   for name, href in images.items())
    meta = {"sourceSha256": record["sha256"], "kind": "editorial teaching presentation", "geometryEdited": False,
            "license": "CC BY-SA 4.0", "cameraProvenance": record["cameraProvenance"],
            "views": [{k: v[k] for k in ("view", "sha256", "resolution", "anchors")} for v in record["views"]]}
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="1440" viewBox="0 0 1920 1440" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<metadata>{escape(json.dumps(meta, ensure_ascii=False, separators=(",", ":")))}</metadata>
<defs>{defs}</defs><rect width="1920" height="1440" fill="{BG}"/>
<g font-family="DejaVu Sans, Noto Sans CJK SC, sans-serif">{content}</g></svg>\n'''


def teaching(images, record):
    c = text(40, 38, "Z-ANATOMY · SOURCE-NAMED LOCATORS / 源模型命名定位", 18, MUTED, 700)
    c += text(40, 91, "Arch branches: follow the same numbers · 主动脉弓分支：循编号对照", 38, INK, 700)
    for view, x, name in zip(record["views"], (40, 980), ("Overview / 全貌", "Junction detail / 分支交接局部")):
        c += text(x, 137, name, 24, INK, 700)
        c += panel(view, x, 160, True)
        c += text(x + 18, 195, "R / 右", 20, MUTED, 700)
        c += text(x + 882, 195, "L / 左", 20, MUTED, 700, text_anchor="end")
    c += legend() + footer()
    return frame("Aortic arch branch locators / 主动脉弓分支定位", "Two source-native views. Numbers 1–4 identify the same source groups in overview and junction detail; source left is screen right. No geometry is added or fused.", c, images, record)


def comparison(images, record, view):
    name = "Overview / 全貌" if view["view"] == "overview" else "Junction detail / 分支交接局部"
    c = text(40, 38, "MATCHED COMPARISON / 匹配对照 · " + name, 21, MUTED, 700)
    c += text(40, 90, "Original / 原图", 36, INK, 700)
    c += text(980, 90, "Updated / 添加定位标记", 36, INK, 700)
    c += text(40, 132, "Same new source render, crop and scale in each pair / 每对使用同一张新渲染图、裁剪与比例", 23, MUTED)
    c += panel(view, 40, 160, False) + panel(view, 980, 160, True)
    c += legend() + footer()
    return frame("Original / Updated — " + name, "Both panels use identical exact-source raster bytes. Only Updated adds numbered editorial locators. These are new recorded-camera captures, not historical pixel replay.", c, {view["view"]: images[view["view"]]}, record)


def build(source, renders, output):
    record, images = verify_inputs(source, renders)
    payloads = {"arch-locators.svg": teaching(images, record)}
    for view in record["views"]:
        payloads[view["view"] + "-comparison.svg"] = comparison(images, record, view)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, content in payloads.items():
        raw = content.encode()
        (output / name).write_bytes(raw)
        rows.append({"file": name, "sha256": sha(raw), "bytes": len(raw)})
    receipt = {"sourceSha256": record["sha256"], "renderReceiptSha256": sha((renders / "render.json").read_bytes()),
               "outputs": rows, "badges": BADGES, "sameRasterUsedForEachPair": True,
               "portableEmbeddedImages": True, "license": "CC BY-SA 4.0"}
    (output / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New private directory; no publication")
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.renders, args.output), indent=2))
