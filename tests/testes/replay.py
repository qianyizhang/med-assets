"""Scoped deterministic build, source-export and failure-path checks.

Usage: python3 tests/testes/replay.py --source /path/Startup.blend --out NEW_DIR
Requires Blender 4.3.2; does not render or publish. Images are reviewed separately.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender", default="blender")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    recipe = root / "models/testes/source/z-native-epididymis-r01"
    results = []

    def run(name, script, arguments, expected_error=None):
        start = time.monotonic()
        process = subprocess.run([args.blender, "-b", "--factory-startup", "--python-exit-code", "1",
                                  "--python", str(recipe / script), "--", *map(str, arguments)],
                                 capture_output=True, text=True)
        log = process.stdout + process.stderr
        (args.out / (name + ".log")).write_text(log)
        passed = (process.returncode == 0 if expected_error is None
                  else process.returncode != 0 and expected_error in log)
        results.append({"check": name, "passed": passed, "exit_code": process.returncode,
                        "elapsed_seconds": round(time.monotonic() - start, 3)})
        if not passed:
            raise RuntimeError(f"{name} failed; inspect its local log")

    for name in ("first", "replay"):
        run(name, "build.py", ["--source", args.source, "--out", args.out / name])
    first = args.out / "first/testicular-region.glb"
    replay = args.out / "replay/testicular-region.glb"
    identical = first.read_bytes() == replay.read_bytes()
    results.append({"check": "byte-identical-replay", "passed": identical})
    if not identical:
        raise AssertionError("Rebuild changed GLB bytes")
    run("source-export", "verify.py", ["--source", args.source, "--artifact", first,
                                      "--out", args.out / "source-export.json"])
    invalid = args.out / "wrong-source.blend"
    invalid.write_bytes(b"Not the pinned source")
    run("reject-wrong-source", "build.py", ["--source", invalid, "--out", args.out / "must-not-exist"],
        "Pinned source hash mismatch")
    run("refuse-output-overwrite", "build.py", ["--source", args.source, "--out", args.out / "first"],
        "Output must be a new directory")
    import struct
    data = first.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    shape_ok = len(gltf["meshes"]) == 4 and not gltf.get("animations")
    shape_ok &= not (args.out / "must-not-exist").exists()
    results.append({"check": "four-static-meshes-no-failed-output", "passed": bool(shape_ok)})
    if not shape_ok:
        raise AssertionError("Export scope or failure output mismatch")
    receipt = {"passed": all(r["passed"] for r in results), "checks": results,
               "artifact_sha256": hashlib.sha256(data).hexdigest(), "artifact_bytes": len(data),
               "scope": "Build/rebuild, source equivalence, two expected failure paths and static export membership; no visual/runtime/anatomy assertions"}
    (args.out / "replay.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
