"""Check actual retained bytes and crown-ray identities; no render or anatomy claim.

Run from any directory: python3 .../verify_sources.py [--output receipt.json]
Requires Node for reading the same locator constants used by the UI; otherwise stdlib.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT = ROOT / "reviews/teeth_gums/2026-10-26-set-contact-checkpoint"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accessor(doc, binary, index):
    item = doc["accessors"][index]
    view = doc["bufferViews"][item["bufferView"]]
    count = {"SCALAR": 1, "VEC3": 3}[item["type"]]
    code = {5123: "H", 5125: "I", 5126: "f"}[item["componentType"]]
    fmt = "<" + code * count
    start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", struct.calcsize(fmt))
    return [struct.unpack_from(fmt, binary, start + i * stride) for i in range(item["count"])]


def projected(point, view):
    x, y, z = point
    blender = [x, -z, y]
    delta = [v - t for v, t in zip(blender, view["target_blender_m"])]
    scale = 1000 / view["orthographic_vertical_span_m"]
    dot = lambda a, b: sum(v * w for v, w in zip(a, b))
    direction = [t - c for t, c in zip(view["target_blender_m"], view["camera_position_blender_m"])]
    norm = math.sqrt(dot(direction, direction))
    return (550 + scale * dot(delta, view["screen_right_blender"]),
            500 - scale * dot(delta, view["screen_up_blender"]),
            dot([v - c for v, c in zip(blender, view["camera_position_blender_m"])], direction) / norm)


def ray_hit(point, mesh):
    x, y = point
    found = []
    vertices, triangles = mesh
    for i in range(0, len(triangles), 3):
        a, b, c = (vertices[triangles[i + j]] for j in range(3))
        denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(denominator) < 1e-10:
            continue
        u = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / denominator
        v = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / denominator
        w = 1 - u - v
        if min(u, v, w) >= -1e-8:
            depth = u * a[2] + v * b[2] + w * c[2]
            if depth > 0:
                found.append((depth, i // 3))
    return min(found) if found else None


def verify():
    triangle = ([(0, 0, 1), (1, 0, 1), (0, 1, 1)], [0, 1, 2])
    assert ray_hit((.2, .2), triangle) == (1.0, 0)
    assert ray_hit((2, 2), triangle) is None
    assert ray_hit((.2, .2), (triangle[0], [2, 1, 0])) == (1.0, 0)
    assert ray_hit((.2, .2), ([(0, 0, 1), (0, 0, 1), (0, 0, 1)], [0, 1, 2])) is None
    coverage = read(ROOT / "docs/dental-atlas/set-coverage.json")
    sources = read(ROOT / "sources/datasets/bp3d-4.0-head-studies/external-source-map.json")["members"]
    manifest = read(CHECKPOINT / "manifest.json")
    identities = {f["path"]: f for f in manifest["files"]}
    # Bind all review inputs used here to their original retained receipt.
    for name in ["render-bindings.json", "identity-frame-check.json"]:
        assert sha(CHECKPOINT / name) == identities[name]["sha256"], name
    bindings = read(CHECKPOINT / "render-bindings.json")
    model = ROOT / coverage["bp3d_evidence"]["canonical_path"]
    assert sha(model) == coverage["bp3d_evidence"]["glb_sha256"] == manifest["source_glb_sha256"]
    raw = model.read_bytes()
    magic, version, length = struct.unpack_from("<III", raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw)
    json_len = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + json_len])
    binary = raw[28 + json_len:]
    assert len(doc["nodes"]) == 30 and len(doc["meshes"]) == 30
    nodes = {n["extras"]["source_file_id"]: n for n in doc["nodes"]}
    for node in doc["nodes"]:
        assert not any(k in node for k in ["matrix", "translation", "rotation", "scale"]), node["name"]
    plate = ROOT / "lessons/arch-identification/plate.mjs"
    locators = json.loads(subprocess.check_output(["node", "--input-type=module", "-e",
        f"import {{PLACEMENTS}} from {json.dumps(plate.as_uri())}; console.log(JSON.stringify(PLACEMENTS));"], text=True))
    teeth = {t["fdi"]: t for t in coverage["teeth"] if t["bp3d"]}
    assert set(teeth) == set(locators["upper"]) | set(locators["lower"]) and len(teeth) == 28
    for fdi in ["18", "28", "38", "48"]:
        assert next(t for t in coverage["teeth"] if t["fdi"] == fdi)["bp3d"] is None
    result = {"scope": "Retained-byte identity, source-label/FDI/camera consistency, nearest visible triangle at 28 editorial crown endpoints. Not clinical crown segmentation or anatomy approval.",
              "model": {"file": str(model.relative_to(ROOT)), "sha256": sha(model), "bytes": len(raw)},
              "ray_controls_passed": 4, "images": [], "leader_hits": [], "max_object_center_error_px": 0}
    classes = ["central secondary incisor", "lateral secondary incisor", "secondary canine", "first secondary premolar", "second secondary premolar", "first secondary molar", "second secondary molar"]
    for arch in ["upper", "lower"]:
        filename = arch + "-occlusal-teeth.png"
        view = next(v for v in bindings["views"] if v["file"] == filename)
        image = CHECKPOINT / "media" / filename
        assert sha(image) == identities["media/" + filename]["sha256"]
        assert struct.unpack_from(">II", image.read_bytes(), 16) == (1100, 1000)
        assert view["screen_right_blender"] == ([1.0, 0.0, 0.0] if arch == "upper" else [-1.0, 0.0, 0.0])
        assert view["glb_sha256"] == result["model"]["sha256"] and not view["gingiva_visible"]
        result["images"].append({"file": str(image.relative_to(ROOT)), "sha256": sha(image), "bytes": image.stat().st_size})
        center_receipt = {p["source_id"]: p["pixel"] for p in view["object_center_label_projections"]}
        meshes = {}
        for fdi in locators[arch]:
            tooth = teeth[fdi]["bp3d"]
            sid = tooth["source_object"]
            node = nodes[sid]
            expected_side = "Right" if fdi[0] in "14" else "Left"
            expected_name = f"{expected_side} {arch} {classes[int(fdi[1]) - 1]} tooth"
            assert tooth["source_name"] == node["extras"]["source_name"] == sources[sid]["identity"]["English name"] == expected_name
            assert tooth["source_mesh_sha256"] == node["extras"]["source_sha256"] == sources[sid]["sha256"]
            primitives = doc["meshes"][node["mesh"]]["primitives"]
            assert len(primitives) == 1
            primitive = primitives[0]
            verts = accessor(doc, binary, primitive["attributes"]["POSITION"])
            indices = [v[0] for v in accessor(doc, binary, primitive["indices"])]
            meshes[sid] = ([projected(p, view) for p in verts], indices)
            center = [(min(p[i] for p in verts) + max(p[i] for p in verts)) / 2 for i in range(3)]
            projected_center = projected(center, view)
            error = math.dist(projected_center[:2], center_receipt[sid])
            assert error < .02, (fdi, "receipt camera does not reproduce object center", error)
            result["max_object_center_error_px"] = max(result["max_object_center_error_px"], error)
        assert set(meshes) == set(view["selected_source_ids"]) == set(center_receipt)
        for fdi, coords in locators[arch].items():
            hits = [(hit[0], sid, hit[1]) for sid, mesh in meshes.items() if (hit := ray_hit(coords[:2], mesh))]
            assert hits, (fdi, "endpoint misses visible geometry")
            depth, sid, triangle = min(hits)
            assert sid == teeth[fdi]["bp3d"]["source_object"], (fdi, sid, "wrong front-most object")
            result["leader_hits"].append({"fdi": fdi, "source": sid, "triangle": triangle})
    result["max_object_center_error_px"] = round(result["max_object_center_error_px"], 8)
    result["ids_checked"] = len(result["leader_hits"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["ids_checked", "max_object_center_error_px", "model", "images"]}, indent=2))
