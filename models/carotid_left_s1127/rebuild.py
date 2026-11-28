"""Replay the left s1127 common carotid exteriors."""

import runpy
from pathlib import Path

from build_thyroid import AFFINE, SHAPE

HERE = Path(__file__).resolve().parent
MASK_SHA = "1afcd7bef5e969daa5b4f09788dfabbd05d4a8fd260a140b90370e957e70fb10"


if __name__ == "__main__":
    shared = runpy.run_path(str(HERE.parent / "carotid_s1127/reconstruct.py"))
    shared["replay"](HERE, "left", MASK_SHA, SHAPE, AFFINE)
