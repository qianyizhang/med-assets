"""Replay bounded follow-up trials against the same hydrated TAQ-012 controls."""
import argparse
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / "refinement-economy"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--repacked-lung", type=Path, help="Directory from the s1233 lung owner rebuild")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    controls = {row["name"]: row for row in json.loads((PREVIOUS / "trials.json").read_text())}
    plans = json.loads((HERE / "sweep-settings.json").read_text())
    if args.repacked_lung:
        folder = args.repacked_lung.resolve()
        if not folder.is_relative_to(ROOT / ".artifacts"):
            parser.error("Use the texture repack under .artifacts")
        reviewed = json.loads((HERE / "lung-render.json").read_text())["candidate"]
        candidate = folder / Path(reviewed["path"]).name
        plans["lung_left"] = {
            "plan": "reuse",
            "candidate": {**reviewed, "path": str(candidate.relative_to(ROOT))},
        }
    selected = set(args.only) if args.only else set(plans)
    if selected - set(plans):
        parser.error("Unknown trial")
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh directory under .artifacts")
    out.mkdir(exist_ok=False, parents=True)
    run_trial = runpy.run_path(str(PREVIOUS / "trial.py"))["run"]
    results = []
    for name, settings in plans.items():
        if name not in selected:
            continue
        row = {**controls[name], **settings}
        folder = out / name
        folder.mkdir()
        print(f"START {name}", flush=True)
        try:
            results.append(run_trial(row, folder, render=True))
        except (OSError, ValueError) as error:
            results.append({"name": name, "error": str(error)})
            print(f"FAILED {name}: {error}", flush=True)
        (out / "index.json").write_text(json.dumps(results, indent=2) + "\n")
    if any("error" in result for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
