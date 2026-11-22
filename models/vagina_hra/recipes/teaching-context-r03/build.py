"""Pack the seven exact HRA meshes used by the cervicovaginal locator."""
import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from glb import buffer_view_bytes, decode, encode, pack_buffer_view

CONTROL = ROOT / "models/vagina_hra/exports/context-r02/vagina_hra_same_atlas_context_r02.glb"
SHA256 = "c649de4db766ba00020315029c922de1d018061c1a34bd95c850a05255ab3037"
KEEP = {
    "VH_F_vagina", "VH_F_cervix", "VH_F_cervicovaginal_junction", "VH_F_rectum",
    "VH_F_fundus_of_urinary_bladder_dome", "VH_F_fundus_of_urinary_bladder_base",
    "VH_F_urinary_bladder_neck_smooth_muscle",
}


def select(data):
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Expected the hydrated, exact r02 pelvis")
    source, binary = decode(data)
    doc = deepcopy(source)
    for key in ("nodes", "meshes", "materials", "accessors", "bufferViews"):
        doc[key] = []
    doc["scenes"][doc["scene"]]["nodes"] = []
    packed = bytearray()
    maps = {"materials": {}, "accessors": {}, "bufferViews": {}}

    def add(key, index):
        if index not in maps[key]:
            payload = deepcopy(source[key][index])
            if key == "accessors":
                payload["bufferView"] = add("bufferViews", payload["bufferView"])
            if key == "bufferViews":
                payload = pack_buffer_view(packed, payload, buffer_view_bytes(binary, payload))
            maps[key][index] = len(doc[key])
            doc[key].append(payload)
        return maps[key][index]

    for index in source["scenes"][source["scene"]]["nodes"]:
        node = deepcopy(source["nodes"][index])
        if node["name"] not in KEEP:
            continue
        if node.get("children"):
            raise ValueError("Expected a flat source node")
        mesh = deepcopy(source["meshes"][node["mesh"]])
        (part,) = mesh["primitives"]
        part["material"] = add("materials", part["material"])
        part["indices"] = add("accessors", part["indices"])
        part["attributes"] = {name: add("accessors", accessor)
                              for name, accessor in part["attributes"].items()}
        node["mesh"] = len(doc["meshes"])
        doc["scenes"][doc["scene"]]["nodes"].append(len(doc["nodes"]))
        doc["nodes"].append(node)
        doc["meshes"].append(mesh)
    if {node["name"] for node in doc["nodes"]} != KEEP or len(doc["nodes"]) != len(KEEP):
        raise ValueError("Missing or duplicated teaching mesh")
    doc["asset"].setdefault("extras", {})["teachingSelection"] = (
        "Exact r02 source-frame meshes. Seven parts retained for the external cervix–vagina relationship.")
    doc["buffers"][0]["byteLength"] = len(packed)
    return encode(doc, packed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = select(CONTROL.read_bytes())
    with args.output.open("xb") as stream:
        stream.write(result)
    print(hashlib.sha256(result).hexdigest(), len(result), args.output)


if __name__ == "__main__":
    main()
