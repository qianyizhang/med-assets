"""Rebuild six full-scene teaching editions from their exact hydrated controls."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import buffer_view_bytes, decode, encode, pack_buffer_view


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def compact_normals(source):
    doc, original = decode(source)
    result = deepcopy(doc)
    attr_views = Counter(a.get("bufferView") for a in doc["accessors"])
    normals = {}
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            index = primitive["attributes"]["NORMAL"]
            accessor = doc["accessors"][index]
            view = accessor["bufferView"]
            if (attr_views[view] != 1 or accessor["componentType"] != 5126 or
                    accessor["type"] != "VEC3" or set(accessor) - {"type", "componentType", "count", "bufferView", "name"}):
                raise ValueError(f"Unsupported normal accessor for {mesh['name']}")
            normals[view] = index, mesh["name"]
    if "extensionsRequired" in doc or "extensionsUsed" in doc:
        raise ValueError("Unexpected existing extension")
    result["extensionsUsed"] = result["extensionsRequired"] = ["KHR_mesh_quantization"]
    payload = bytearray()
    for i, view in enumerate(doc["bufferViews"]):
        data = buffer_view_bytes(original, view)
        new_view = dict(view)
        if i in normals:
            index, _ = normals[i]
            accessor = result["accessors"][index]
            if len(data) != 12 * accessor["count"] or view.get("byteStride", 12) != 12:
                raise ValueError("Unsupported source normal packing")
            packed = bytearray()
            for xyz in struct.iter_unpack("<3f", data):
                if any(not math.isfinite(x) or abs(x) > 1.0001 for x in xyz):
                    raise ValueError("Invalid source normal")
                packed.extend(struct.pack("<3bx", *(round(x * 127) for x in xyz)))
            data = bytes(packed)
            accessor.update(componentType=5120, normalized=True)
            new_view.update(byteStride=4, target=34962)
        result["bufferViews"][i] = pack_buffer_view(payload, new_view, data)
    result["buffers"][0]["byteLength"] = len(payload)
    encoded = encode(result, payload)

    # Decode the actual exported normal streams, including their padding and sign.
    checked, binary = decode(encoded)
    angles = []
    zero_count = 0
    vertex_count = 0
    for i, before in enumerate(doc["bufferViews"]):
        after = checked["bufferViews"][i]
        left = buffer_view_bytes(original, before)
        right = buffer_view_bytes(binary, after)
        if i not in normals:
            if left != right:
                raise ValueError(f"Original geometry or support data changed in view {i}")
            continue
        index, name = normals[i]
        if (checked["accessors"][index]["componentType"] != 5120 or
                checked["accessors"][index].get("normalized") is not True or after["byteStride"] != 4):
            raise ValueError("Incorrect decoded normal declaration")
        worst_angle = 0.
        for a, b in zip(struct.iter_unpack("<3f", left), struct.iter_unpack("<3bx", right), strict=True):
            vertex_count += 1
            if a == (0., 0., 0.) and b == (0, 0, 0):
                zero_count += 1
                continue
            length = math.hypot(*a) * math.hypot(*b)
            if not length:
                raise ValueError("A normal vanished during packing")
            cosine = sum(x * y for x, y in zip(a, b)) / length
            worst_angle = max(worst_angle, math.degrees(math.acos(max(-1., min(1., cosine)))))
        angles.append((worst_angle, name))
    if max(angles)[0] > .4 or len(encoded) >= len(source):
        raise ValueError("Angular error or size limit exceeded")
    return encoded, {"normalCount": vertex_count, "sourceZeroNormalsRetained": zero_count,
                     "maxNormalDegrees": round(max(angles)[0], 6), "worstMesh": max(angles)[1],
                     "exactNonNormalViews": len(doc["bufferViews"]) - len(normals)}


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
            repack = runpy.run_path(str(HERE.parent / "target-economy/lung-textures.py"))["repack"]
            data, textures = repack(source)
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
