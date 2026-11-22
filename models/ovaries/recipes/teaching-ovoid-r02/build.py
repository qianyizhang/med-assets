"""Build an explicitly interpreted ovary exterior while copying every tubal payload."""

import argparse
import hashlib
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from glb import buffer_view_bytes, decode, encode, pack_buffer_view

CONTROL = ROOT / "models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb"
DIGEST = "465a44b18df91ece95a236372a8cbe3e1a0de0207525955290e6b0fa519195d1"


def loop_once(points, faces):
    # The HRA export contains seams. Subdivide shared spatial edges once.
    vertices, inverse = np.unique(points, axis=0, return_inverse=True)
    triangles = inverse[faces]
    edge_pairs = np.concatenate([triangles[:, [i, (i + 1) % 3]] for i in range(3)])
    edges, edge_index, counts = np.unique(
        np.sort(edge_pairs, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    if not np.all(counts == 2):
        raise ValueError("Expected a closed ovary envelope")
    opp = np.concatenate([triangles[:, (i + 2) % 3] for i in range(3)])
    mids = vertices[edges].sum(axis=1) * 0.375
    np.add.at(mids, edge_index, vertices[opp] / 8)
    ordered = np.concatenate((edges, edges[:, ::-1]))
    degrees = np.bincount(ordered[:, 0])
    totals = np.zeros_like(vertices)
    np.add.at(totals, ordered[:, 0], vertices[ordered[:, 1]])
    beta = np.where(degrees == 3, 3 / 16, 3 / (8 * degrees))
    rounded = vertices * (1 - degrees * beta)[:, None] + totals * beta[:, None]
    a, b, c = triangles.T
    ab, bc, ca = edge_index.reshape(3, -1) + len(vertices)
    refined = np.concatenate(
        [np.column_stack(part) for part in [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]]
    )
    return np.vstack([rounded, mids]), refined


def build(output):
    data = CONTROL.read_bytes()
    if hashlib.sha256(data).hexdigest() != DIGEST:
        raise ValueError("Changed source export")
    doc, binary = decode(data)
    raw = [buffer_view_bytes(binary, v) for v in doc["bufferViews"]]
    for node in doc["nodes"]:
        if node["name"] not in {"VH_F_left_ovary", "VH_F_right_ovary"}:
            continue
        (prim,) = doc["meshes"][node["mesh"]]["primitives"]
        pos, norm, idx = [
            doc["accessors"][i]
            for i in (prim["attributes"]["POSITION"], prim["attributes"]["NORMAL"], prim["indices"])
        ]
        if idx["componentType"] != 5123:
            raise ValueError("Unexpected index format")
        points = np.frombuffer(raw[pos["bufferView"]], "<f4", count=pos["count"] * 3).reshape(-1, 3)
        faces = np.frombuffer(raw[idx["bufferView"]], "<u2").reshape(-1, 3)
        rounded, refined = loop_once(points.astype(float), faces)
        # Interpret the broad exterior from each source ovary's own principal span.
        # Retain some asymmetry from the source instead of replacing it with an ellipsoid.
        _, axes = np.linalg.eigh(np.cov(rounded.T))
        projected = np.einsum("ij,jk->ik", rounded, axes)
        low, high = projected.min(axis=0), projected.max(axis=0)
        center, radii = (high + low) / 2, (high - low) / 2
        local = projected - center
        elliptical = local / np.linalg.norm(local / radii, axis=1)[:, None]
        delta = np.einsum("ij,kj->ik", elliptical - local, axes)
        side = "L" if "left" in node["name"] else "R"
        fringe = next(n for n in doc["nodes"] if n["name"] == f"VH_F_fibria_of_uterine_tube_{side}")
        (part,) = doc["meshes"][fringe["mesh"]]["primitives"]
        accessor = doc["accessors"][part["attributes"]["POSITION"]]
        fringe_vertices = np.frombuffer(
            raw[accessor["bufferView"]],
            "<f4",
            count=accessor["count"] * 3,
            offset=accessor.get("byteOffset", 0),
        ).reshape(-1, 3)
        distance = cKDTree(fringe_vertices).query(rounded)[0]
        taper = np.clip((distance - 0.004) / 0.004, 0, 1)
        delta *= (taper * taper * (3 - 2 * taper))[:, None]
        rounded += delta
        normals = np.zeros_like(rounded)
        tris = rounded[refined]
        cross = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        for corner in range(3):
            np.add.at(normals, refined[:, corner], cross)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        for access, arr in (
            (pos, rounded.astype("<f4")),
            (norm, normals.astype("<f4")),
            (idx, refined.astype("<u2").reshape(-1, 1)),
        ):
            if access is norm:
                access["byteOffset"] = len(raw[pos["bufferView"]])
                raw[pos["bufferView"]] += arr.tobytes()
            else:
                raw[access["bufferView"]] = arr.tobytes()
            access["count"] = len(arr)
            for key, reduction in (("min", np.min), ("max", np.max)):
                if key in access or access is pos:
                    access[key] = reduction(arr, axis=0).tolist()
        node["extras"]["teachingEdition"] = (
            "Interpreted ovary exterior, broad ovoid interpretation fitted to the HRA axes and spans. Source-labeled tubes preserved."
        )
    merged = bytearray()
    doc["bufferViews"] = [
        pack_buffer_view(merged, view, data) for view, data in zip(doc["bufferViews"], raw, strict=True)
    ]
    doc["buffers"][0]["byteLength"] = len(merged)
    with output.open("xb") as stream:
        stream.write(encode(doc, merged))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output)
