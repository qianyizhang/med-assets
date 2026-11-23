"""Fair the first fork of the exact r14 authored bronchial exterior."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.surface_fairing import blend, edges_for, export_trial, load_mesh, residual, unit
from med_assets.glb import decode, encode
CONTROL = {
    "path": "models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb",
    "sha256": "f8d78751f47cf14311138a3c7e2e35d6e28415c9f6e1d2a0e4f6ca2bf1a07fc9",
    "bytes": 7401328,
}


def ordered_edges(positions, faces, weight):
    edges = edges_for(faces)
    edges = np.unique(np.concatenate((edges, edges[:, ::-1])), axis=0)
    active = edges[weight[edges[:, 0]] > 0]
    return residual(positions, active, weight)


def fair(positions, faces, weight, cap, passes, compensation):
    original = positions.astype(np.float64)
    updated = original.copy()
    delta = ordered_edges(original, faces, weight)
    for _ in range(passes):
        updated += .42 * delta(updated)
        updated -= compensation * delta(updated)
    # Saturate gradually instead of clipping against a sphere after each pass.
    # Hard clipping leaves a ridge where neighboring vertices first hit the cap.
    movement = updated - original
    length = np.linalg.norm(movement, axis=1)
    normalized = length / cap
    taper = np.divide(np.tanh(normalized), normalized, out=np.ones_like(length), where=length > 0)
    return original + movement * taper[:, None]


def build(output, radius=.024, cap=.0018, passes=700, compensation=.15):
    document, binary, ids, positions, normals, faces = load_mesh(CONTROL)
    # Frame in glTF metres. Covers the underside and opposite collar together.
    center = np.array([-.001, .0775, -.0075])
    distance = np.linalg.norm(positions - center, axis=1)
    weight = blend((radius - distance) / (radius * .72))
    updated = fair(positions, faces, weight, cap, passes, compensation)
    trial = export_trial(
        document, binary, ids, positions, normals, faces, updated, weight, output,
        "Bounded fairing of the authored first-fork exterior. Original triangle order, topology and downstream branches retained.",
        weight == 0,
    )
    final, final_binary = decode(output.read_bytes())
    accessor = final["accessors"][ids[1]]
    view = final["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    generated = np.frombuffer(final_binary, dtype="<f4", count=normals.size,
                              offset=start).reshape(normals.shape).astype(float)
    normal_taper = blend(weight * 1.8)
    delta = ordered_edges(positions, faces, normal_taper)
    for _ in range(150):
        generated += .40 * delta(generated)
    final_normals = normals.copy()
    touched = weight > 0
    final_normals[touched] = unit(
        normals[touched] * (1 - normal_taper[touched, None])
        + generated[touched] * normal_taper[touched, None]
    )
    edited_binary = bytearray(final_binary)
    edited_binary[start:start + final_normals.nbytes] = final_normals.tobytes()
    extras = final["nodes"][0]["extras"]
    extras["firstForkFairing"] = extras.pop("taq011_trial")
    edited = encode(final, edited_binary)
    output.write_bytes(edited)
    trial.update(sha256=hashlib.sha256(edited).hexdigest(), bytes=len(edited),
                 changedNormalVertices=int(np.count_nonzero(np.any(final_normals != normals, axis=1))))
    return {
        "control": CONTROL,
        "trial": trial,
        "supportCenterGltfM": center.tolist(),
        "supportRadiusM": radius,
        "movementSaturationM": cap,
        "passes": passes,
        "compensation": compensation,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--radius", type=float, default=.024)
    parser.add_argument("--cap", type=float, default=.0018)
    parser.add_argument("--passes", type=int, default=700)
    parser.add_argument("--compensation", type=float, default=.15)
    args = parser.parse_args()
    if not (0 < args.radius <= .03 and 0 < args.cap <= .003
            and 0 < args.passes <= 1000 and 0 <= args.compensation < .42):
        parser.error("Fairing parameters exceed the bounded trial range")
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = build(args.output / "bronchial-first-fork.glb", args.radius, args.cap,
                    args.passes, args.compensation)
    (args.output / "trial-build.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
