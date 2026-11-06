"""Pinned source inventory and laterality for the private arch locator study."""
import hashlib
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.glb import decode as decode_glb

MODEL_PATH = "models/aortic_tree_z/exports/r02/aortic_tree_z_source_frame.glb"
MODEL_SHA = "d4b3dbd2d09fd76795f47bb96844acdeba5f1b4f48dd630f2a294f33816deaeb"
MODEL_BYTES = 881168
GROUPS = [
    {"number": 1, "node": "Brachiocephalic trunk + Right common carotid artery",
     "en": "Brachiocephalic trunk + right common carotid artery", "zh": "头臂干＋右颈总动脉",
     "sourceNames": ["Brachiocephalic trunk", "Right common carotid artery"],
     "targetSourceM": [0.001, 1.400, 0.018]},
    {"number": 2, "node": "Left common carotid artery.001",
     "en": "Left common carotid artery", "zh": "左颈总动脉",
     "sourceNames": ["Left common carotid artery"], "targetSourceM": [0.018, 1.425, 0.009]},
    {"number": 3, "node": "Left subclavian artery.001",
     "en": "Left subclavian artery", "zh": "左锁骨下动脉",
     "sourceNames": ["Left subclavian artery"], "targetSourceM": [0.044, 1.421, 0.002]},
    {"number": 4, "node": "Right subclavian artery.001",
     "en": "Right subclavian artery", "zh": "右锁骨下动脉",
     "sourceNames": ["Right subclavian artery"], "targetSourceM": [-0.044, 1.420, 0.007]},
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(raw, verify_identity=True):
    if verify_identity:
        require(len(raw) == MODEL_BYTES and sha(raw) == MODEL_SHA, 'Source GLB identity mismatch')
    return decode_glb(raw)


def positions(doc, binary, mesh):
    prim = doc["meshes"][mesh]["primitives"]
    require(len(prim) == 1, "Expected one retained primitive")
    accessor = doc["accessors"][prim[0]["attributes"]["POSITION"]]
    require(accessor["componentType"] == 5126 and accessor["type"] == "VEC3" and "sparse" not in accessor,
            "Unsupported position encoding")
    view = doc["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", 12)
    return [struct.unpack_from("<fff", binary, start + i * stride) for i in range(accessor["count"])]


def inventory(raw):
    doc, binary = decode(raw)
    require(len(doc["meshes"]) == len(doc["nodes"]) == 9, "Expected all nine source meshes/nodes")
    require(doc["scenes"][0]["nodes"] == list(range(9)), "Source scene membership changed")
    rows = []
    for i, node in enumerate(doc["nodes"]):
        require(not any(k in node for k in ("matrix", "translation", "rotation", "scale", "children")),
                "Expected baked source-native coordinates without node transforms")
        ps = positions(doc, binary, node["mesh"])
        prim = doc["meshes"][node["mesh"]]["primitives"][0]
        rows.append({"nodeIndex": i, "meshIndex": node["mesh"], "nodeName": node["name"],
            "sourceNames": node["extras"]["source_component_names"], "vertices": len(ps),
            "triangles": doc["accessors"][prim["indices"]]["count"] // 3,
            "minimumSourceM": [min(p[a] for p in ps) for a in range(3)],
            "maximumSourceM": [max(p[a] for p in ps) for a in range(3)],
            "meanSourceM": [sum(p[a] for p in ps) / len(ps) for a in range(3)]})
    require(sum(len(r["sourceNames"]) for r in rows) == 15, "Expected 15 named source structures")
    by_name = {r["nodeName"]: r for r in rows}
    for group in GROUPS:
        require(by_name[group["node"]]["sourceNames"] == group["sourceNames"], "Callout source names changed")
    checks = []
    for left, right in [("Left subclavian artery.001", "Right subclavian artery.001"),
                        ("Left renal artery.001", "Right renal artery.001"),
                        ("Common iliac artery.l + External iliac artery.l", "Common iliac artery.r + External iliac artery.r")]:
        lx, rx = by_name[left]["meanSourceM"][0], by_name[right]["meanSourceM"][0]
        require(rx < 0 < lx, "Source-labeled laterality is inconsistent")
        checks.append({"leftNode": left, "rightNode": right, "leftMeanX": lx, "rightMeanX": rx})
    return {"file": MODEL_PATH, "sha256": sha(raw), "bytes": len(raw), "binaryChunkSha256": sha(binary),
        "meshCount": 9, "sourceStructureCount": 15, "nodes": rows, "groups": GROUPS,
        "laterality": {"basis": "Source-name checks on three bilateral pairs: +X is source left, -X source right.",
                       "bilateralChecks": checks}}
