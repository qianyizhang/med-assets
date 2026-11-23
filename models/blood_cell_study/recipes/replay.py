#!/usr/bin/env python3
"""Re-export the exact saved baked blood-cell scene in Blender 4.3.2."""

import argparse
import hashlib
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "source/blood-cell-authored-study-r05-public.blend"
SOURCE_SHA256 = "f3123f0c84444ada60a2c0abe81520b166da4a4be69ba447211c11ada2191ad1"
EXPORT_SHA256 = "4c7c738b3ca6ae6cc7e44a449be0f7d26d04ceb9975e43d3b834a2caad96618c"


def verify(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Identity mismatch for {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blender", default="blender")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a fresh output path")
    verify(SOURCE, SOURCE_SHA256)
    with TemporaryDirectory(dir=args.output.parent) as scratch:
        generated = Path(scratch).resolve() / args.output.name
        subprocess.run(
            [args.blender, "--background", "--disable-autoexec", str(SOURCE), "--threads", "1",
             "--python-exit-code", "1", "--python", str(HERE / "export_baked.py"), "--", str(generated)],
            check=True,
        )
        verify(generated, EXPORT_SHA256)
        with args.output.open("xb") as destination:
            destination.write(generated.read_bytes())
    print("Exact reviewed baked-source export verified.")


if __name__ == "__main__":
    main()
