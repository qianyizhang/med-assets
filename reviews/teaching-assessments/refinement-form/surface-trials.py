"""Build localized presentation trials with original GLB triangles and source frames."""

import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.surface_fairing import blend, export_trial, fair, load_mesh

thyroid_recipe = ROOT / "models/thyroid_ct_s0189/recipes/illustrative-exterior-r02/build.py"
thyroid_trial = runpy.run_path(str(thyroid_recipe))["thyroid_trial"]

def airway_trial(row, output):
    doc, binary, ids, pos, normals, faces = load_mesh(row)
    # The two source-frame trial supports target the lower junction and opposite
    # collar. Each support fades into the complete untouched branches.
    centers = np.array([[.000, .076, -.002], [-.005, .082, -.013]])
    distance = np.min(np.stack([np.linalg.norm(pos - p, axis=1) for p in centers]), axis=0)
    weight = blend((.014 - distance) / .010)
    updated = fair(pos, faces, weight, .00075, 120, compensation=.18)
    return export_trial(doc, binary, ids, pos, normals, faces, updated, weight,
                        output / "airway-trial.glb",
                        "Localized junction fairing of the authored exterior. No lumen, new branch or anatomy validation.",
                        weight == 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a fresh output directory")
    rows = json.loads((HERE / "controls.json").read_text())
    trials = {"thyroid_ct_s0189": thyroid_trial, "bronchial_tree": airway_trial}
    args.output.mkdir(parents=True)
    scores = {key: {"control": rows[key], "trial": fn(rows[key], args.output)}
              for key, fn in trials.items()}
    (args.output / "trial-build.json").write_text(json.dumps(scores, indent=2) + "\n")


if __name__ == "__main__":
    main()
