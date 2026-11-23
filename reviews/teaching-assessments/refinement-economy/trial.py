"""Build same-scene teaching mesh trials from pinned GLBs and render clean imports."""
import argparse
import json
from pathlib import Path
import re
import runpy
import sys

from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.blender_scene import scene_import
from med_assets.glb import decode
from med_assets.glb_selection import identity
from med_assets.mesh_contraction import (
    contract,
    geometry_replacements,
    lossless_budget,
    replace_accessors,
    simplify,
    verify_streams,
)
from med_assets.triangle_geometry import oriented

VIEWS = runpy.run_path(str(HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"))


def camera_views(row, scene, objects, folder, side, bindings):
    camera = VIEWS["configure"](scene)
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    result = []
    for index, view in enumerate(row["views"]):
        visible = [o for n, o in objects.items()
                   if not view.get("visible") or re.search(view["visible"], n, re.I)]
        framed = [o for n, o in objects.items()
                  if re.search(view["focus"], n, re.I)] if view.get("focus") else visible
        if not framed:
            raise ValueError(f"No matched focus for {row['name']} {view}")
        direction = view["direction"]
        if bindings is None:
            VIEWS["frame_camera"](camera, framed, direction)
            camera.data.ortho_scale *= view.get("zoom", 1.)
            if "offset" in view:
                camera.location += Vector(view["offset"])
        else:
            binding = bindings[index]
            camera.location = binding["location"]
            camera.rotation_mode = "QUATERNION"
            camera.rotation_quaternion = binding["rotation"]
            camera.data.clip_start = binding["clip"][0]
            camera.data.clip_end = binding["clip"][1]
            camera.data.ortho_scale = binding["ortho"]
        output = folder / f"{side}-{index}.png"
        info = VIEWS["shot"](scene, camera, list(objects.values()), direction, output,
                             view.get("palette", True), visible, fixed=True)
        result.append({"file": output.name, "sha256": info["sha256"], "camera": direction,
                       "location": list(camera.location), "rotation": list(camera.rotation_quaternion),
                       "clip": [camera.data.clip_start, camera.data.clip_end],
                       "ortho": camera.data.ortho_scale})
    return result


def run(row, folder, render):
    return contract(row, folder, camera_views if render else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--recovered", action="append", default=[], metavar="NAME=PATH")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    rows = json.loads((HERE / "trials.json").read_text())
    selected = [row for row in rows if not args.only or row["name"] in args.only]
    recovered = {}
    for argument in args.recovered:
        name, sep, path = argument.partition("=")
        if not sep or not path:
            parser.error("--recovered requires NAME=PATH")
        recovered[name] = path
    reuse_names = {row["name"] for row in selected if row["plan"] == "reuse"}
    if recovered.keys() - reuse_names:
        parser.error("A recovery path must name a selected owner trial")
    for row in selected:
        if row["name"] in recovered:
            path = Path(recovered[row["name"]]).resolve()
            if not path.is_relative_to(ROOT / ".artifacts"):
                parser.error("A recovered candidate must be in the ignored .artifacts directory")
            row["candidate"]["path"] = str(path.relative_to(ROOT))
    if args.only and set(args.only) != {row["name"] for row in selected}:
        parser.error("Unknown trial name")
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a new output directory under .artifacts")
    out.mkdir(exist_ok=False, parents=True)
    index = []
    for row in selected:
        folder = out / row["name"]
        folder.mkdir()
        print(f"START {row['name']}", flush=True)
        try:
            result = run(row, folder, not args.no_render)
            index.append(result)
            print(f"DONE {row['name']}", flush=True)
        except (OSError, ValueError) as error:
            index.append({"name": row["name"], "error": str(error)})
            print(f"FAILED {row['name']}: {error}", flush=True)
        (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    if any("error" in row for row in index):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
