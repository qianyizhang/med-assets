"""Clean-import both editions under the previous task cameras and one protected detail."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ADDITIONAL = {
    "brain": {"direction": [.74, 1, -.4], "visible": "cerebellum|medulla oblongata|pons",
              "focus": "cerebellum", "palette": False},
    "trachea": {"direction": [-.21, 1, .32], "focus": "C-band 8$", "palette": False},
    "liver": {"direction": [.22, 1, .24], "focus": "bare_area", "palette": False},
    "muscle": {"direction": [.14, -1, .1], "focus": "pectoralis major|rectus abdominis", "palette": False},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    folder = args.output.resolve()
    if not folder.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh directory under .artifacts")
    folder.mkdir(parents=True, exist_ok=False)
    records = json.loads((args.build / "measurements.json").read_text())
    renderer = runpy.run_path(str(HERE.parent / "refinement-economy/trial.py"))
    rows = {r["name"]: r for r in json.loads((HERE.parent / "refinement-economy/trials.json").read_text())}
    for name, spec in records.items():
        output = folder / name
        output.mkdir()
        candidate = args.build / name / Path(spec["edition"]["path"]).name
        for path, binding in ((candidate, spec["edition"]), (ROOT / spec["control"]["path"], spec["control"])):
            if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
                raise ValueError(f"Unexpected export digest for {path}")
        if name == "stomach":
            digestive = runpy.run_path(str(HERE.parent / "target-risk/review_blender.py"))
            helper = runpy.run_path(str(HERE.parent / "refinement-risk/render.py"))
            helper["take"].__globals__["OUTPUT"] = output
            helper["opening"].__globals__["SIZE"] = 640
            digestive["digestive"](helper, output, name, digestive["identity"](candidate))
            continue
        row = dict(rows[name])
        row["views"] = row["views"] + ([ADDITIONAL[name]] if name in ADDITIONAL else [])
        if name == "trachea":
            row["views"].extend([{"direction": [sign, -.18, -.56], "palette": True}
                                 for sign in (-1, 1)])
        frames = {}
        for side, path in (("original", ROOT / spec["control"]["path"]), ("updated", candidate.resolve())):
            scene, objects, inventory = renderer["scene_import"](path)
            if side == "original":
                source_inventory = inventory
            elif inventory != source_inventory:
                raise ValueError(f"Clean-import mesh names/counts/transforms/materials/shape keys changed in {name}")
            frames[side] = renderer["camera_views"](row, scene, objects, output, side, frames.get("original"))
        result = {"frames": frames, "views": row["views"], "cleanImportMeshes": len(inventory),
                  "blender": bpy.app.version_string, "build": bpy.app.build_hash.decode()}
        (output / "frames.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
