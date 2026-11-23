"""Repack the exact embedded s1233 PNG pixels and verify retained GLB streams."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))
from med_assets.glb_repack import compact_png as repack

TRIALS = HERE.parent / "refinement-economy" / "trials.json"


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    folder = args.out.resolve()
    if not folder.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh directory under .artifacts")
    task, = [row for row in json.loads(TRIALS.read_text()) if row["name"] == "lung_left"]
    source = (ROOT / task["path"]).read_bytes()
    if identity(source) != {key: task[key] for key in ("sha256", "bytes")}:
        raise ValueError("Wrong or unhydrated s1233 control")
    output, images = repack(source)
    folder.mkdir(exist_ok=False, parents=True)
    (folder / "candidate.glb").write_bytes(output)
    receipt = {"control": {"path": task["path"], **identity(source)},
               "candidate": identity(output), "textures": images}
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
