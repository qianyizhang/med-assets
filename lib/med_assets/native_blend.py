"""Losslessly repack a Zstandard-compressed Blender scene."""

import subprocess

from .glb_selection import identity


def recompress(data, level, threads):
    unpacked = subprocess.check_output(["zstd", "-qdc"], input=data)
    candidate = subprocess.check_output(
        ["zstd", "-q", f"-{level}", f"-T{threads}", "-c"], input=unpacked)
    if subprocess.check_output(["zstd", "-qdc"], input=candidate) != unpacked:
        raise ValueError("Native Blender stream changed")
    decoded = identity(unpacked)
    return candidate, {"decodedNativeFile": {"bytes": decoded["bytes"], "sha256": decoded["sha256"]}}
