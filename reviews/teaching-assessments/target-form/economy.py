"""Build and check bounded economy options for the TAQ-016 form controls."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / "refinement-form"
TRIAL = HERE.parent / "refinement-economy/trial.py"
PACKED = HERE / "economy-settings.json"


def run_economy(row, folder, tools):
    run = tools["run"]
    if row["name"] != "heart":
        return run(row, folder, True)
    # The shared static gate excludes texture/motion by default. The exact
    # heart has PBR images and one transform-only clip, independent of mesh
    # indices. Use the same checked accessor operations and verify untouched
    # image and animation data before running the clean import comparison.
    data = (ROOT / row["path"]).read_bytes()
    if tools["identity"](data) != {key: row[key] for key in ("sha256", "bytes")}:
        raise ValueError("Heart control identity changed")
    source, binary = tools["decode"](data)
    if (source.get("skins") or len(source.get("animations", [])) != 1
            or [c["target"]["path"] for c in source["animations"][0]["channels"]] != ["translation"]):
        raise ValueError("Expected the one pinned transform-only clip")
    edited, relocated, sparse, parts, count, reduced = tools["geometry_replacements"](
        row, source, binary, row["worldSpan"])
    result = {"name": row["name"], "control": {"path": row["path"], **tools["identity"](data), "triangles": count},
              "parts": parts, "candidate": None, "bindings": {},
              "losslessBudget": tools["lossless_budget"](*tools["decode"](data)),
              "rejectedPreview": any(part.get("rejectedPreview") for part in parts)}
    scene, meshes, inventory = tools["scene_import"](ROOT / row["path"])
    result["bindings"]["control"] = tools["camera_views"](row, scene, meshes, folder, "control", None)
    if edited:
        candidate = tools["replace_accessors"](source, binary, edited, relocated, sparse)
        tools["verify_streams"](data, candidate, edited, relocated)
        output = folder / ("rejected-preview.glb" if result["rejectedPreview"] else "candidate.glb")
        output.write_bytes(candidate)
        scene, meshes, after = tools["scene_import"](output)
        if inventory.keys() != after.keys() or any(
            left[key] != after[name][key]
            for name, left in inventory.items() for key in left if key != "triangles"
        ):
            raise ValueError("Heart scene, transforms or materials changed after reimport")
        result["candidate"] = {"path": str(output.relative_to(ROOT)), **tools["identity"](candidate),
                               "triangles": reduced}
        result["bindings"]["candidate"] = tools["camera_views"](
            row, scene, meshes, folder, "candidate", result["bindings"]["control"])
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def vagina(control, candidate, folder, tools):
    render_tools = runpy.run_path(str(HERE / "render.py"))
    row = {"views": [
        {"direction": (1, -.21, .16), "palette": False},
        {"direction": (1, -.21, .16), "palette": False},
        {"direction": (-1, -.24, .16), "palette": False},
    ]}
    before_scene, registry = render_tools["import_meshes"](control)
    keep = runpy.run_path(str(ROOT / "models/vagina_hra/recipes/teaching-context-r03/build.py"))["KEEP"]
    visible = {name: mesh for name, mesh in registry.items() if name in keep}
    before = render_tools["packed"](visible)
    names = "|".join(keep)
    row["views"][1].update(visible=names)
    row["views"][2].update(visible=names, focus=names)
    original = tools["camera_views"](row, before_scene, registry, folder, "control", None)
    scene, objects = render_tools["import_meshes"](candidate)
    after = render_tools["packed"](objects)
    exact = render_tools["compare"]("ovary", before, after, False)
    row["views"][1].pop("visible")
    row["views"][2].pop("visible")
    row["views"][2].pop("focus")
    updated = tools["camera_views"](row, scene, objects, folder, "candidate", original)
    result = {"control": tools["identity"](control.read_bytes()), "candidate": tools["identity"](candidate.read_bytes()),
              "bindings": {"control": original, "candidate": updated}, "exactRetained": exact}
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")


def workshop(control, folder, tools):
    selectors = runpy.run_path(str(BASE / "render-selections.py"))
    campaign = tools["VIEWS"]
    source, meshes = campaign["open_model"]({
        "path": str(control), "sha256": "c773480a49471e697e12ca1a710a4c93314217a8683e6ab224b3fa83d9a12fbc",
        "bytes": 17571351,
    })
    scene, meshes = selectors["snapshot_visible_meshes"](meshes)
    inventory = {obj.name: obj for obj in meshes}
    rows = selectors["workshop"](inventory)
    chosen = rows[1][3]
    row = {"views": [{"direction": shot[1], "focus": "|".join(chosen),
                       "visible": "|".join(shot[3] or ()), "palette": False} for shot in rows]}
    base = tools["camera_views"](row, scene, inventory, folder, "control", None)
    for obj in meshes:
        obj.data.calc_loop_triangles()
    before = {obj.name: len(obj.data.loop_triangles) for obj in meshes}
    evaluated = []
    for name in chosen:
        obj = inventory[name]
        if not name.startswith("Lung"):
            continue
        reduction = obj.modifiers.new("Disposable surface reduction", "DECIMATE")
        reduction.ratio = .65
        evaluated.append(obj)
    bpy.context.view_layer.update()
    after = before.copy()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in evaluated:
        mesh = obj.evaluated_get(depsgraph).data
        mesh.calc_loop_triangles()
        after[obj.name] = len(mesh.loop_triangles)
    trial = tools["camera_views"](row, scene, inventory, folder, "trial", base)
    result = {"control": tools["identity"](control.read_bytes()), "before": before, "after": after,
              "bindings": {"control": base, "trial": trial}, "frozenSnapshot": True}
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--settings", type=Path, default=PACKED)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    tools = runpy.run_path(str(TRIAL))
    controls = json.loads((BASE / "controls.json").read_text())
    for row in json.loads(args.settings.read_text()):
        name = row["name"]
        if args.only and name not in args.only:
            continue
        folder = args.output / name
        folder.mkdir()
        if name == "vagina_hra":
            vagina(ROOT / controls[name]["path"], args.candidate, folder, tools)
        elif name == "anatomy-workshop-r1":
            workshop(ROOT / controls[name]["path"], folder, tools)
        else:
            run_economy({**controls[name], **row}, folder, tools)


if __name__ == "__main__":
    main()
