"""Clean reimport each edition and capture its protected task in matched original cameras."""

import json
from pathlib import Path
import re
import runpy
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOLS = runpy.run_path(str(HERE.parent / "refinement-economy/trial.py"))
SELECT = runpy.run_path(str(HERE.parent / "refinement-form/render-selections.py"))
CONFIG = json.loads((HERE.parent / "target-form/economy-settings.json").read_text())
ROWS = {x["name"]: x for x in CONFIG}


def record_part(obj, out):
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    mesh.calc_loop_triangles()
    np.savez_compressed(
        out,
        xyz=np.array([list(obj.matrix_world @ v.co) for v in mesh.vertices]),
        triangles=np.array([list(f.vertices) for f in mesh.loop_triangles]),
    )


def scene_and_views(key, binding, folder, side):
    row = ROWS.get(key, {})
    scene, meshes = TOOLS["VIEWS"]["open_model"](binding)
    if key == "anatomy-workshop-r1":
        scene, meshes = SELECT["snapshot_visible_meshes"](meshes)
    objects = {obj.name: obj for obj in meshes}
    if side == "edition" and key in (
        "anatomy-workshop-r1",
        "heart",
        "nose_sinuses",
        "lymph",
    ):
        for name, obj in objects.items():
            if key != "anatomy-workshop-r1" or "Lung Lower Lobe" in name:
                record_part(
                    obj,
                    folder / (re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") + ".npz"),
                )
    if key == "anatomy-workshop-r1":
        views = SELECT["workshop"](objects)[1:]
        row = {
            "views": [
                {
                    "direction": v[1],
                    "visible": "|".join(re.escape(n) for n in v[3]),
                    "palette": False,
                }
                for v in views
            ]
        }
    if key == "lymph":
        colors = runpy.run_path(str(HERE.parent / "refinement-risk/render.py"))[
            "COLORS"
        ]
        for name, obj in objects.items():
            if name in colors:
                for slot in obj.material_slots:
                    slot.material.diffuse_color = colors[name]
        row = {
            "views": [
                {
                    "direction": [0.25, -0.9, 0.2],
                    "focus": "capsule",
                    "visible": "capsule",
                    "palette": False,
                },
                {
                    "direction": [0.25, -0.9, 0.2],
                    "focus": "capsule",
                    "visible": "follicles|paracortex|medulla",
                },
                {
                    "direction": [-0.62, -0.55, -0.41],
                    "focus": "capsule",
                    "visible": "medulla",
                    "palette": False,
                },
            ]
        }
    row = {**row, "name": key}
    return row, scene, objects


def main():
    build, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
    output.mkdir(parents=True, exist_ok=False)
    bindings = json.loads((build / "build.json").read_text())
    if bindings != json.loads((HERE / "build.json").read_text()):
        raise ValueError(
            "Reimport requires all five reviewed editions and their exact controls"
        )
    result = {}
    for key, record in bindings.items():
        folder = output / key
        folder.mkdir()
        matches = None
        result[key] = {}
        for side in ("source", "edition"):
            binding = record[side]
            if side == "edition":
                binding = {**binding, "path": str((build / binding["path"]).resolve())}
            row, scene, objects = scene_and_views(key, binding, folder, side)
            matches = TOOLS["camera_views"](row, scene, objects, folder, side, matches)
            stats = {}
            for name, obj in objects.items():
                obj.data.calc_loop_triangles()
                stats[name] = len(obj.data.loop_triangles)
            result[key][side] = {
                "asset": record[side],
                "views": matches,
                "triangles": stats,
            }
        if result[key]["source"]["triangles"] != result[key]["edition"]["triangles"]:
            raise ValueError(
                f"Clean imports disagree on triangles or object identity: {key}"
            )
        result[key]["sectionInputs"] = {
            p.name: TOOLS["identity"](p.read_bytes())
            for p in sorted(folder.glob("*.npz"))
        }
        (output / "render.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
