#!/usr/bin/env python3
"""Replace only r01's transport summary; retain the outlined anatomical drawing.

Requires Inkscape 1.4 and Noto Sans CJK SC / Noto Sans for the new labels.
Writes editable and portable SVGs to a new directory; never overwrites r01.
"""

import argparse
import copy
import hashlib
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
SVG = "{" + NS + "}"
HASHES = {
    "en": (
        "d2e0d0a576ff8230ffe1fca7f9a261e53816e3b4b2076bfc445d208352bbf4bc",
        "d00f45b3e6f1d4866cd426e4bd7d22e31df5dcaeb40c62eca82aba00eb8f26f6",
    ),
    "zh": (
        "502635908a84a638fb7052dacc357291c78fc09c9c7e29f8ce98b7c832b776e0",
        "6c97095658b4b402ac03e2183fb3ed5f19d5b085bdb0424baa7b7dd0d3edb322",
    ),
}
COPY = {
    "en": [
        ("Seminiferous", "tubules"),
        ("Straight tubules", "↓ Rete testis"),
        ("Efferent", "ductules"),
        ("Epididymis", "Head → body → tail"),
        ("Ductus", "deferens"),
    ],
    "zh": [
        ("生精小管", ""),
        ("生精直小管", "↓ 睾丸网"),
        ("睾丸输出小管", ""),
        ("附睾", "头 → 体 → 尾"),
        ("输精管", ""),
    ],
}


def element(tag, attributes, text=None):
    node = ET.Element(SVG + tag, {k: str(v) for k, v in attributes.items()})
    node.text = text
    return node


def label(x, y, text, size=24, color="#e9edf1"):
    return element("text", {
        "x": x, "y": y,
        "style": "font-family:'Noto Sans CJK SC','Noto Sans',sans-serif;"
                 f"font-size:{size}px;fill:{color}",
    }, text)


def summary(language):
    title = "TRANSPORT PATH" if language == "en" else "输送路径"
    group = element("g", {
        "id": "transport-path-summary", "role": "group",
        "aria-label": "Transport path" if language == "en" else title,
    })
    group.append(element("rect", {
        "x": 70, "y": 863, "width": 1260, "height": 100, "rx": 10,
        "fill": "#1c232b", "stroke": "#323b46",
    }))
    group.append(label(88, 886, title, 16, "#a7b0bb"))
    for i, (line1, line2) in enumerate(COPY[language]):
        x = 88 + i * 248
        step = element("g", {
            "id": f"transport-step-{i + 1}", "role": "group",
            "aria-label": f"{line1} {line2}".strip(),
        })
        step.append(element("rect", {
            "x": x, "y": 897, "width": 220, "height": 59, "rx": 5,
            "fill": "#202a33", "stroke": "#425262",
        }))
        step.append(label(x + 12, 921 if line2 else 937, line1))
        if line2:
            step.append(label(x + 12, 948, line2, 20 if i == 3 else 24))
        group.append(step)
        if i < 4:
            group.append(element("path", {
                "d": f"M{x + 226} 929h16m-5 -5l5 5 -5 5",
                "fill": "none", "stroke": "#76b9f4", "stroke-width": 2,
                "stroke-linecap": "round", "stroke-linejoin": "round",
            }))
    return group


def replace_summary(root, replacement):
    children = list(root)
    strip = [i for i, node in enumerate(children)
             if node.tag == SVG + "rect"
             and node.get("x") == "70" and node.get("y") == "863"]
    if strip != [64] or len(children) != 77:
        raise ValueError("Unexpected frozen r01 layout")
    for node in children[64:75]:
        root.remove(node)
    root.insert(64, replacement)


def write_svg(root, destination):
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New, nonexistent output directory")
    parser.add_argument("--inkscape", default="inkscape")
    args = parser.parse_args()

    inputs = {}
    for language in COPY:
        editable = ROOT / "sources/authored/testis_pathway/r01" / (
            f"testis-pathway-{language}-editable.svg")
        display = ROOT / "diagrams/testis_pathway/exports/r01" / (
            f"testis-pathway-{language}.svg")
        hashes = tuple(hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (editable, display))
        if hashes != HASHES[language]:
            raise ValueError(f"Frozen {language} source identity mismatch")
        inputs[language] = editable, display
    args.output.mkdir(parents=True, exist_ok=False)

    for language, (editable, display) in inputs.items():
        group = summary(language)
        fragment = element("svg", {
            "width": 1400, "height": 1060, "viewBox": "0 0 1400 1060",
        })
        fragment.append(copy.deepcopy(group))
        fragment_file = args.output / f"summary-{language}.svg"
        fragment_out = args.output / f"summary-{language}-outlined.svg"
        write_svg(fragment, fragment_file)
        subprocess.run([
            args.inkscape, str(fragment_file), "--export-text-to-path",
            "--export-plain-svg", f"--export-filename={fragment_out}",
        ], check=True)
        outlined = ET.parse(fragment_out).getroot().find(
            './/*[@id="transport-path-summary"]')
        if outlined is None or any(n.tag == SVG + "text" for n in outlined.iter()):
            raise ValueError("Summary text did not outline")
        # The fragment uses only paths/rectangles/groups: no reference rewriting.
        for node in outlined.iter():
            if node.tag not in {SVG + tag for tag in ("g", "rect", "path")}:
                raise ValueError("Unexpected outlined summary element")
            if any("url(" in v or k.endswith("href") for k, v in node.attrib.items()):
                raise ValueError("Unexpected outlined summary reference")
            if node.get("id") and not node.get("id").startswith("transport-"):
                node.set("id", "transport-" + node.get("id"))

        for source, replacement, suffix in (
            (editable, group, "-editable"), (display, outlined, ""),
        ):
            root = ET.parse(source).getroot()
            replace_summary(root, replacement)
            write_svg(root, args.output / f"testis-pathway-{language}{suffix}.svg")
        print(f"{language}: editable and outlined r02 SVGs written")


if __name__ == "__main__":
    main()
