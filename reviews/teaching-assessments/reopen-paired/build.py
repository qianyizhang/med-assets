"""Build five teaching editions from exact historical owners into a fresh directory."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.artifacts import verify_bytes
from tools.rebuild_asset import build

RECIPES = {
    "anatomy-workshop-r1": "body/anatomy-workshop-r1/recipes/compact.json",
    "heart": "models/heart/recipes/texture-pack-r02.json",
    "diaphragm": "models/diaphragm/recipes/normal-pack-r02.json",
    "lymph": "models/lymph_node/recipes/tissue-color-pack-r02.json",
    "nose_sinuses": "models/nose_sinuses/recipes/index-pack-r02.json",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    reviewed = json.loads((HERE / "build.json").read_text())
    records = {}
    for key, path in RECIPES.items():
        recipe = json.loads((ROOT / path).read_text())
        source, edition = (reviewed[key][field] for field in ("source", "edition"))
        if recipe["source"] != source or recipe["output"] != edition:
            raise ValueError(f"Owner recipe pins differ from the paired review for {key}")
        candidate, metrics = build(recipe)
        verify_bytes(candidate, edition)
        result = {"source": source, "edition": edition, **metrics}
        if result != reviewed[key]:
            raise ValueError(f"Rebuilt measurements differ from the paired review for {key}")
        target = args.output / edition["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(candidate)
        records[key] = result
    (args.output / "build.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
