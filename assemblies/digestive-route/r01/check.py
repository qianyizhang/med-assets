"""Verify shared food rims and secretion endpoints directly on the delivered GLB."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from glb import decode


def read_accessor(document, data, index, fmt):
    acc = document['accessors'][index]
    view = document['bufferViews'][acc['bufferView']]
    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride', struct.calcsize(fmt))
    return [struct.unpack_from(fmt, data, offset+i*stride) for i in range(acc['count'])]


def get_rims(document, data, node):
    primitive, = document['meshes'][node['mesh']]['primitives']
    xyz = read_accessor(document,data,primitive['attributes']['POSITION'],'<fff')
    ii = primitive['indices']
    fmt = {5121:'<B',5123:'<H',5125:'<I'}[document['accessors'][ii]['componentType']]
    indices = [i for i, in read_accessor(document,data,ii,fmt)]
    edges = Counter()
    for a,b,c in zip(indices[::3], indices[1::3], indices[2::3]):
        edges.update(tuple(sorted((xyz[u], xyz[v]))) for u,v in ((a,b),(b,c),(c,a)))
    neighbors = defaultdict(set)
    for (a,b),count in edges.items():
        if count == 1:
            neighbors[a].add(b)
            neighbors[b].add(a)
        elif count != 2:
            raise ValueError(f"Nonmanifold {node['name']}")
    rims = []
    while neighbors:
        p = next(iter(neighbors))
        pending = [p]
        rim = set()
        while pending:
            p = pending.pop()
            if p not in neighbors:
                continue
            pair = neighbors.pop(p)
            if len(pair) != 2:
                raise ValueError("Branched rim")
            pending.extend(pair)
            rim.add(p)
        rims.append(frozenset(rim))
    if sorted(map(len,rims)) != [32,32]:
        raise ValueError(f"Unexpected open boundary on {node['name']}")
    return rims, xyz


def center(rim):
    return tuple(sum(v[axis] for v in rim)/len(rim) for axis in range(3))


def verify(path):
    blob = path.read_bytes()
    doc, data = decode(blob)
    nodes = {n['name']: n for n in doc['nodes']}
    food = sorted(k for k in nodes if k.startswith("Food "))
    ducts = sorted(k for k in nodes if k.startswith("Accessory "))
    if (len(food), len(ducts), len(nodes)) != (10,6,22):
        raise ValueError("Missing or unexpected structures")
    geometries = {k:get_rims(doc,data,nodes[k]) for k in food+ducts}
    for a,b in zip(food,food[1:]):
        if len(set(geometries[a][0]) & set(geometries[b][0])) != 1:
            raise ValueError(f"Open connection {a} -> {b}")
    # glTF axes: X left, Y superior, Z anterior. All distances in metres.
    joins = {}
    bile = "Accessory Bile - common bile duct"
    common = "Accessory Common channel - duodenal entry"
    for a,b in [
        ("Accessory Bile - gallbladder and cystic duct", bile),
        ("Accessory Bile - hepatic duct", bile),
        (bile, common), ("Accessory Pancreatic - main duct", common),
    ]:
        dist = min(math.dist(center(p),center(q)) for p in geometries[a][0]
                   for q in geometries[b][0])
        if dist > 1e-6:
            raise ValueError(f"Duct confluence {a} / {b}: {dist}")
        joins[f'{a} / {b}'] = dist
    # Measure the nearest wall vertex to a duct endpoint (illustrative contact).
    for duct, recipient in [(common, "Food 05 Duodenum"),
                            ("Accessory Saliva - parotid to oral vestibule", "Food 01 Oral cavity")]:
        verts = geometries[recipient][1]
        d = min(math.dist(center(rim), v) for rim in geometries[duct][0] for v in verts)
        if d > .004:
            raise ValueError(f"Missing recipient {recipient}: {d} m")
        joins[f'{duct} / {recipient} (nearest surface vertex)'] = d
    return dict(sha256=hashlib.sha256(blob).hexdigest(),nodes=len(nodes),
                sharedFoodRims=9,verticesPerRim=32,distancesMetres=joins)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb",type=Path)
    print(json.dumps(verify(parser.parse_args().glb),indent=2))
