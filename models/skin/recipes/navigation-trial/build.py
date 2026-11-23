"""Build one protected simplification of the pinned FJ2810 envelope."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
from mathutils import Vector
import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPO / "lib"), str(REPO)]
from med_assets.triangle_geometry import edges, neighbors, oriented, preserves_faces
from tools.glb import decode, encode

CONTROL_SHA = "d86719833a17dc7b45c8eb970498f1e2feefd352b5812942f4b147a9ffcfbe4f"
CONTROL_BYTES = 4_901_132
CONTROL_TRIANGLES = 203_382
MAX_EDGE_METRES = .006
MIN_FACE_COSINE = math.cos(math.radians(25))
PASSES = 6


def read_control(path):
    data = path.read_bytes()
    if len(data) != CONTROL_BYTES or hashlib.sha256(data).hexdigest() != CONTROL_SHA:
        raise ValueError("Expected the exact hydrated bp3d-envelope-r01 GLB")
    return data


def mesh_data(data):
    document, binary = decode(data)
    primitive, = document["meshes"][0]["primitives"]
    attrs = primitive["attributes"]

    def array(index, width):
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        dtype = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[accessor["componentType"]]
        return np.frombuffer(binary, dtype, accessor["count"] * width,
                             view.get("byteOffset", 0)).reshape(-1, width)

    return (document, array(attrs["POSITION"], 3), array(attrs["NORMAL"], 3),
            array(primitive["indices"], 1).reshape(-1, 3))


def protection(positions, faces):
    """Source glTF axes are patient left, superior and anterior."""
    x, height, _ = positions.T
    shoulder = (height >= 1.21) & (height <= 1.425)
    wrist_and_hand = (height >= .60) & (height <= .865)
    foot_and_ankle = height <= .075
    links, count = edges(faces)
    seams = np.zeros(len(positions), dtype=bool)
    seams[links[count != 2].ravel()] = True
    # Also guard coincident index splits, including both sides of each split.
    _, group, count = np.unique(positions, axis=0, return_inverse=True, return_counts=True)
    seams |= count[group] > 1
    extrema = ((positions == positions.min(axis=0)) | (positions == positions.max(axis=0))).any(axis=1)
    return {
        "left shoulder": shoulder & (x >= .12),
        "right shoulder": shoulder & (x <= -.12),
        "left wrist and hand": wrist_and_hand & (x >= .205),
        "right wrist and hand": wrist_and_hand & (x <= -.205),
        "left ankle and foot": foot_and_ankle & (x >= 0),
        "right ankle and foot": foot_and_ankle & (x < 0),
        "index seams": seams,
        "envelope extrema": extrema,
    }


def simplify(positions, triangles, locked):
    mesh = bmesh.new()
    tag = mesh.verts.layers.int.new("source_index")
    vertices = []
    for index, point in enumerate(positions):
        vertex = mesh.verts.new(Vector(point))
        vertex[tag] = index
        vertices.append(vertex)
    for face in triangles:
        mesh.faces.new([vertices[index] for index in face])

    collapses = []
    for _ in range(PASSES):
        mesh.normal_update()
        options = []
        for edge in mesh.edges:
            a, b = sorted(edge.verts, key=lambda vertex: vertex[tag])
            if locked[a[tag]] or locked[b[tag]] or not edge.is_manifold:
                continue
            length = edge.calc_length()
            if length <= MAX_EDGE_METRES:
                options.append((length, a[tag], b[tag], edge, a, b))

        mapping = {}
        occupied = set()
        for _, _, _, edge, a, b in sorted(options):
            if a in occupied or b in occupied:
                continue
            opposite = {vertex for face in edge.link_faces for vertex in face.verts
                        if vertex not in (a, b)}
            a_neighbors, b_neighbors = neighbors(a), neighbors(b)
            # The link condition prevents new handles, joins and duplicate faces.
            if len(opposite) != 2 or a_neighbors & b_neighbors != opposite:
                continue
            keep, remove = a, b
            if not preserves_faces(keep, remove, MIN_FACE_COSINE):
                keep, remove = b, a
                if not preserves_faces(keep, remove, MIN_FACE_COSINE):
                    continue
            mapping[remove] = keep
            occupied.update(a_neighbors | b_neighbors | {a, b})
        collapses.append(len(mapping))
        bmesh.ops.weld_verts(mesh, targetmap=mapping)

    result = np.array([[vertex[tag] for vertex in face.verts] for face in mesh.faces])
    mesh.free()
    if len(result) != len(triangles) - 2 * sum(collapses):
        raise ValueError("An edge contraction removed an unexpected number of triangles")
    return oriented(result), collapses


def pack(document, positions, normals, faces):
    used, indices = np.unique(faces, return_inverse=True)
    index_type, component_type = ("<u2", 5123) if len(used) <= 65_536 else ("<u4", 5125)
    blobs = (positions[used].tobytes(), normals[used].tobytes(), indices.astype(index_type).tobytes())
    offset = 0
    for view, blob in zip(document["bufferViews"], blobs, strict=True):
        view.update(byteOffset=offset, byteLength=len(blob))
        offset += len(blob)
    for accessor, count in zip(document["accessors"], (len(used), len(used), faces.size), strict=True):
        accessor["count"] = count
    document["accessors"][2]["componentType"] = component_type
    document["buffers"][0]["byteLength"] = offset
    document["asset"]["generator"] = "med-assets FJ2810 navigation trial"
    return encode(document, b"".join(blobs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(f"Build destination already exists: {args.output}")
    document, positions, normals, triangles = mesh_data(read_control(args.input))
    if len(triangles) != CONTROL_TRIANGLES:
        raise ValueError("Unexpected control triangle count")
    protected = np.logical_or.reduce(list(protection(positions, triangles).values()))
    locked = protected.copy()
    locked[triangles[protected[triangles].any(axis=1)].ravel()] = True
    faces, collapses = simplify(positions, triangles, locked)
    candidate = pack(document, positions, normals, faces)
    args.output.mkdir()
    (args.output / "skin_navigation_trial.glb").write_bytes(candidate)
    (args.output / "build.json").write_text(json.dumps({
        "controlSha256": CONTROL_SHA,
        "candidateSha256": hashlib.sha256(candidate).hexdigest(),
        "candidateBytes": len(candidate),
        "triangles": len(faces),
        "collapsesByPass": collapses,
        "lockedVertices": int(locked.sum()),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
