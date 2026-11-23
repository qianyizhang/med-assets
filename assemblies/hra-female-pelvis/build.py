"""Export the bladder and cervicovaginal locators from shared native HRA geometry."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
from med_assets.glb import buffer_view_bytes, decode, encode, pack_buffer_view
from med_assets.glb_selection import select

STYLE = ROOT / 'models/vagina_hra/exports/context-r02/vagina_hra_same_atlas_context_r02.glb'
SHA256 = 'c649de4db766ba00020315029c922de1d018061c1a34bd95c850a05255ab3037'
VAGINA_FILE = 'vagina_teaching_context.glb'
KEEP = {
    'VH_F_vagina', 'VH_F_cervix', 'VH_F_cervicovaginal_junction', 'VH_F_rectum',
    'VH_F_fundus_of_urinary_bladder_dome', 'VH_F_fundus_of_urinary_bladder_base',
    'VH_F_urinary_bladder_neck_smooth_muscle',
}


def require_frame(document):
    if any({'translation', 'rotation', 'scale', 'matrix'} & node.keys() for node in document['nodes']):
        raise ValueError('Expected identity transforms in the shared atlas frame')


def vagina_selection(data, master):
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Expected the hydrated, exact r02 pelvis")
    source, binary = decode(data)
    geometry, geometry_binary = decode(master)
    require_frame(geometry)
    require_frame(source)
    masters = {node["name"]: geometry["meshes"][node["mesh"]]["primitives"][0]
               for node in geometry["nodes"] if "mesh" in node}
    doc = deepcopy(source)
    for key in ("nodes", "meshes", "materials", "accessors", "bufferViews"):
        doc[key] = []
    doc["scenes"][doc["scene"]]["nodes"] = []
    packed = bytearray()
    maps = {"materials": {}, "accessors": {}, "bufferViews": {}}

    def add(key, index, shared=None):
        if index not in maps[key]:
            payload = deepcopy(source[key][index])
            if key == "accessors":
                if shared is not None:
                    master_accessor = geometry['accessors'][shared]
                    layout = ('type', 'componentType', 'count', 'byteOffset', 'normalized')
                    if any(payload.get(field) != master_accessor.get(field) for field in layout):
                        raise ValueError('Shared pelvic geometry does not match the reviewed style layout')
                    if payload['type'] == 'VEC3':
                        for limit in ('min', 'max'):
                            # R02 writes shorter decimal bounds for the same f32 buffers.
                            values = master_accessor[limit]
                            if any(abs(a - b) > 1e-8 for a, b in zip(payload[limit], values)):
                                payload[limit] = values
                payload['bufferView'] = add('bufferViews', payload['bufferView'],
                                            master_accessor['bufferView'] if shared is not None else None)
            if key == "bufferViews":
                data = (buffer_view_bytes(binary, payload) if shared is None else
                        buffer_view_bytes(geometry_binary, geometry['bufferViews'][shared]))
                if len(data) != payload['byteLength']:
                    raise ValueError('Shared pelvic geometry has a different buffer span')
                payload = pack_buffer_view(packed, payload, data)
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
        master_part = masters[node["name"]]
        part["material"] = add("materials", part["material"])
        part["indices"] = add("accessors", part["indices"], master_part["indices"])
        part["attributes"] = {name: add("accessors", accessor, master_part["attributes"][name] if name == "POSITION" else None)
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



def build(master, style, bladder):
    """Return the two verified selections without writing either destination."""
    bladder_delivery, _ = select(master, bladder)
    return {bladder['file']: bladder_delivery, VAGINA_FILE: vagina_selection(style, master)}


def read_bladder_selection():
    return json.loads((HERE / 'bladder-selection.json').read_text())


def read_inputs():
    bladder = read_bladder_selection()
    return (ROOT / bladder['source']).read_bytes(), STYLE.read_bytes(), bladder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Fresh output directory')
    args = parser.parse_args()
    outputs = build(*read_inputs())
    args.output.mkdir()
    for name, data in outputs.items():
        path = args.output / name
        path.write_bytes(data)
        print(hashlib.sha256(data).hexdigest(), len(data), path)


if __name__ == '__main__':
    main()
