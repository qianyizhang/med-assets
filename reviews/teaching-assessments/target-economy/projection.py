"""Build and compare four exact, task-scoped HRA scene projections."""

import argparse
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / "refinement-economy"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))
from tools.glb import decode
from med_assets.glb_projection import count_triangles, project, verify

def run(task, options, folder, helpers):
    control = ROOT / task["path"]
    data = control.read_bytes()
    identity = helpers["identity"]
    if identity(data) != {key: task[key] for key in ("sha256", "bytes")}:
        raise ValueError(f"Wrong or unhydrated control {control}")
    source, original_binary = decode(data)
    edition, maps = project(source, original_binary, set(options["omit"]), options["scope"], task["sha256"])
    doc = verify(source, original_binary, edition, maps)
    if len(edition) >= len(data):
        raise ValueError("Projection did not save bytes")
    candidate = folder / "candidate.glb"
    candidate.write_bytes(edition)
    scene_import, camera_views = (helpers[key] for key in ("scene_import", "camera_views"))
    scene, objects, stats = scene_import(control)
    bindings = camera_views(task, scene, objects, folder, "control", None)
    scene, objects, after = scene_import(candidate)
    if not after.keys() <= stats.keys() or any(stats[name] != item for name, item in after.items()):
        raise ValueError("Retained mesh names, world transforms, materials, shape data or triangle counts changed")
    candidate_bindings = camera_views(task, scene, objects, folder, "candidate", bindings)
    return {
        "name": task["name"],
        "control": {"path": task["path"], **identity(data), "triangles": count_triangles(source)},
        "candidate": {**identity(edition), "triangles": count_triangles(doc)},
        "scope": options["scope"],
        "omittedMeshes": [node["name"] for i, node in enumerate(source["nodes"])
                          if i not in maps["nodes"] and "mesh" in node],
        "retainedMeshes": list(after),
        "verifiedAccessors": len(maps["accessors"]),
        "bindings": {"control": bindings, "candidate": candidate_bindings},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh directory under .artifacts")
    out.mkdir(exist_ok=False, parents=True)
    options = json.loads((HERE / "projections.json").read_text())
    controls = json.loads((PREVIOUS / "trials.json").read_text())
    helpers = runpy.run_path(str(PREVIOUS / "trial.py"))
    results = []
    for task in controls:
        name = task["name"]
        if name not in options:
            continue
        folder = out / name
        folder.mkdir()
        plan = options[name]
        results.append(run({**task, "views": plan.get("views", task["views"])}, plan, folder, helpers))
        (out / "index.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
