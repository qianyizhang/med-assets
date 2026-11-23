"""Project tightly packed static GLB scenes and verify every retained stream."""

from copy import deepcopy

from .glb import decode, encode, pack_buffer_view

TOP_LEVEL = {"asset", "scene", "scenes", "nodes", "meshes", "accessors", "bufferViews",
             "buffers", "materials"}


def stream(doc, binary, accessor):
    """Read just the accessor's packed entries from a possibly shared buffer view."""
    if "sparse" in accessor or "bufferView" not in accessor:
        raise ValueError("Expected tightly bound static source streams")
    width = {5123: 2, 5125: 4, 5126: 4}[accessor["componentType"]]
    width *= {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    view = doc["bufferViews"][accessor["bufferView"]]
    offset = view.get("byteOffset", 0)
    start = offset + accessor.get("byteOffset", 0)
    end = start + accessor["count"] * width
    if (view["buffer"] != 0 or view.get("byteStride", width) != width
            or not 0 <= offset <= start <= end <= min(len(binary), offset + view["byteLength"])):
        raise ValueError("Unsupported stride or source stream outside its view")
    return binary[start:end]


def project(source, binary, excluded, scope, sha256):
    """Copy retained scene and accessor entries, remapping indices and binary ranges."""
    if set(source) != TOP_LEVEL or source["scene"] != 0 or len(source["scenes"]) != 1:
        raise ValueError("Expected the pinned single-scene static HRA format")
    if len(source["buffers"]) != 1 or "uri" in source["buffers"][0]:
        raise ValueError("Expected one embedded buffer")
    names = [node["name"] for node in source["nodes"]]
    for name in excluded:
        if names.count(name) != 1:
            raise ValueError(f"Unknown or ambiguous omission {name}")

    edition = {key: deepcopy(source[key]) for key in ("asset", "scene", "scenes", "buffers")}
    edition["asset"].setdefault("extras", {}).update(teachingScope=scope, teachingControlSha256=sha256)
    maps = {}
    for key in ("nodes", "meshes", "materials", "accessors"):
        edition[key] = []
        maps[key] = {}
    edition["bufferViews"] = []
    payload = bytearray()

    def add(key, prior, update):
        index_map = maps[key]
        if prior not in index_map:
            index_map[prior] = len(edition[key])
            edition[key].append(deepcopy(source[key][prior]))
            update(edition[key][-1])
        return index_map[prior]

    def copy_accessor(accessor):
        entries = stream(source, binary, accessor)
        view = source["bufferViews"][accessor["bufferView"]]
        accessor.pop("byteOffset", None)
        accessor["bufferView"] = len(edition["bufferViews"])
        edition["bufferViews"].append(pack_buffer_view(payload, view, entries))

    def copy_mesh(mesh):
        for part in mesh["primitives"]:
            if part.get("mode", 4) != 4 or set(part) - {"mode", "indices", "attributes", "material"}:
                raise ValueError("Expected ordinary indexed, untextured triangles")
            part["indices"] = add("accessors", part["indices"], copy_accessor)
            part["attributes"] = {name: add("accessors", idx, copy_accessor)
                                  for name, idx in part["attributes"].items()}
            part["material"] = add("materials", part["material"], lambda material: None)

    def copy_node(node):
        if "mesh" in node:
            node["mesh"] = add("meshes", node["mesh"], copy_mesh)
        if "children" in node:
            node["children"] = [add("nodes", child, copy_node) for child in node["children"]
                                if names[child] not in excluded]

    roots = source["scenes"][0]["nodes"]
    if any(names[idx] in excluded for idx in roots):
        raise ValueError("The original source frame root must be kept")
    edition["scenes"][0]["nodes"] = [add("nodes", idx, copy_node) for idx in roots]
    edition["buffers"][0]["byteLength"] = len(payload)
    return encode(edition, payload), maps


def verify(source, binary, output, maps):
    """Compare retained source declarations and raw buffer bytes after GLB decode."""
    doc, packed = decode(output)
    references = {
        "nodes": {"children": "nodes", "mesh": "meshes"},
        "meshes": {"indices": "accessors", "attributes": "accessors", "material": "materials"},
    }
    for key, mapping in maps.items():
        for prior, current in mapping.items():
            expected = deepcopy(source[key][prior])
            actual = deepcopy(doc[key][current])
            if key == "accessors":
                if stream(source, binary, expected) != stream(doc, packed, actual):
                    raise ValueError(f"Retained accessor {prior} bytes changed")
                for declaration in (expected, actual):
                    declaration.pop("bufferView")
                    declaration.pop("byteOffset", None)
            elif key == "nodes" and "children" in expected:
                expected["children"] = [i for i in expected["children"] if i in mapping]
            pairs = zip(expected["primitives"], actual["primitives"], strict=True) if key == "meshes" else [(expected, actual)]
            for left, right in pairs:
                for field, target in references.get(key, {}).items():
                    if field not in left:
                        continue
                    index_map = maps[target]
                    value = left[field]
                    if isinstance(value, list):
                        left[field] = [index_map[i] for i in value]
                    elif isinstance(value, dict):
                        left[field] = {name: index_map[i] for name, i in value.items()}
                    else:
                        left[field] = index_map[value]
            if expected != actual:
                raise ValueError(f"Retained {key}[{prior}] declaration changed")
    return doc


def count_triangles(doc):
    return sum(doc["accessors"][primitive["indices"]]["count"] // 3
               for mesh in doc["meshes"] for primitive in mesh["primitives"])
