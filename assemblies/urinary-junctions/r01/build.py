"""Compose the Workshop teaching sections and an enlarged filtration inset."""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import colorize, export, load_meshes, material, tube


def cue(name, point, direction, mat, radius):
    axis = Vector(direction).normalized()
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, radius1=radius, radius2=0, depth=3 * radius, location=point
    )
    obj = bpy.context.object
    obj.name = "Flow overlay - " + name
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    colorize(obj, mat)


def cap_center(obj, direction):
    axis = Vector(direction).normalized()
    coords = {tuple(v.co) for v in obj.data.vertices}
    end = max(Vector(p).dot(axis) for p in coords)
    rim = [Vector(p) for p in coords if abs(Vector(p).dot(axis) - end) < 1e-6]
    if len(rim) < 8:
        raise ValueError(f"Incomplete end ring for {obj.name}: {len(rim)} vertices")
    return sum(rim, Vector()) / len(rim)


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    inputs = json.loads((HERE / "inputs.json").read_text())
    organ = material("Renal section", (0.55, 0.23, 0.18))
    uro = material("Urine pathway", (0.69, 0.51, 0.23))
    flow = material("Flow arrows", (0.16, 0.42, 0.45))
    blood = material("Glomerular blood", (0.52, 0.21, 0.13))
    landmarks = {}
    bladder = load_meshes(
        **inputs["bladder"],
        select=lambda n: any(
            t in n for t in ("anterior teaching", "trigone", "urethral outlet")
        ),
    )
    trigone = next(o for o in bladder if "trigone" in o.name)
    outlet = next(o for o in bladder if "urethral" in o.name)
    for obj in bladder:
        colorize(
            obj,
            uro
            if obj == outlet
            else material("Trigone", (0.43, 0.61, 0.58))
            if obj == trigone
            else organ,
        )
    tri = [v.co.copy() for v in trigone.data.vertices]
    lower = min(tri, key=lambda v: v.z)
    urethra = cap_center(outlet, (0, -0.003, 0.021))
    neck = tube(
        "Bladder neck to urethral outlet",
        [lower, (0, -0.025, -0.315), urethra],
        0.0027,
        uro,
    )
    landmarks["bladder-outlet"] = [list(lower), trigone.name, neck.name]
    landmarks["outlet-join"] = [list(urethra), neck.name, outlet.name]
    cue("outlet", (0.009, -0.029, -0.331), (0, 0, -1), flow, 0.003)
    for side, sign in [("left", 1), ("right", -1)]:
        key = "kidney_" + side
        prefix = side.capitalize()
        kidney = load_meshes(**inputs[key], select=lambda n: "source surface" not in n)
        for obj in kidney:
            obj.name = prefix + " " + obj.name.removeprefix(key + " ").replace("| ", "")
            mat = uro
            if "section" in obj.name:
                mat = (
                    organ
                    if "closed-back" in obj.name
                    else material("Renal medulla", (0.65, 0.42, 0.30))
                )
            colorize(obj, mat)
        origin = next(o for o in kidney if "single ureter origin" in o.name)
        start = cap_center(origin, (-sign * 0.001, 0.001, -0.011))
        end = max(tri, key=lambda v: v.x * sign)
        mid = (sign * 0.026, 0.005, -0.210)
        a = Vector((start.x * 0.83, start.y, start.z - 0.014))
        b = Vector((sign * 0.020, -0.009, -0.255))
        course = tube(prefix + " middle ureter", [a, mid, b], 0.0018, uro)
        inlet = tube(
            prefix + " proximal ureter", [start, start.lerp(a, 0.48), a], 0.0018, uro
        )
        distal = tube(
            prefix + " distal ureter", [b, b.lerp(end, 0.48), end], 0.0018, uro
        )
        landmarks[side + "-renal"] = [list(start), origin.name, inlet.name]
        landmarks[side + "-upper-course"] = [list(a), inlet.name, course.name]
        landmarks[side + "-lower-course"] = [list(b), course.name, distal.name]
        landmarks[side + "-vesical"] = [list(end), distal.name, trigone.name]
        cue(
            side + " ureter",
            (mid[0] + sign * 0.007, mid[1] - 0.003, mid[2]),
            (-sign * 0.35, 0, -1),
            flow,
            0.0035,
        )
    # Enlarged open renal corpuscle; front arc omitted to expose capillary loops.
    cx, cy, cz = 0.184, -0.012, -0.153

    def at(x, y, z):
        return (cx + x, cy + y, cz + z)

    points = []
    for i in range(61):
        angle = math.radians(43 + i * 274 / 60)
        points.append(at(0.032 * math.sin(angle), 0.003, 0.032 * math.cos(angle)))
    tube("Filtration - open Bowman capsule profile", points, 0.0028, uro, smooth=False)
    points = [at(-0.017, -0.001, 0.022)]
    for i in range(145):
        t = -0.44 + (math.tau - 1.02) * (-i / 144)
        points.append(
            at(
                0.017 * math.sin(t) + 0.005 * math.sin(5 * t),
                0.008 * math.sin(3 * t),
                0.013 * math.cos(t) + 0.005 * math.cos(5 * t),
            )
        )
    points.append(at(0.014, 0, 0.022))
    tube("Filtration - glomerular capillary tuft", points, 0.0021, blood, smooth=False)
    tube(
        "Filtration - afferent arteriole",
        [at(-0.030, 0, 0.044), at(-0.022, 0, 0.030), points[0]],
        0.0036,
        blood,
    )
    tube(
        "Filtration - efferent arteriole",
        [points[-1], at(0.020, 0, 0.032), at(0.030, 0.002, 0.043)],
        0.0026,
        blood,
    )
    tube(
        "Filtration - proximal tubule",
        [
            at(0, 0.003, -0.032),
            at(0.004, 0.003, -0.039),
            at(0.019, 0, -0.044),
            at(0.023, -0.002, -0.053),
            at(0.013, -0.004, -0.058),
        ],
        0.0031,
        uro,
    )
    cue(
        "filtrate to capsular space",
        at(0.022, -0.004, -0.008),
        (1, 0, -0.4),
        flow,
        0.0027,
    )
    cue("filtrate to tubule", at(0.006, -0.005, -0.034), (0.4, 0, -1), flow, 0.0022)
    export(out, "urinary-junctions")
    (out / "junctions.json").write_text(json.dumps(landmarks, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args(sys.argv[sys.argv.index("--") + 1 :]).output)
