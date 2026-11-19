"""Gross endocrine locator with separate islet and thyroid-axis teaching overlays."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import colorize, ellipsoid, export, load_meshes, material, place, tube


def arrow(label, points, radius, mat):
    tip = Vector(points[-1])
    axis = (tip - Vector(points[-2])).normalized()
    depth = 5 * radius
    base = tip - axis * depth
    tube(label + " path", points[:-1] + [tuple(base)], radius, mat)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius * 2.6, radius2=0,
                                    depth=depth, location=(tip + base) / 2)
    head = bpy.context.object
    head.name = label + " direction"
    head.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    colorize(head, mat)


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    inputs = json.loads((HERE / "inputs.json").read_text())
    gland = material("Gland exterior", (.65, .42, .21))
    target = material("Target gland", (.55,.23,.18))
    duct = material("Hormone overlay", (.14,.40,.44))
    context = material("Locator outline", (.42,.48,.51))
    offsets = {}
    groups = {}
    specs = [
        ("pituitary", "Hypothalamus-pituitary", None, lambda n: True),
        ("adrenals", "Adrenal", None, lambda n: True),
        ("thyroid","Neck", (0,-.127,1.432), lambda n: True),
        ("pancreas","Pancreas", (.026,-.110,1.072), lambda n: any(w in n for w in
         ("tail_of","body_of","ucinate","head_of","neck_of"))),
        ("ovary","Pelvic ovary", (0,-.104,.831), lambda n: n.endswith("_ovary")),
        ("testes","Alternative testis inset", (.265,-.096,.780), lambda n: n.startswith("Testis")),
    ]
    for key, prefix, location, select in specs:
        group = load_meshes(**inputs[key], select=select)
        offsets[key] = place(group, location) if location else [0,0,0]
        for obj in group:
            obj.name = prefix+" - "+obj.name
            if key != "pituitary":   # retain the source's coloured stalk zones
                palette = {"adrenals": material("Adrenal cortex exterior", (.22,.42,.40)),
                           "ovary": target, "pancreas": gland}
                colorize(obj, target if "Thyroid gland" in obj.name else palette.get(key, gland))
        groups[key] = group
    # Editorial anterior silhouette cropped below the pelvis. +X is subject left.
    side = [(0,1.643),(.055,1.618),(.074,1.555),(.064,1.506),(.043,1.481),
            (.048,1.434),(.146,1.412),(.199,1.367),(.183,1.302),(.146,1.251),
            (.130,1.149),(.119,1.042),(.149,.958),(.164,.872),(.150,.760),(.133,.708)]
    loop = [(-x,.01,z) for x,z in reversed(side[1:])] + [(x,.01,z) for x,z in side]
    tube("Head to pelvis outline - schematic", loop, .0026, context)
    for key, center, radius in [("Male gonad alternative",(.265,-.092,.78),.052),
                                ("Islet inset",(.27,-.092,1.078),.066)]:
        x,y,z=center
        rim=[(x+radius*math.cos(i*math.tau/64),y+.015,z+radius*math.sin(i*math.tau/64)) for i in range(65)]
        tube(key + " frame", rim,.0014,context,smooth=False)
    # Illustrated islet microenvironment, enlarged and detached from the pancreas exterior.
    cell_mats = [material("Alpha - glucagon",(.65,.35,.18)),material("Beta - insulin",(.30,.49,.37))]
    for index,(x,z,kind) in enumerate([(-.026,.015,0),(-.009,.023,1),(.009,.018,1),
                                      (.021,.003,0),(.009,-.010,1),(-.009,-.013,1),
                                      (-.025,-.005,1),(0,.004,0),(.020,-.026,1)]):
        ellipsoid(f"Islet {'alpha' if kind==0 else 'beta'} cell {index+1}",(.27+x,-.093,1.078+z),
                        (.009,.007,.008),cell_mats[kind])
    tube("Islet capillary",[(.228,-.102,1.055),(.252,-.101,1.065),(.276,-.102,1.086),
                           (.297,-.100,1.090),(.313,-.098,1.109)],.0024,material("Capillary",(.52,.21,.13)))
    pit=groups["pituitary"][0]
    verts=[pit.matrix_world @ v.co for v in pit.data.vertices]
    hyp=max(verts,key=lambda v:v.z)
    pitbase=min(verts,key=lambda v:v.z)
    thyroid=next(o for o in groups["thyroid"] if "Thyroid gland" in o.name)
    thyroid_verts=[thyroid.matrix_world @ v.co for v in thyroid.data.vertices]
    th=max(thyroid_verts,key=lambda v:v.x)
    arrow("TRH - portal to anterior pituitary",[tuple(hyp),(-.017,-.117,1.548),(-.017,-.116,1.527),tuple(pitbase)],.0015,material("Portal overlay",(.69,.48,.19)))
    arrow("TSH - blood to thyroid",[tuple(pitbase),(.035,-.122,1.503),(.037,-.132,1.458),tuple(th)],.002,duct)
    for key in ("ovary","testes","adrenals"):
        if len(groups[key])!=2:
            raise ValueError("Bilateral pair missing " +key)
    export(out,"endocrine-locator")
    (out/"placement.json").write_text(json.dumps(dict(translations=offsets,
         signalAnchors=[list(p) for p in [hyp,pitbase,th]]),indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    build(parser.parse_args(sys.argv[sys.argv.index("--")+1:]).output)
