"""Audit exported endpoints and evidence bindings using decoded GLB positions."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode

ORDER = [
    "01 Right atrium", "02 Tricuspid valve - annulus", "03 Right ventricle",
    "04 Pulmonary valve - annulus", "05 Lung vascular bed - central", "07 Left atrium",
    "08 Mitral valve - annulus", "09 Left ventricle", "10 Aortic valve - annulus",
    "11 Systemic vascular bed - central",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(model_dir, evidence_dir):
    model = model_dir / "cardiovascular-loop.glb"
    doc, binary = decode(model.read_bytes())
    nodes = {n["name"]: n for n in doc["nodes"]}
    joins = json.loads((model_dir / "placement.json").read_text())["joins"]
    groups = defaultdict(list)

    def vertices(name):
        node = nodes[name]
        if any(k in node for k in ("matrix","rotation","scale","translation")):
            raise ValueError("Expected world-baked positions for "+name)
        prim, = doc["meshes"][node["mesh"]]["primitives"]
        a = doc["accessors"][prim["attributes"]["POSITION"]]
        v = doc["bufferViews"][a["bufferView"]]
        offset = v.get("byteOffset",0) + a.get("byteOffset",0)
        if a["componentType"] != 5126 or a["type"] != "VEC3":
            raise ValueError("Expected float VEC3")
        for i in range(a["count"]):
            x,z,minus_y = struct.unpack_from("<3f",binary,offset + i*v.get("byteStride",12))
            yield (x,-minus_y,z)

    worst = 0
    for join in joins:
        p = join["point_m"]
        edge = join["bridge"]
        host = join["host"]
        groups[edge].append(host)
        gap = min(math.dist(v,p) for v in vertices(edge))
        verts = list(vertices(host))
        if host.endswith("annulus"):
            # A vessel centre traverses the ring's aperture, not its tissue.
            mid = [(min(v[i] for v in verts)+max(v[i] for v in verts))/2 for i in range(3)]
            host_gap = math.dist(mid,p)
        else:
            host_gap = min(math.dist(v,p) for v in verts)
        worst = max(worst,gap,host_gap)
        host_tolerance = .0003 if host.endswith("annulus") else .000001
        if gap > .000001 or host_gap > host_tolerance:
            raise ValueError(f"{edge} to {host} missed by {max(gap,host_gap)*1000:g} mm")
    if list(groups.values()) != [[host, ORDER[(i+1)%len(ORDER)]] for i,host in enumerate(ORDER)]:
        raise ValueError("Disconnected or reordered circulation loop")
    for valve, count in (("Tricuspid",3),("Mitral",2),("Pulmonary",3),("Aortic",3)):
        if sum(valve+" valve - leaflet " in name for name in nodes) != count:
            raise ValueError("Missing source leaflet in "+valve)
    receipt = json.loads((evidence_dir/"renders.json").read_text())
    if receipt["sha256"] != digest(model) or receipt["viewsSha256"] != digest(Path(__file__).with_name("views.json")):
        raise ValueError("Evidence input mismatch")
    for view in receipt["views"]:
        for image in view["images"]:
            if digest(evidence_dir/image["file"]) != image["sha256"]:
                raise ValueError("Evidence image mismatch")
    print(f"{len(nodes)} nodes, {len(groups)} directed transitions, {len(joins)} endpoints, "
          f"maximum discrepancy {worst*1000:.6f} mm, all four valve leaflet counts and evidence hashes passed")


if __name__ == "__main__":
    check(Path(sys.argv[1]),Path(sys.argv[2]))
