"""Replay the right s1127 common carotid exteriors."""

import runpy
from pathlib import Path

from build_thyroid import AFFINE, SHAPE

HERE = Path(__file__).resolve().parent
MASK_SHA = "b96238f9bac2dab4a3467d5036816972dfc49529f2ba526fe8659a443c5281e2"

if __name__ == "__main__":
    shared = runpy.run_path(str(HERE.parent / "carotid_s1127/reconstruct.py"))
    shared["replay"](HERE, "right", MASK_SHA, SHAPE, AFFINE)
