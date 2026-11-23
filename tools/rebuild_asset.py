#!/usr/bin/env python3
"""Replay a portable asset recipe and verify its reviewed output identity."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets import glb_projection, glb_repack
from med_assets.artifacts import repo_file, verify_bytes
from med_assets.glb import decode
from med_assets.glb_selection import select
from med_assets.native_blend import recompress


def payload(pinned):
    return verify_bytes(repo_file(ROOT, pinned["path"]).read_bytes(), pinned)


def build(recipe):
    source = recipe["source"]
    output = recipe["output"]
    data = payload(source)
    parameters = recipe.get("parameters", {})
    operation = recipe["operation"]

    if operation == "scene-selection":
        return select(data, {**parameters, "source": source["path"],
                             "sha256": source["sha256"], "file": Path(output["path"]).name})
    if operation == "exterior":
        doc, binary = decode(data)
        result, maps = glb_projection.project(
            doc, binary, set(parameters["omit"]), parameters["scope"], source["sha256"])
        retained = glb_projection.verify(doc, binary, result, maps)
        if len(result) >= len(data):
            raise ValueError("Projection did not save bytes")
        return result, {"verifiedAccessors": len(maps["accessors"]),
                        "retainedTriangles": glb_projection.count_triangles(retained)}
    if operation == "native-zstd":
        return recompress(data, **parameters)
    if operation == "normal-i8":
        return glb_repack.compact_normals(data, **parameters)
    if operation == "png":
        parameters = {**parameters, "expected_size": tuple(parameters["expected_size"])}
        result, measurements = glb_repack.compact_png(data, **parameters)
        return result, {"textures": measurements}

    operations = {"paired-png": glb_repack.png_streams, "normal-i16": glb_repack.normals,
                  "white-colors": glb_repack.colors, "index-u16": glb_repack.index_blocks}
    doc, binary = decode(data)
    result, measurements = operations[operation](doc, binary, **parameters)
    if operation == "index-u16":
        measurements["orderedCornerAttributesSha256"] = glb_repack.verify_triangles(data, result)
    return result, measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", type=Path)
    parser.add_argument("output", type=Path, help="Fresh output directory")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Output directory already exists: {args.output}")
    recipe = json.loads(args.recipe.read_text())
    result, measurements = build(recipe)
    expected = recipe["output"]
    verify_bytes(result, expected)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / Path(expected["path"]).name).write_bytes(result)
    receipt = {"source": recipe["source"], "edition": expected, "measurements": measurements}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Exact reviewed output: {expected['path']}")


if __name__ == "__main__":
    main()
