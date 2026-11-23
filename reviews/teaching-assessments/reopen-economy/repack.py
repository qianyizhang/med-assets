"""Rebuild six full-scene teaching editions from their exact hydrated controls."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.artifacts import verify_bytes
from med_assets.glb import decode
from tools.rebuild_asset import build

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    folder = args.destination.resolve()
    if not folder.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh scratch output under .artifacts")
    folder.mkdir(parents=True, exist_ok=False)
    receipts = {}
    reviewed = json.loads((HERE / "measurements.json").read_text())
    for name, expected in reviewed.items():
        control, edition = expected["control"], expected["edition"]
        recipe = json.loads((ROOT / f"models/{name}/recipes/teaching-economy-r02.json").read_text())
        if recipe["source"] != control or recipe["output"] != edition:
            raise ValueError(f"Owner recipe pins differ from the full-scene review for {name}")
        data, metrics = build(recipe)
        verify_bytes(data, edition)
        doc, _ = decode(data)
        parts = [part for mesh in doc["meshes"] for part in mesh["primitives"]]
        result = {
            "control": control,
            "edition": edition,
            "bytesSaved": control["bytes"] - len(data),
            "meshCount": len(doc["meshes"]),
            "primitives": len(parts),
            "triangles": sum(doc["accessors"][part["indices"]]["count"] // 3 for part in parts),
            **metrics,
        }
        if result != expected:
            raise ValueError(f"Rebuilt measurements differ from the full-scene review for {name}")
        target = folder / name / Path(edition["path"]).name
        target.parent.mkdir()
        target.write_bytes(data)
        receipts[name] = result
    (folder / "measurements.json").write_text(json.dumps(receipts, indent=2) + "\n")


if __name__ == "__main__":
    main()
