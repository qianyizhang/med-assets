"""Rebuild six full-scene teaching editions from their exact hydrated controls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))
from tools.glb import decode
from med_assets.glb_repack import compact_normals, compact_png


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


from med_assets.glb_repack import compact_normals, compact_png

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    folder = args.destination.resolve()
    if not folder.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh scratch output under .artifacts")
    folder.mkdir(parents=True, exist_ok=False)
    receipts = {}
    for name, settings in json.loads((HERE / "editions.json").read_text()).items():
        source = (ROOT / settings["path"]).read_bytes()
        if identity(source)["sha256"] != settings["sha256"]:
            raise ValueError(f"Incorrect or unhydrated source for {name}")
        if name == "stomach":
            data, textures = compact_png(source)
            result = {"textures": textures}
        else:
            data, result = compact_normals(source)
        target = folder / name / Path(settings["output"]).name
        target.parent.mkdir()
        target.write_bytes(data)
        doc, _ = decode(data)
        parts = []
        for mesh in doc["meshes"]:
            parts.append({"mesh": mesh["name"], "triangles": sum(
                doc["accessors"][p["indices"]]["count"] // 3 for p in mesh["primitives"]),
                "primitives": len(mesh["primitives"])})
        receipts[name] = {"control": {"path": settings["path"], **identity(source)},
                          "edition": {"path": settings["output"], **identity(data)},
                          "bytesSaved": len(source) - len(data), "meshCount": len(parts),
                          "primitives": sum(r["primitives"] for r in parts),
                          "triangles": sum(r["triangles"] for r in parts), **result}
    (folder / "measurements.json").write_text(json.dumps(receipts, indent=2) + "\n")


if __name__ == "__main__":
    main()
