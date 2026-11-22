"""Project only exposed Balanced bone toward the registered interface-locked reference."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np
import point_cloud_utils as pcu
from trimesh.triangles import closest_point
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode, encode

helpers = runpy.run_path(str(HERE / "dental-sections.py"))
BAL = "models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb"
FINE = "reviews/swirendo_fdi31/2026-10-27-interface-locked/media/A_1_31_T2_SEG_na__layered.glb"
SHA = "90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7"
REF = "c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014"


def normals(points, f):
    a, b, c = points[f].transpose(1, 0, 2)
    return np.cross(b - a, c - a)


def surface_distance_mm(point, vertices, faces):
    # Every closer triangle must have an AABB closer than the nearest mesh vertex.
    upper = np.min(np.linalg.norm(vertices - point, axis=1))
    tri = vertices[faces]
    offset = np.maximum(0, np.maximum(tri.min(axis=1) - point, point - tri.max(axis=1)))
    near = tri[np.linalg.norm(offset, axis=1) <= upper + 1e-9]
    closest = closest_point(near, np.broadcast_to(point, (len(near), 3)))
    return float(np.min(np.linalg.norm(closest - point, axis=1)))


def main(work):
    read = helpers["arrays"]
    points, f = read(ROOT / BAL, SHA)["bone"]
    detail = read(ROOT / FINE, REF)
    ref, rf = next(v for k, v in detail.items() if k.endswith("bone"))
    raw = helpers["verified"](
        work / "fdi31.nrrd", "f4eda9fe91b60d78ece366d6f32532862775a1725c664067da5a20aae3c142fe"
    )
    volume = np.frombuffer(gzip.decompress(raw.split(b"\n\n", 1)[1]), np.uint8).reshape(679, 500, 500)
    voxel = np.rint(points / 0.04).astype(int)[:, ::-1]
    voxel = np.clip(voxel, [0, 0, 0], np.array(volume.shape) - 1)
    # Only the tight specimen crop is needed for the root-interface guard.
    low, high = voxel.min(axis=0) - 6, voxel.max(axis=0) + 7
    low = np.maximum(low, 0)
    crop = volume[tuple(slice(a, b) for a, b in zip(low, high))]
    foreign = ndi.maximum_filter(np.isin(crop, [1, 2, 4]), size=9)
    guard = foreign[tuple((voxel - low).T)] | (voxel[:, 0] >= 675)
    # Freeze non-manifold edges and small components of the original bone budget.
    edges = np.concatenate([f[:, [i, (i + 1) % 3]] for i in range(3)])
    pairs, count = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    guard[np.unique(pairs[count != 2])] = True
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    graph = coo_matrix(
        (np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(points), len(points))
    )
    _, islands = connected_components(graph, directed=False)
    guard |= islands != np.bincount(islands).argmax()
    d, face, weights = pcu.closest_points_on_mesh(
        np.ascontiguousarray(points), np.ascontiguousarray(ref), np.ascontiguousarray(rf, dtype=np.int32)
    )
    nearest = (ref[rf[face]] * weights[:, :, None]).sum(axis=1)
    delta = nearest - points
    moving = (~guard) & (d > 0.025)
    trial = points.copy()
    trial[moving] += delta[moving] * np.minimum(1, 0.12 / d[moving])[:, None]
    old_norm = normals(points, f)
    for _ in range(16):
        new_norm = normals(trial, f)
        bad = (new_norm * old_norm).sum(axis=1) <= 0.20 * np.linalg.norm(
            new_norm, axis=1
        ) * np.linalg.norm(old_norm, axis=1)
        affected = np.unique(f[bad])
        if not len(affected) or np.array_equal(trial[affected], points[affected]):
            break
        trial[affected] = points[affected]
    doc, binary = decode((ROOT / BAL).read_bytes())
    n = next(n for n in doc["nodes"] if n["name"].endswith("/bone"))
    (prim,) = doc["meshes"][n["mesh"]]["primitives"]
    pos = doc["accessors"][prim["attributes"]["POSITION"]]
    buf = doc["bufferViews"][pos["bufferView"]]
    original = np.frombuffer(
        binary, "<f4", count=len(points) * 3, offset=buf.get("byteOffset", 0) + pos.get("byteOffset", 0)
    ).reshape(-1, 3)
    final = original.copy()
    changed = np.any(trial != points, axis=1)
    final[changed] = np.asarray(trial[changed] / 1000, dtype="<f4")
    if np.any(final[guard] != original[guard]) or not changed.any():
        raise ValueError("Protected or empty change")
    arr = bytearray(binary)
    offset = buf.get("byteOffset", 0) + pos.get("byteOffset", 0)
    arr[offset : offset + final.nbytes] = final.tobytes()
    pos.update(min=final.min(axis=0).tolist(), max=final.max(axis=0).tolist())
    n.setdefault("extras", {})["trial"] = (
        "Exposed prepared bone only; native-label root collar and acquisition edge retained."
    )
    target = work / "fdi-bone.glb"
    target.write_bytes(encode(doc, arr))
    updated = read(target, hashlib.sha256(target.read_bytes()).hexdigest())["bone"]
    metrics = {}
    for y in (176, 195, 214):
        s = volume[:, y, :]
        contours = helpers["find_contours"](np.pad((s == 3).astype(float), 1), 0.5)
        true = np.concatenate([a[:, ::-1] - 1 for a in contours])
        results = {}
        for name, (v, fs) in (("original", (points, f)), ("projected", updated), ("detail", (ref, rf))):
            approx = helpers["sample"](helpers["intersections"](v, fs, y * 0.04) / 0.04)
            kdtree = helpers["cKDTree"]
            a = kdtree(true).query(approx)[0] * 0.04
            b = kdtree(approx).query(true)[0] * 0.04
            inner = true[:, 1] < 677.5
            xi, zi = true[inner][b[inner].argmax()]
            source_point = np.array([xi, y, zi]) * 0.04
            results[name] = {
                "includingPaddedAcquisitionCutMaxSourceIndexXZ": true[np.argmax(b)].tolist(),
                "awayFromAcquisitionCutMaxSectionMm": float(b[inner].max()),
                "awayFromAcquisitionCutWorstSourceIndexXZ": [float(xi), float(zi)],
                "sameWitnessDistanceTo3DSurfaceMm": surface_distance_mm(source_point, v, fs),
                "p95Mm": [float(np.percentile(x, 95)) for x in (a, b)],
                "maxMm": [float(x.max()) for x in (a, b)],
            }
        metrics[str(y)] = results
    support = {}
    for y in range(210, 219):
        labels, _ = ndi.label(volume[:, y, :] == 3)
        local_id = labels[564, 275]
        support[str(y)] = int(np.count_nonzero(labels == local_id)) if local_id else 0
    receipt = dict(
        original=SHA,
        reference=REF,
        trialSha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        boneVertices=len(points),
        boneFaces=len(f),
        protectedVertices=int(guard.sum()),
        movedVertices=int(changed.sum()),
        maximumDisplacementMm=float(np.linalg.norm(final - original, axis=1).max() * 1000),
        sections=metrics,
        cutPlaneInterpretation="A padded label slice closes at z=678.5 beyond the last acquired voxel. The resulting worst planar discrepancy is not a missing-bone measure.",
        localSectionSupport=support,
    )
    (work / "fdi-bone-trial.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    main(p.parse_args().work)
