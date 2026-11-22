"""Repack exact heart and bladder selections with their source frames and channels."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb_selection import select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selections = json.loads((HERE / "selections.json").read_text())
    parser.add_argument("family", choices=selections)
    parser.add_argument("output", type=Path, help="Fresh output directory")
    args = parser.parse_args()
    spec = selections[args.family]
    raw = (ROOT / spec["source"]).read_bytes()
    result, receipt = select(raw, spec)
    args.output.mkdir()
    (args.output / spec["file"]).write_bytes(result)
    (args.output / "selection.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
