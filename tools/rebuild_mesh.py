"""Replay pinned mesh contractions and exterior projections in Blender."""

import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.artifacts import verify_bytes
from med_assets.blender_scene import scene_import
from med_assets.mesh_contraction import contract
from tools.rebuild_asset import build


def replay(recipe, folder):
    expected = recipe["output"]
    path = folder / Path(expected["path"]).name
    if recipe["operation"] == "mesh-contraction":
        row = {**recipe["parameters"], **recipe["source"]}
        receipt = contract(row, folder, candidate_name=path.name)
        if receipt["rejectedPreview"] or receipt["candidate"]["triangles"] != expected["triangles"]:
            raise ValueError(f"Unexpected contraction result for {expected['path']}")
        verify_bytes(path.read_bytes(), expected)
    elif recipe["operation"] == "exterior":
        data, receipt = build(recipe)
        verify_bytes(data, expected)
        path.write_bytes(data)
        _, _, original = scene_import(ROOT / recipe["source"]["path"])
        _, _, retained = scene_import(path)
        if not retained.keys() <= original.keys() or any(original[n] != s for n, s in retained.items()):
            raise ValueError("Clean import changed retained meshes, transforms, materials or shape keys")
        (folder / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    else:
        raise ValueError(f"Unsupported Blender recipe operation: {recipe['operation']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Fresh directory under .artifacts")
    parser.add_argument("recipes", nargs="+", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if bpy.app.build_hash.decode() != "fab76e95306d":
        parser.error("Use Blender 5.2.3 LTS Release Candidate fab76e95306d")
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh output directory under .artifacts")
    output.mkdir(parents=True, exist_ok=False)
    for recipe_path in args.recipes:
        recipe = json.loads(recipe_path.read_text())
        owner = Path(recipe["output"]["path"]).parts[1]
        folder = output / owner
        folder.mkdir()
        replay(recipe, folder)
        print(f"Exact reviewed output: {recipe['output']['path']}", flush=True)


if __name__ == "__main__":
    main()
