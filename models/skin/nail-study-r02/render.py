"""Render the two clean GLB imports at a shared scale and pose."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from render_teaching import configure_scene, render_pair, sha256


PLATE = "Nail | Nail plate with free edge"
OFFSET = Vector((0.00016, 0, 0.00054))
CAMERA_BOUNDS = [[0.00402, 0, 0.00030], [0.00758, 0.00147, 0.00252]]
LEGENDS = {
    "original": [
        ("Distal digit tissue", "#cbaa91"),
        ("Proximal nail fold", "#cbaa91"),
        ("Germinal matrix", "#9a7891"),
        ("Nail bed", "#c6897d"),
        ("Nail plate and free edge", "#dbccb0"),
    ],
    "updated": [
        ("Distal digit tissue", "#bd947e"),
        ("Proximal nail fold", "#a5755e"),
        ("Germinal matrix", "#8a536c"),
        ("Nail bed", "#c77c73"),
        ("Nail plate", "#c9a694"),
        ("Free edge", "#e4d4b4"),
    ],
}


def render_model(glb, output, key):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()), disable_bone_shape=True)
    scene = bpy.context.scene
    configure_scene(scene)
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    view = {"include": ["Nail | *"], "cameraBounds": CAMERA_BOUNDS}
    assembled = render_pair(scene, meshes, {**view, "id": key}, output)
    scene.objects[PLATE].location += OFFSET
    lifted = render_pair(scene, meshes, {**view, "id": f"{key}-lifted"}, output)
    lifted["illustrativeDisplayOffsetMetres"] = list(OFFSET)
    for receipt in (assembled, lifted):
        receipt["glb"] = {"file": glb.name, "sha256": sha256(glb)}
        receipt["legend"] = [
            {"label": name, "color": color, "alpha": 1} for name, color in LEGENDS[key]
        ]
    return assembled, lifted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("updated", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    args.output.mkdir(parents=True, exist_ok=False)
    results = [
        *render_model(args.original, args.output, "original"),
        *render_model(args.updated, args.output, "updated"),
    ]
    record = {
        "blender": bpy.app.version_string,
        "cameraBounds": CAMERA_BOUNDS,
        "render": {"resolution": [800, 640], "engine": "Cycles CPU", "samples": 12, "viewTransform": "AgX", "exposure": 0, "transparent": True},
        "views": results,
    }
    (args.output / "renders.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
