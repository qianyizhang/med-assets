"""Compose a regional lower-limb to left venous-angle teaching route."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import (
    colorize,
    ellipsoid,
    export,
    load_meshes,
    material,
    place,
    tube,
)


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    inputs = json.loads((HERE / "inputs.json").read_text())
    green = material("Collecting lymphatic", (0.30, 0.49, 0.30))
    gold = material("Nodal lymph passage", (0.69, 0.51, 0.23))
    capsule = material("Nodal capsule", (0.43, 0.61, 0.47))
    vein = material("Venous return", (0.22, 0.36, 0.53))
    flesh = material("Tissue", (0.66, 0.41, 0.28))
    low, high = (0, 0.04, -0.20), (0.045, 0.005, 0.21)
    (duct,) = load_meshes(
        **inputs["duct"], select=lambda n: n.startswith("Thoracic duct")
    )
    duct.name = "Thoracic duct - source scaffold"
    colorize(duct, green)
    node = load_meshes(
        **inputs["node"],
        select=lambda n: any(word in n for word in ("capsule", "afferent", "efferent")),
    )
    offsets = {"node": place(node, (0.047, 0.003, -0.278), 2.4)}
    aff = next(o for o in node if "afferent" in o.name)
    eff = next(o for o in node if "efferent" in o.name)
    for obj in node:
        colorize(obj, capsule if "capsule" in obj.name else gold)

    def pole(obj, top):
        coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
        return tuple((max if top else min)(coords, key=lambda p: p.z))

    entry = pole(aff, False)
    exit_node = pole(eff, True)
    seed = (0.071, -0.004, -0.348)
    ellipsoid("Distal tissue drainage bed", seed, (0.019, 0.010, 0.008), flesh)
    stem = (0.067, -0.010, -0.333)
    for i, dx in enumerate([-0.012, 0, 0.012]):
        start = (seed[0] + dx, -0.009, seed[2] + 0.001)
        tube(
            f"Blind initial capillary {i + 1}",
            [start, (start[0], -0.012, -0.340), stem],
            0.0012,
            green,
        )
    tube(
        "Afferent collector from tissue",
        [stem, (0.061, -0.009, -0.319), entry],
        0.0025,
        green,
    )
    tube(
        "Schematic intranodal passage",
        [entry, (0.045, -0.006, -0.279), exit_node],
        0.0019,
        gold,
    )
    cisterna = (0.004, 0.038, -0.206)
    tube(
        "Efferent collecting trunk",
        [exit_node, (0.034, 0.010, -0.242), (0.018, 0.031, -0.219), cisterna],
        0.0028,
        green,
    )
    ellipsoid("Cisterna chyli - schematic", cisterna, (0.0065, 0.0065, 0.012), green)
    angle = (0.061, -0.009, 0.202)
    tube(
        "Terminal duct bridge",
        [high, (0.051, 0.001, 0.212), (0.058, -0.004, 0.209), angle],
        0.0026,
        green,
    )
    tube(
        "Left internal jugular vein",
        [(0.058, -0.011, 0.254), (0.059, -0.009, 0.228), angle],
        0.007,
        vein,
    )
    tube(
        "Left subclavian vein",
        [(0.128, -0.010, 0.206), (0.095, -0.012, 0.203), angle],
        0.008,
        vein,
    )
    tube(
        "Left brachiocephalic vein",
        [angle, (0.042, -0.013, 0.193), (0.006, -0.012, 0.175)],
        0.0084,
        vein,
    )
    for key, target, mat in [
        ("spleen", (0.116, 0.021, -0.115), material("Spleen", (0.55, 0.23, 0.18))),
        ("thymus", (0, -0.035, 0.105), material("Thymus", (0.65, 0.42, 0.21))),
    ]:
        organs = load_meshes(**inputs[key])
        offsets[key] = place(organs, target)
        for obj in organs:
            obj.name = key.capitalize() + " locator - " + obj.name
            colorize(obj, mat)
    marks = [
        [stem, ["Blind initial capillary 2", "Afferent collector from tissue"]],
        [
            entry,
            [
                aff.name,
                "Afferent collector from tissue",
                "Schematic intranodal passage",
            ],
        ],
        [
            exit_node,
            [eff.name, "Schematic intranodal passage", "Efferent collecting trunk"],
        ],
        [cisterna, ["Efferent collecting trunk"]],
        [low, [duct.name]],
        [high, [duct.name, "Terminal duct bridge"]],
        [
            angle,
            [
                "Terminal duct bridge",
                "Left internal jugular vein",
                "Left subclavian vein",
                "Left brachiocephalic vein",
            ],
        ],
    ]
    export(out, "lymphatic-return")
    (out / "placement.json").write_text(
        json.dumps(dict(translations=offsets, junctions=marks), indent=2) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args(sys.argv[sys.argv.index("--") + 1 :]).output)
