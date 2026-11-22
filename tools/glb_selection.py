"""Export named glTF geometry with exact accessor bytes and source transforms."""
from copy import deepcopy
import hashlib

from tools.glb import buffer_view_bytes, decode, encode, pack_buffer_view


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def select(raw, spec):
    require(identity(raw)["sha256"] == spec["sha256"], "Expected exact hydrated selection input")
    doc, binary = decode(raw)
    supported = {"asset", "scene", "scenes", "nodes", "meshes", "materials", "animations",
                 "accessors", "bufferViews", "buffers"}
    require(set(doc) <= supported and len(doc["scenes"]) == 1 and len(doc["buffers"]) == 1
            and "uri" not in doc["buffers"][0], "Unexpected selection source dependencies")
    output = {"asset": deepcopy(doc["asset"]), "scene": 0, "scenes": [],
              "buffers": [{}], "extras": {"title": spec["title"], "scope": spec["scope"],
                                          "source": spec["source"], "sourceSha256": spec["sha256"]}}
    blob = bytearray()
    maps = {field: {} for field in ("materials", "meshes", "accessors", "bufferViews", "nodes")}
    for field in maps:
        output[field] = []

    def add(field, index):
        if index in maps[field]:
            return maps[field][index]
        entry = deepcopy(doc[field][index])
        if field == "bufferViews":
            entry = pack_buffer_view(blob, entry, buffer_view_bytes(binary, entry))
        if field == "accessors":
            if "bufferView" in entry:
                entry["bufferView"] = add("bufferViews", entry["bufferView"])
            if "sparse" in entry:
                for item in ("indices", "values"):
                    sparse = entry["sparse"][item]
                    sparse["bufferView"] = add("bufferViews", sparse["bufferView"])
        if field == "meshes":
            for part in entry["primitives"]:
                require(set(part) <= {"attributes", "indices", "material", "mode", "targets"},
                        "Unexpected mesh dependencies")
                part["indices"] = add("accessors", part["indices"])
                part["material"] = add("materials", part["material"])
                for bindings in (part["attributes"], *part.get("targets", [])):
                    for semantic, value in bindings.items():
                        bindings[semantic] = add("accessors", value)
        if field == "nodes":
            require(not any(k in entry for k in ("skin", "camera", "extensions")), "Unexpected node dependencies")
            if "mesh" in entry:
                require(entry["name"] in spec["retain"], "A retained ancestor has unselected geometry")
                entry["mesh"] = add("meshes", entry["mesh"])
            children = [add("nodes", i) for i in entry.pop("children", []) if i in retained]
            if children:
                entry["children"] = children
        if field == "materials":
            require(not any("texture" in key.lower() for key in entry) and
                    not any("texture" in key.lower() for key in entry.get("pbrMetallicRoughness", {})),
                    "Unexpected material texture binding")
        result = len(output[field])
        output[field].append(entry)
        maps[field][index] = result
        return result

    def retain(index):
        node = doc["nodes"][index]
        children = [retain(i) for i in node.get("children", [])]
        if node.get("name") in spec["retain"] or any(children):
            retained.add(index)
            return True
        return False

    retained = set()
    scene = deepcopy(doc["scenes"][0])
    roots = [i for i in scene["nodes"] if retain(i)]
    scene["nodes"] = [add("nodes", i) for i in roots]
    output["scenes"].append(scene)
    require(set(spec["retain"]) == {n["name"] for n in output["nodes"] if "mesh" in n}, "Selection mismatch")

    for animation in doc.get("animations", []):
        channels, samplers = [], []
        for channel in animation["channels"]:
            channel = deepcopy(channel)
            node = channel["target"]["node"]
            if node not in retained:
                continue
            channel["target"]["node"] = maps["nodes"][node]
            sampler = deepcopy(animation["samplers"][channel["sampler"]])
            for key in ("input", "output"):
                sampler[key] = add("accessors", sampler[key])
            channel["sampler"] = len(samplers)
            samplers.append(sampler)
            channels.append(channel)
        if channels:
            output.setdefault("animations", []).append({**animation, "channels": channels, "samplers": samplers})
    output["buffers"][0]["byteLength"] = len(blob)
    result = encode(output, blob)
    checked, checked_blob = decode(result)
    for old, new in maps["bufferViews"].items():
        a, b = doc["bufferViews"][old], checked["bufferViews"][new]
        require(buffer_view_bytes(binary, a) == buffer_view_bytes(checked_blob, b), "Retained bytes changed")

    def triangles(model):
        return sum(model["accessors"][p["indices"]]["count"] // 3
                   for mesh in model["meshes"] for p in mesh["primitives"])

    def channels(model):
        return sum(len(a["channels"]) for a in model.get("animations", []))

    return result, {
        "source": {"path": spec["source"], **identity(raw), "triangles": triangles(doc), "channels": channels(doc)},
        "candidate": {"file": spec["file"], **identity(result), "triangles": triangles(checked),
                      "channels": channels(checked)},
        "retained": spec["retain"],
        "retainedViewsIdentical": len(maps["bufferViews"]),
    }
