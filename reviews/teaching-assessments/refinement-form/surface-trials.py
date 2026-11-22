"""Build localized presentation trials with original GLB triangles and source frames."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode, encode

THYROID_SOURCE = {
    "path": "models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb",
    "sha256": "4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883",
    "bytes": 151580,
}


def blob_identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def load_mesh(identity):
    data = (ROOT / identity["path"]).read_bytes()
    if blob_identity(data) != {k: identity[k] for k in ("sha256", "bytes")}:
        raise ValueError(f"Wrong export bytes: {identity['path']}")
    doc, binary = decode(data)
    if len(doc["meshes"]) != 1 or len(doc["meshes"][0]["primitives"]) != 1:
        raise ValueError("Expected one unchanged, indexed triangle primitive")
    attrs = doc["meshes"][0]["primitives"][0]
    ids = (attrs["attributes"]["POSITION"], attrs["attributes"]["NORMAL"], attrs["indices"])
    arrays = []
    for number in ids:
        accessor = doc["accessors"][number]
        view = doc["bufferViews"][accessor["bufferView"]]
        dtype = {5126: "<f4", 5123: "<u2", 5125: "<u4"}[accessor["componentType"]]
        width = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
        if accessor.get("sparse") or view.get("byteStride") or view["buffer"] != 0:
            raise ValueError("Expected a contiguous accessor in GLB buffer zero")
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        arrays.append(np.frombuffer(binary, dtype, accessor["count"] * width, offset).reshape((-1, 3)))
    return doc, binary, ids, *arrays


def blend(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def unit(vectors):
    return vectors / np.maximum(1e-30, np.linalg.norm(vectors, axis=-1, keepdims=True))


def triangle_normals(verts, faces):
    triangles = verts[faces]
    return np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])


def edges_for(faces):
    return np.unique(np.concatenate([faces[:, [i, (i + 1) % 3]] for i in range(3)]), axis=0)


def residual(positions, edges, weight):
    original_lengths = np.linalg.norm(positions[edges[:, 0]] - positions[edges[:, 1]], axis=1)
    strength = 1 / np.maximum(original_lengths, 1e-7)
    size = len(positions)
    totals = np.bincount(edges[:, 0], strength, minlength=size)
    totals = np.maximum(totals, 1e-15)

    def calculate(coords):
        delta = coords[edges[:, 1]] - coords[edges[:, 0]]
        averaged = np.stack([np.bincount(edges[:, 0], strength * values, minlength=size)
                             for values in delta.T], axis=1) / totals[:, None]
        return averaged * weight[:, None]

    return calculate


def fair(positions, faces, weight, cap_m, passes, compensation=.39):
    smoothed = positions.astype(float).copy()
    edges = edges_for(faces)
    both = np.concatenate((edges, edges[:, ::-1]))
    active_edges = np.unique(both[weight[both[:, 0]] > 0], axis=0)
    delta = residual(smoothed, active_edges, weight)
    for _ in range(passes):
        smoothed += .42 * delta(smoothed)
        smoothed -= compensation * delta(smoothed)
        move = smoothed - positions
        smoothed = positions + move * np.minimum(1, cap_m / np.maximum(
            1e-30, np.linalg.norm(move, axis=-1, keepdims=True)))
    return smoothed


def export_trial(doc, binary, ids, positions, normals, faces, updated, weight,
                 path, note, protected, bridge_reference=None):
    updated = updated.astype("<f4")
    moved = np.linalg.norm(updated.astype(float) - positions, axis=1)
    if not np.any(moved > 0) or np.any(moved[protected] > 0):
        raise ValueError("Expected nonzero fairing with exact protected positions")
    old_face_normals = triangle_normals(positions.astype(float), faces)
    face_normals = triangle_normals(updated.astype(float), faces)
    normal_dot = np.sum(unit(old_face_normals) * unit(face_normals), axis=1)
    if np.any(normal_dot <= 0) or np.any(np.linalg.norm(face_normals, axis=1) < 1e-16):
        raise ValueError("Localized fairing produced a flipped or collapsed triangle")
    vertex_normals = np.zeros_like(updated)
    for corner in range(3):
        np.add.at(vertex_normals, faces[:, corner], face_normals)
    replaced = unit(vertex_normals).astype("<f4")
    # Preserve the exported shading normals wherever the edit has no influence.
    mix = blend(weight * 2.5)[:, None]
    new_normals = normals.copy()
    touched = np.flatnonzero(moved > 0)
    new_normals[touched] = unit(normals[touched] * (1 - mix[touched]) + replaced[touched] * mix[touched])
    changed_binary = bytearray(binary)
    for access_id, values in zip(ids[:2], (updated, new_normals), strict=True):
        accessor = doc["accessors"][access_id]
        offset = doc["bufferViews"][accessor["bufferView"]].get("byteOffset", 0) + accessor.get("byteOffset", 0)
        changed_binary[offset:offset + values.nbytes] = values.tobytes()
    doc["accessors"][ids[0]].update(min=updated.min(axis=0).tolist(), max=updated.max(axis=0).tolist())
    doc["nodes"][0].setdefault("extras", {})["taq011_trial"] = note
    encoded = encode(doc, changed_binary)
    path.write_bytes(encoded)
    relative_source_difference = None
    if bridge_reference is not None:
        relative_source_difference = float(np.max(np.linalg.norm(updated - bridge_reference, axis=1)) * 1000)
    return {
        "file": path.name, **blob_identity(encoded), "triangles": len(faces),
        "changedVertices": len(touched), "exactProtectedVertices": int(protected.sum()),
        "maxMovementMm": float(moved.max() * 1000),
        "rmsMovementMm": float(np.sqrt(np.mean(moved * moved)) * 1000),
        "maxDifferenceFromRetainedSourceMm": relative_source_difference,
        "minimumOrientedFaceNormalDot": float(normal_dot.min()),
        "note": note,
    }


def thyroid_trial(row, output):
    doc, binary, ids, pos, normals, faces = load_mesh(row)
    _, _, _, original, _, reference_faces = load_mesh(THYROID_SOURCE)
    if not np.array_equal(reference_faces, faces) or np.max(np.linalg.norm(pos - original, axis=1)) > .00062:
        raise ValueError("Source-to-baseline vertex correspondence changed")
    # Coordinates are source-frame glTF metres. This panel addresses the rear-facing
    # mid-to-lower band, protecting the bridge, upper lobes and outer contour.
    weight = (blend((np.abs(pos[:, 0]) - .009) / .004) *
              blend((-normals[:, 2] - .35) / .40) *
              blend((pos[:, 1] - .601) / .005) *
              blend((.642 - pos[:, 1]) / .008))
    updated = fair(pos, faces, weight, .00045, 32)
    # Bound combined presentation change against the unretouched retained surface.
    delta = updated - original
    bounds = np.minimum(1, .00075 / np.maximum(1e-30, np.linalg.norm(delta, axis=1, keepdims=True)))
    updated[weight > 0] = (original + delta * bounds)[weight > 0]
    return export_trial(doc, binary, ids, pos, normals, faces, updated, weight,
                        output / "thyroid-trial.glb",
                        "Rear-facing localized ridge treatment; representative trial on the retained s0189 label exterior. The midline bridge is pinned. No new segmentation.",
                        weight == 0, original)


def airway_trial(row, output):
    doc, binary, ids, pos, normals, faces = load_mesh(row)
    # The two source-frame trial supports target the lower junction and opposite
    # collar. Each support fades into the complete untouched branches.
    centers = np.array([[.000, .076, -.002], [-.005, .082, -.013]])
    distance = np.min(np.stack([np.linalg.norm(pos - p, axis=1) for p in centers]), axis=0)
    weight = blend((.014 - distance) / .010)
    updated = fair(pos, faces, weight, .00075, 120, compensation=.18)
    return export_trial(doc, binary, ids, pos, normals, faces, updated, weight,
                        output / "airway-trial.glb",
                        "Localized junction fairing of the authored exterior. No lumen, new branch or anatomy validation.",
                        weight == 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a fresh output directory")
    rows = json.loads((HERE / "controls.json").read_text())
    trials = {"thyroid_ct_s0189": thyroid_trial, "bronchial_tree": airway_trial}
    args.output.mkdir(parents=True)
    scores = {key: {"control": rows[key], "trial": fn(rows[key], args.output)}
              for key, fn in trials.items()}
    (args.output / "trial-build.json").write_text(json.dumps(scores, indent=2) + "\n")


if __name__ == "__main__":
    main()
