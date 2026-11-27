"""Replay the pinned r01 liver surface using the existing ultrasound mesher."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LFS_HEADER = b"version https://git-lfs.github.com/spec/v1\n"


def _is_matching_lfs_pointer(data: bytes, digest: str, size: int) -> bool:
    if not data.startswith(LFS_HEADER):
        return False
    fields: dict[str, str] = {}
    for line in data.decode("utf-8", errors="ignore").splitlines():
        if " " in line:
            key, value = line.split(" ", 1)
            fields[key.strip()] = value.strip()
    return fields.get("oid") == f"sha256:{digest}" and fields.get("size") == str(size)


def place_verified_output(candidate: Path, destination: Path, raw: bytes, digest: str) -> None:
    """Install verified bytes at destination, replacing only a matching LFS pointer."""
    try:
        os.link(candidate, destination)
    except FileExistsError:
        existing = destination.read_bytes()
        if existing == raw:
            return
        if _is_matching_lfs_pointer(existing, digest, len(raw)):
            os.replace(candidate, destination)
            return
        raise ValueError(
            f"Existing output differs: {destination}. Choose --output in a fresh directory."
        ) from None


def main() -> None:
    owner = Path(__file__).resolve().parent
    repo = owner.parents[1]
    record = json.loads((owner / "asset.record.json").read_text())
    revision = next(row for row in record["revisions"] if row["revisionId"] == "r01")
    export = next(row for row in revision["exports"] if row["id"] == "liver")
    builder = repo / "experiments/ultrasound-sweep/build_abdomen.py"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=os.environ.get("S1233_CASE"))
    parser.add_argument("--output", type=Path, default=repo / export["path"])
    args = parser.parse_args()
    if args.case is None:
        parser.error("Supply --case or set S1233_CASE to the pinned case directory")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temp:
        candidate = Path(temp) / "liver.mesh"
        subprocess.run(
            [sys.executable, str(builder), str(args.case), "--export-liver", str(candidate)],
            check=True,
        )
        raw = candidate.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) != export["bytes"] or digest != export["sha256"]:
            parser.exit(1, f"Liver replay differs from r01: SHA-256 {digest}, {len(raw)} bytes\n")
        try:
            place_verified_output(candidate, args.output, raw, digest)
        except ValueError as exc:
            parser.exit(1, f"{exc}\n")
    print(f"Verified r01 liver surface: {digest}, {len(raw)} bytes")


if __name__ == "__main__":
    main()
