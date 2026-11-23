"""Compatibility imports for the shared GLB toolkit."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from med_assets.glb_selection import identity, require, select

__all__ = ['identity', 'require', 'select']
