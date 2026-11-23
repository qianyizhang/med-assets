"""Compatibility imports for the shared GLB toolkit."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from med_assets.glb import BIN_CHUNK, JSON_CHUNK, buffer_view_bytes, decode, encode, pack_buffer_view

__all__ = ['BIN_CHUNK', 'JSON_CHUNK', 'buffer_view_bytes', 'decode', 'encode', 'pack_buffer_view']
