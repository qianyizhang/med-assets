"""Extract four exact tissue meshes from the pinned HRA lymph-node source GLB."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from tools.glb import decode, encode
from models.lymph_node.recipes.editorial_window_r03.gltf_source import accessor

ORIGIN = ROOT / "sources/datasets/hra/lymph-node-v1.2/source.json"
GEOMETRY = {"POSITION", "NORMAL", "COLOR_0"}
TRANSFORMS = ("matrix", "translation", "rotation", "scale")


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def source_accessor(doc, binary, index):
    a = doc["accessors"][index]
    v = doc["bufferViews"][a["bufferView"]]
    element = {5123: 2, 5125: 4, 5126: 4}[a["componentType"]] * {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    if a.get("sparse") or v["buffer"] != 0 or v.get("byteStride", element) != element:
        raise ValueError("Unsupported accessor storage in the pinned source")
    offset = a.get("byteOffset", 0)
    length = a["count"] * element
    start = v.get("byteOffset", 0) + offset
    if offset < 0 or offset + length > v["byteLength"] or start + length > len(binary):
        raise ValueError("Accessor extends outside its source buffer view")
    return binary[start:start + length]


def load_inputs(path, origin, selection):
    data = path.read_bytes()
    if identity(data) != {k: origin[k] for k in ("sha256", "bytes")}:
        raise ValueError("Wrong HRA source identity")
    doc, binary = decode(data)
    expected_top = {"asset", "scene", "scenes", "nodes", "meshes", "accessors", "bufferViews", "buffers", "materials"}
    if set(doc) != expected_top or len(doc["buffers"]) != 1 or "uri" in doc["buffers"][0]:
        raise ValueError("Expected the declared standalone HRA GLB structure")
    names = {n["name"] for n in doc["nodes"] if "mesh" in n}
    retained, omitted = (set(selection[k]) for k in ("retained", "omitted"))
    if len(names) != 7 or len(retained) != 4 or retained & omitted or names != retained | omitted:
        raise ValueError("The fixed selection and omission names must cover the exact source")
    return doc, binary


def build(source, binary, origin, selection):
    doc = {k: deepcopy(source[k]) for k in ("asset", "scene", "scenes", "buffers")}
    doc.update({k: [] for k in ("nodes", "meshes", "materials", "accessors", "bufferViews")})
    doc["asset"]["extras"] = {
        "title": "HRA lymph node tissue layers",
        "source": origin["doi"],
        "source_sha256": origin["sha256"],
        "credit": "Kristen Browne and Heidi Schlehlein, HRA 3D Reference Organ for Lymph Node, Male v1.2 (2022)",
        "license": origin["licenseUrl"],
        "changes": "Tissue selection only. Source vessel structures and the disputed network are omitted.",
    }

    (scene_root,) = source["scenes"][source["scene"]]["nodes"]
    root = deepcopy(source["nodes"][scene_root])
    doc["nodes"].append(root)
    doc["scenes"][source["scene"]]["nodes"] = [0]
    parts = root["children"]
    root["children"] = []
    packed = bytearray()
    material_map = {}

    def add_accessor(index):
        payload = source_accessor(source, binary, index)
        packed.extend(b"\0" * (-len(packed) % 4))
        index_out = len(doc["accessors"])
        node = deepcopy(source["accessors"][index])
        node.pop("byteOffset", None)
        node["bufferView"] = len(doc["bufferViews"])
        doc["accessors"].append(node)
        doc["bufferViews"].append({"buffer": 0, "byteOffset": len(packed), "byteLength": len(payload)})
        packed.extend(payload)
        return index_out

    for index in parts:
        node = deepcopy(source["nodes"][index])
        if node["name"] not in selection["retained"]:
            continue
        mesh = deepcopy(source["meshes"][node["mesh"]])
        (primitive,) = mesh["primitives"]
        if set(primitive["attributes"]) != GEOMETRY or "children" in node:
            raise ValueError("Expected the declared flat named tissue mesh")
        primitive["indices"] = add_accessor(primitive["indices"])
        primitive["attributes"] = {semantic: add_accessor(i) for semantic, i in primitive["attributes"].items()}
        material = primitive["material"]
        if material not in material_map:
            material_map[material] = len(doc["materials"])
            doc["materials"].append(deepcopy(source["materials"][material]))
        primitive["material"] = material_map[material]
        node["mesh"] = len(doc["meshes"])
        root["children"].append(len(doc["nodes"]))
        doc["nodes"].append(node)
        doc["meshes"].append(mesh)

    doc["buffers"][0]["byteLength"] = len(packed)
    return encode(doc, packed)


def audit(source, source_bin, candidate_data, selection):
    """Decode both accessor streams and check parent, node, mesh and material links."""
    candidate, candidate_bin = decode(candidate_data)
    parents = {}
    for label, doc in (("source", source), ("candidate", candidate)):
        (parent_id,) = doc["scenes"][doc["scene"]]["nodes"]
        parent = doc["nodes"][parent_id]
        parents[label] = {k: v for k, v in parent.items() if k != "children"}
    if parents["source"] != parents["candidate"]:
        raise ValueError("Source frame parent changed")
    scratch = ("source", "candidate")
    nodes = ({n["name"]: n for n in doc["nodes"] if "mesh" in n} for doc in (source, candidate))
    before, after = nodes
    if set(after) != set(selection["retained"]) or not set(selection["omitted"]).isdisjoint(after):
        raise ValueError("The candidate contains the wrong tissue or vessel nodes")
    if len(candidate["nodes"]) != len(after) + 1 or len(candidate["meshes"]) != len(after):
        raise ValueError("Unexpected unreferenced mesh or node")
    sources = dict(zip(scratch, (source, candidate), strict=True))
    originals = dict(zip(scratch, (before, after), strict=True))
    for label, doc in sources.items():
        (root,) = doc["scenes"][doc["scene"]]["nodes"]
        if {doc["nodes"][i]["name"] for i in doc["nodes"][root]["children"]} != set(originals[label]):
            raise ValueError(f"Scene children do not match declared meshes: {label}")
    report = {}
    for name in after:
        prior, updated = (source_label[name] for source_label in (before, after))
        if {k: v for k, v in prior.items() if k != "mesh"} != {k: v for k, v in updated.items() if k != "mesh"}:
            raise ValueError(f"Source transform or provider node properties changed: {name}")
        mesh_a = source["meshes"][prior["mesh"]]
        mesh_b = candidate["meshes"][updated["mesh"]]
        (a,), (b,) = mesh_a["primitives"], mesh_b["primitives"]
        if mesh_a["name"] != mesh_b["name"] or a.get("mode", 4) != 4 or b.get("mode", 4) != 4:
            raise ValueError(f"Mesh identity or triangle primitive changed: {name}")
        material_a = source["materials"][a["material"]]
        material_b = candidate["materials"][b["material"]]
        if material_a != material_b:
            raise ValueError(f"Source material changed: {name}")
        semantics = {"indices": a["indices"], **a["attributes"]}
        outputs = {"indices": b["indices"], **b["attributes"]}
        if semantics.keys() != outputs.keys():
            raise ValueError(f"Accessor semantics changed: {name}")
        matched = {}
        for key, i in semantics.items():
            j = outputs[key]
            source_bytes = source_accessor(source, source_bin, i)
            updated_bytes = source_accessor(candidate, candidate_bin, j)
            if source_bytes != updated_bytes or accessor(source, source_bin, i) != accessor(candidate, candidate_bin, j):
                raise ValueError(f"Source {key} data changed: {name}")
            matched[key] = identity(updated_bytes)
        report[name] = {
            "label": selection["retained"][name],
            "providerOntology": updated["extras"]["ontologyid"],
            "triangles": candidate["accessors"][b["indices"]]["count"] // 3,
            "material": material_b["name"],
            "transforms": {k: updated[k] for k in TRANSFORMS if k in updated},
            "identicalDecodedAccessors": matched,
        }
    return report


def write_fresh(path, data):
    with tempfile.TemporaryDirectory(dir=path.parent) as folder:
        staged = Path(folder) / path.name
        staged.write_bytes(data)
        os.link(staged, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate an existing file without writing it")
    args = parser.parse_args()
    origin = json.loads(ORIGIN.read_text())
    selection = json.loads((HERE / "selection.json").read_text())
    source_path = args.source or ROOT / origin["canonicalPayload"]
    source, binary = load_inputs(source_path, origin, selection)
    candidate = build(source, binary, origin, selection)
    if args.check and args.output.read_bytes() != candidate:
        raise ValueError("Existing candidate differs from the exact replay")
    parts = audit(source, binary, candidate, selection)
    record = {
        "source": {"path": origin["canonicalPayload"], "sha256": origin["sha256"], "bytes": origin["bytes"]},
        "candidate": {"name": args.output.name, **identity(candidate)},
        "sourceTriangles": sum(source["accessors"][m["primitives"][0]["indices"]]["count"] // 3 for m in source["meshes"]),
        "retainedTriangles": sum(part["triangles"] for part in parts.values()),
        "verifiedRetained": parts,
        "intentionalOmissions": selection["omitted"],
    }
    if not args.check:
        write_fresh(args.output, candidate)
    receipt = (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode()
    if args.report:
        write_fresh(args.report, receipt)
    else:
        print(receipt.decode(), end="")


if __name__ == "__main__":
    main()
