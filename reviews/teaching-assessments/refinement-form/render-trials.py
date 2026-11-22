"""Clean-import exact candidate GLBs and compare in matched neutral cameras."""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMERAS = HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine" / "render.py"
AIRWAY = ROOT / "reviews/bronchial_tree/2026-11-21-distal-simplification-trial/views.json"
THYROID = ROOT / "reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/renders/raster-bindings.json"


def load_camera_tools():
    spec = spec_from_file_location("campaign_cameras", CAMERAS)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cameras(key):
    if key == "bronchial_tree":
        prior = json.loads(AIRWAY.read_text())
        return [
            (name, row["position"], row["quaternion"], row["orthoScaleMeters"])
            for name, row in prior.items()
            if name in {"whole", "close", "opposite-close", "rotated-close"}
        ]
    prior = json.loads(THYROID.read_text())
    rows = [
        (name, r["camera"], list((Vector(r["camera"]) - Vector(r["target"])).to_track_quat("Z", "Y")), r["orthoscale"])
        for name in ("whole", "reverse", "oblique", "ridge-detail")
        for r in prior if r["file"] == f"updated-{name}.png"
    ]
    pos = Vector((-.045, .330, .667))
    q = (pos - Vector((-.016, .173, .617))).to_track_quat("Z", "Y")
    return rows + [("rear-band", list(pos), list(q), .041)]


def capture(key, kind, inputs, output, tools):
    identity = inputs["control"] if kind == "original" else inputs["trial"]
    path = input_dir / identity["file"] if kind == "trial" else ROOT / identity["path"]
    if tools.identity(path) != {k: identity[k] for k in ("sha256", "bytes")}:
        raise ValueError(f"Wrong input bytes: {path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == "MESH"]
    if len(meshes) != 1:
        raise ValueError("Expected one mesh on clean reimport")
    obj = meshes[0]
    obj.data.calc_loop_triangles()
    camera = tools.configure(scene)
    if key == "bronchial_tree":
        scene.render.resolution_y = 544
    camera.data.clip_start = .001
    camera.data.clip_end = 5
    views = []
    for label, position, rotation, scale in cameras(key):
        camera.location = position
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = Quaternion(rotation)
        camera.data.ortho_scale = scale
        name = f"{key}-{kind}-{label}.png"
        view = tools.shot(scene, camera, meshes, [0, 0, 0], output / name, False, fixed=True)
        del view["direction"]
        view["rotation"] = list(rotation)
        views.append(view)
    return {"glb": {k: identity[k] for k in ("bytes", "sha256")},
            "triangles": len(obj.data.loop_triangles), "views": views}


def main():
    global input_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    tools = load_camera_tools()
    input_dir = args.input
    inputs = json.loads((input_dir / "trial-build.json").read_text())
    args.output.mkdir(exist_ok=False, parents=True)
    record = {"blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(), "assets": {}}
    for key, row in inputs.items():
        record["assets"][key] = {kind: capture(key, kind, row, args.output, tools)
                                 for kind in ("original", "trial")}
    (args.output / "trial-render.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
